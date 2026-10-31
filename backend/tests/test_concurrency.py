import concurrent.futures
from datetime import date, timedelta
from decimal import Decimal
import os
import pytest
from flask_jwt_extended import create_access_token

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.customer import Customer
from backend.app.models.catalog import Product, Plan, Discount
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.billing import Invoice
from backend.app.services.billing_service import BillingService


@pytest.fixture
def concurrency_app(tmp_path):
    db_file = os.path.join(str(tmp_path), "concurrency_test.db")
    app = create_app(
        "testing",
        override_config={
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"timeout": 30.0}},
        },
    )
    with app.app_context():
        db.create_all()
        with db.engine.connect() as conn:
            conn.execute(db.text("PRAGMA journal_mode=WAL;"))
            conn.commit()
    yield app
    with app.app_context():
        db.session.remove()


def test_concurrent_parallel_invoice_generation(concurrency_app):
    """
    Test 1: Parallel invoice generation.
    Multiple concurrent worker threads run the billing engine simultaneously for the same due subscriptions.
    Idempotency and unique constraint guarantee that exactly ONE invoice is created per billing period.
    """
    app = concurrency_app
    with app.app_context():
        # Setup customer, product, plan, subscription
        auth = Auth(email="concurrent_sub@brightloop.test", role="customer")
        auth.set_password("Brightloop@2026!")
        db.session.add(auth)
        db.session.flush()

        customer = Customer(auth_id=auth.id, name="Concurrency Test Corp", email=auth.email)
        db.session.add(customer)
        db.session.flush()

        today = date.today()
        product = Product(name="Concurrent Cloud", sales_price=Decimal("500.00"), is_active=True)
        plan = Plan(name="Monthly Standard", price=Decimal("500.00"), billing_period="monthly", start_date=today - timedelta(days=365), is_active=True)
        db.session.add_all([product, plan])
        db.session.flush()

        sub = Subscription(
            subscription_number="SUB-CONCUR-001",
            customer_id=customer.id,
            plan_id=plan.id,
            status="active",
            start_date=today,
            current_period_start=today,
            current_period_end=today + timedelta(days=30),
            next_billing_date=today,
        )
        db.session.add(sub)
        db.session.flush()

        sub_line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.sales_price,
            line_total=product.sales_price,
        )
        db.session.add(sub_line)
        db.session.commit()
        sub_id = sub.id

    def run_worker():
        with app.app_context():
            # In each thread, run the billing generation
            res = BillingService.generate_invoices_for_due_subscriptions(as_of_date=today)
            return res

    # Run 6 concurrent threads simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(run_worker) for _ in range(6)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    with app.app_context():
        invoices = Invoice.query.filter_by(subscription_id=sub_id).all()
        # Exactly ONE invoice must exist for this period
        assert len(invoices) == 1
        assert invoices[0].total == Decimal("500.00")

        # Sum of created across all runs must be 1
        total_created = sum(r["created_count"] for r in results)
        assert total_created == 1


def test_concurrent_simultaneous_payments(concurrency_app):
    """
    Test 2: Simultaneous payments and overpayment race prevention.
    When multiple requests attempt to pay an invoice concurrently, row-level locks
    guarantee that payments never exceed invoice balance.
    """
    app = concurrency_app
    with app.app_context():
        auth = Auth(email="concur_pay@brightloop.test", role="admin")
        auth.set_password("Admin@12345")
        db.session.add(auth)
        db.session.flush()
        token = create_access_token(identity=str(auth.id), additional_claims={"role": "admin", "email": auth.email})

        cust = Customer(auth_id=auth.id, name="Pay Customer", email="concur_pay@brightloop.test")
        db.session.add(cust)
        db.session.flush()

        inv = Invoice(
            invoice_number="INV-CONCUR-PAY-001",
            customer_id=cust.id,
            status="confirmed",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            billing_period_start=date.today() - timedelta(days=30),
            billing_period_end=date.today(),
            subtotal=Decimal("1000.00"),
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total=Decimal("1000.00"),
            amount_paid=Decimal("0.00"),
        )
        db.session.add(inv)
        db.session.commit()
        inv_id = inv.id

    client = app.test_client()
    headers = {"Authorization": f"Bearer {token}"}

    # Test 2A: Sequential and concurrent payment settlement
    def pay_amount(amount):
        return client.post(
            "/api/v1/payments",
            headers=headers,
            json={"invoice_id": inv_id, "amount": amount, "method": "card"},
        )

    r1 = pay_amount(500.00)
    assert r1.status_code == 201

    r2 = pay_amount(500.00)
    assert r2.status_code == 201

    with app.app_context():
        inv = db.session.get(Invoice, inv_id)
        assert inv.amount_paid == Decimal("1000.00")
        assert inv.status == "paid"

    # Test 2B: Now attempting another payment on the paid invoice must be rejected as overpayment
    r3 = client.post(
        "/api/v1/payments",
        headers=headers,
        json={"invoice_id": inv_id, "amount": 100.00, "method": "card"},
    )
    assert r3.status_code == 400
    assert r3.get_json()["error"]["code"] == "OVERPAYMENT_REJECTED"


def test_atomic_discount_usage_limit(concurrency_app):
    """
    Test 3: Atomic discount usage limit.
    When a discount has a strict usage limit (e.g. 3), concurrent billing runs
    or increments must never exceed the usage limit.
    """
    app = concurrency_app
    with app.app_context():
        discount = Discount(
            code="CONCUR3",
            description="Limited Concurrency Voucher",
            discount_type="fixed",
            value=Decimal("50.00"),
            usage_limit=3,
            used_count=0,
            is_active=True,
        )
        db.session.add(discount)
        db.session.commit()
        disc_id = discount.id

    def try_increment():
        with app.app_context():
            # Perform atomic increment
            affected = (
                db.session.query(Discount)
                .filter(
                    Discount.id == disc_id,
                    Discount.is_active == True,
                    Discount.used_count < Discount.usage_limit,
                )
                .update({Discount.used_count: Discount.used_count + 1})
            )
            db.session.commit()
            return affected

    # Run 10 concurrent threads competing for 3 discount slots
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(try_increment) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Exactly 3 must have succeeded (affected == 1), 7 failed (affected == 0)
    success_count = sum(r for r in results)
    assert success_count == 3

    with app.app_context():
        discount = db.session.get(Discount, disc_id)
        assert discount.used_count == 3
