from datetime import date, timedelta
from decimal import Decimal
import os
import pytest
from filelock import FileLock, Timeout

from backend.app.extensions import db
from backend.app.models.customer import Customer
from backend.app.models.catalog import Plan, Product
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.billing import Invoice
from backend.app.models.notification import Notification
from backend.app.worker import run_worker_tick, LOCK_FILE


def test_worker_single_instance_lock():
    lock1 = FileLock(LOCK_FILE, timeout=0.1)
    lock1.acquire()
    try:
        lock2 = FileLock(LOCK_FILE, timeout=0.1)
        with pytest.raises(Timeout):
            lock2.acquire()
    finally:
        lock1.release()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)


def test_worker_tick_generates_due_invoices(app, customer_user):
    with app.app_context():
        today = date.today()
        plan = Plan(
            name="Worker Due Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=today,
            is_active=True,
        )
        product = Product(name="Worker Product", sales_price=Decimal("300.00"), is_active=True)
        db.session.add_all([plan, product])
        db.session.flush()

        sub = Subscription(
            subscription_number="SUB-WORKER-01",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="active",
            start_date=today,
            current_period_start=today,
            current_period_end=today + timedelta(days=30),
            next_billing_date=today,
        )
        db.session.add(sub)
        db.session.flush()

        line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("300.00"),
            variant_price=Decimal("0.00"),
            line_total=Decimal("300.00"),
        )
        db.session.add(line)
        db.session.commit()

        # Run tick
        res = run_worker_tick(as_of_date=today)
        assert res["invoices_created"] >= 1

        # Check invoice was created
        inv = Invoice.query.filter_by(subscription_id=sub.id).first()
        assert inv is not None
        assert float(inv.total) == 300.00


def test_worker_tick_sends_reminders_and_deduplicates(app, customer_user):
    with app.app_context():
        today = date.today()
        inv = Invoice(
            invoice_number="INV-WORKER-REMIND",
            customer_id=customer_user.id,
            status="confirmed",
            issue_date=today - timedelta(days=5),
            due_date=today + timedelta(days=2),  # due in 2 days (<= 3)
            billing_period_start=today - timedelta(days=5),
            billing_period_end=today + timedelta(days=25),
            subtotal=Decimal("250.00"),
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total=Decimal("250.00"),
            amount_paid=Decimal("0.00"),
        )
        db.session.add(inv)
        db.session.commit()

        # First tick sends reminder
        res1 = run_worker_tick(as_of_date=today)
        assert res1["reminders_sent"] >= 1

        notif = Notification.query.filter_by(
            customer_id=customer_user.id,
            type="reminder",
            dedupe_key=f"reminder_{inv.id}_{today.isoformat()}",
        ).first()
        assert notif is not None
        assert "due in 2 days" in notif.message

        # Second tick on same date skips already-sent reminder
        res2 = run_worker_tick(as_of_date=today)
        # Should not re-send
        assert res2["reminders_sent"] == 0


def test_worker_auto_close_expired_subscription(app, customer_user):
    with app.app_context():
        today = date.today()
        plan = Plan(
            name="Auto Close Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=today - timedelta(days=60),
            auto_close=True,
            is_active=True,
        )
        db.session.add(plan)
        db.session.flush()

        sub = Subscription(
            subscription_number="SUB-AUTOCLOSE",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="active",
            start_date=today - timedelta(days=60),
            current_period_start=today - timedelta(days=60),
            current_period_end=today - timedelta(days=5),  # period ended 5 days ago
            next_billing_date=today + timedelta(days=30),
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

        # Run tick
        res = run_worker_tick(as_of_date=today)
        assert res["subs_closed"] >= 1

        refreshed_sub = db.session.get(Subscription, sub_id)
        assert refreshed_sub.status == "closed"

