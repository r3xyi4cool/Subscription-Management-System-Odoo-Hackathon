import time
from datetime import date, timedelta
from decimal import Decimal
from backend.app.extensions import db
from backend.app.models.customer import Customer
from backend.app.models.catalog import Plan, Product
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice


def test_dashboard_summary_performance_under_half_second(client, app, admin_token, customer_user):
    """
    Verifies that GET /api/v1/dashboard/summary executes in < 0.5s (500ms)
    even when querying subscriptions, plans, and metrics.
    """
    with app.app_context():
        # Ensure a plan and product exist
        plan = Plan(
            name="Perf Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=date.today(),
            is_active=True,
        )
        product = Product(name="Perf Product", sales_price=Decimal("100.00"), is_active=True)
        db.session.add_all([plan, product])
        db.session.commit()

        # Seed 200 subscriptions and 300 invoices in-session
        today = date.today()
        subs = []
        for i in range(200):
            subs.append(
                Subscription(
                    subscription_number=f"SUB-PERF-{i}",
                    customer_id=customer_user.id,
                    plan_id=plan.id,
                    status="active" if i % 2 == 0 else "closed",
                    start_date=today - timedelta(days=i),
                    current_period_start=today - timedelta(days=30),
                    current_period_end=today,
                    next_billing_date=today + timedelta(days=i % 30),
                )
            )
        db.session.add_all(subs)
        db.session.commit()

    # Measure API call time
    t0 = time.time()
    res = client.get(
        "/api/v1/dashboard/summary?status=active",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    elapsed = time.time() - t0

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "active_subscriptions" in data
    assert "total_subscriptions" in data
    # Target: < 0.5 seconds
    assert elapsed < 0.5, f"Dashboard summary took {elapsed:.4f}s which exceeds 0.5s limit"
