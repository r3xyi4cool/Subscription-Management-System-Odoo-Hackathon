from datetime import date, timedelta
from decimal import Decimal

from backend.app.extensions import db
from backend.app.models.catalog import Product, Plan
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.billing import Invoice
from backend.app.services.billing_service import BillingService, add_billing_period


def test_billing_job_idempotence_and_no_duplicates(client, app, admin_token, customer_user):
    with app.app_context():
        plan = Plan(
            name="Monthly Pro",
            billing_period="monthly",
            min_quantity=1,
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        db.session.add(plan)
        db.session.flush()

        product = Product(name="Pro Service", sales_price=Decimal("150.00"), is_active=True)
        db.session.add(product)
        db.session.flush()

        today = date(2026, 1, 1)
        sub = Subscription(
            subscription_number="SUB-BILL-1",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="active",
            start_date=today,
            current_period_start=today,
            current_period_end=add_billing_period(today, "monthly"),
            next_billing_date=today,
        )
        db.session.add(sub)
        db.session.flush()

        line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.sales_price,
            line_total=product.sales_price,
        )
        db.session.add(line)
        db.session.commit()
        sub_id = sub.id

    # Run 1 via API
    res1 = client.post(
        "/api/v1/billing/run",
        json={"as_of_date": "2026-01-01"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res1.status_code == 200
    data1 = res1.get_json()["data"]
    assert data1["created_count"] == 1

    # Run 2 immediately on the same day -> IDEMPOTENT (no duplicate invoices!)
    res2 = client.post(
        "/api/v1/billing/run",
        json={"as_of_date": "2026-01-01"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code == 200
    data2 = res2.get_json()["data"]
    assert data2["created_count"] == 0

    with app.app_context():
        invoices = Invoice.query.filter_by(subscription_id=sub_id).all()
        assert len(invoices) == 1


def test_billing_time_travel_and_paused_closed_skipped(client, app, admin_token, customer_user):
    with app.app_context():
        plan = Plan(
            name="Monthly Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        db.session.add(plan)
        db.session.flush()

        product = Product(name="Item", sales_price=Decimal("100.00"), is_active=True)
        db.session.add(product)
        db.session.flush()

        start = date(2026, 1, 1)

        # Active sub that will miss periods
        sub_active = Subscription(
            subscription_number="SUB-ACTIVE-TIME",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="active",
            start_date=start,
            current_period_start=start,
            current_period_end=add_billing_period(start, "monthly"),
            next_billing_date=start,
        )
        db.session.add(sub_active)
        db.session.flush()
        db.session.add(
            SubscriptionLine(
                subscription_id=sub_active.id,
                product_id=product.id,
                quantity=1,
                unit_price=product.sales_price,
                line_total=product.sales_price,
            )
        )

        # Paused sub
        sub_paused = Subscription(
            subscription_number="SUB-PAUSED",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="paused",
            start_date=start,
            current_period_start=start,
            current_period_end=add_billing_period(start, "monthly"),
            next_billing_date=start,
        )
        db.session.add(sub_paused)

        # Closed sub
        sub_closed = Subscription(
            subscription_number="SUB-CLOSED",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="closed",
            start_date=start,
            current_period_start=start,
            current_period_end=add_billing_period(start, "monthly"),
            next_billing_date=start,
        )
        db.session.add(sub_closed)
        db.session.commit()

        active_id = sub_active.id
        paused_id = sub_paused.id
        closed_id = sub_closed.id

    # Time-travel 3 months ahead: 2026-03-05
    # Should catch up January, February, March (3 periods)
    res_time = client.post(
        "/api/v1/billing/run",
        json={"as_of_date": "2026-03-05"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_time.status_code == 200
    data = res_time.get_json()["data"]
    assert data["created_count"] == 3

    with app.app_context():
        # Active subscription has 3 invoices
        active_invs = Invoice.query.filter_by(subscription_id=active_id).all()
        assert len(active_invs) == 3

        # Paused and closed had ZERO invoices generated
        paused_invs = Invoice.query.filter_by(subscription_id=paused_id).all()
        assert len(paused_invs) == 0

        closed_invs = Invoice.query.filter_by(subscription_id=closed_id).all()
        assert len(closed_invs) == 0

