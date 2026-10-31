from datetime import date, timedelta
from decimal import Decimal

from backend.app.extensions import db
from backend.app.models.catalog import Plan
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice, Payment


def test_dashboard_metrics_and_filters(client, app, admin_token, customer_user, customer2_user):
    with app.app_context():
        plan1 = Plan(name="Plan A", billing_period="monthly", min_quantity=1, start_date=date.today(), is_active=True)
        plan2 = Plan(name="Plan B", billing_period="yearly", min_quantity=1, start_date=date.today(), is_active=True)
        db.session.add_all([plan1, plan2])
        db.session.flush()

        # Customer 1: 1 active sub, 1 paid invoice ($300)
        sub1 = Subscription(
            subscription_number="SUB-DASH-1",
            customer_id=customer_user.id,
            plan_id=plan1.id,
            status="active",
            start_date=date.today(),
            current_period_start=date.today(),
            current_period_end=date.today(),
            next_billing_date=date.today(),
        )
        # Customer 2: 1 active sub, 1 confirmed overdue invoice ($500, paid $100)
        sub2 = Subscription(
            subscription_number="SUB-DASH-2",
            customer_id=customer2_user.id,
            plan_id=plan2.id,
            status="active",
            start_date=date.today(),
            current_period_start=date.today(),
            current_period_end=date.today(),
            next_billing_date=date.today(),
        )
        # Customer 1: 1 closed sub
        sub3 = Subscription(
            subscription_number="SUB-DASH-3",
            customer_id=customer_user.id,
            plan_id=plan1.id,
            status="closed",
            start_date=date.today(),
            current_period_start=date.today(),
            current_period_end=date.today(),
            next_billing_date=date.today(),
        )
        db.session.add_all([sub1, sub2, sub3])
        db.session.flush()

        # Invoices
        inv1 = Invoice(
            invoice_number="INV-DASH-1",
            subscription_id=sub1.id,
            customer_id=customer_user.id,
            status="paid",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            billing_period_start=date.today(),
            billing_period_end=date.today(),
            subtotal=Decimal("300.00"),
            total=Decimal("300.00"),
            amount_paid=Decimal("300.00"),
        )
        past_due = date.today() - timedelta(days=5)
        inv2 = Invoice(
            invoice_number="INV-DASH-2",
            subscription_id=sub2.id,
            customer_id=customer2_user.id,
            status="confirmed",
            issue_date=past_due - timedelta(days=14),
            due_date=past_due,
            billing_period_start=past_due - timedelta(days=14),
            billing_period_end=past_due,
            subtotal=Decimal("500.00"),
            total=Decimal("500.00"),
            amount_paid=Decimal("100.00"),
        )
        db.session.add_all([inv1, inv2])
        db.session.flush()

        # Payments
        pay1 = Payment(
            payment_number="PAY-DASH-1",
            invoice_id=inv1.id,
            customer_id=customer_user.id,
            amount=Decimal("300.00"),
            method="credit_card",
            date=date.today(),
            status="completed",
        )
        pay2 = Payment(
            payment_number="PAY-DASH-2",
            invoice_id=inv2.id,
            customer_id=customer2_user.id,
            amount=Decimal("100.00"),
            method="bank_transfer",
            date=past_due,
            status="completed",
        )
        db.session.add_all([pay1, pay2])
        db.session.commit()

        c1_id = customer_user.id
        p1_id = plan1.id

    # Test global summary
    res = client.get("/api/v1/dashboard/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert data["active_subscriptions"] == 2
    assert data["total_subscriptions"] == 3
    assert data["revenue"] == 800.00
    assert data["payments"] == 400.00
    assert data["amount_owed"] == 400.00  # 500 - 100
    assert data["overdue_invoices"] == 1
    assert data["overdue_amount"] == 400.00

    # Test customer 1 filter
    res_c1 = client.get(
        f"/api/v1/dashboard/summary?customer_id={c1_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_c1.status_code == 200
    data_c1 = res_c1.get_json()["data"]
    assert data_c1["active_subscriptions"] == 1
    assert data_c1["total_subscriptions"] == 2
    assert data_c1["revenue"] == 300.00
    assert data_c1["payments"] == 300.00
    assert data_c1["amount_owed"] == 0.00

