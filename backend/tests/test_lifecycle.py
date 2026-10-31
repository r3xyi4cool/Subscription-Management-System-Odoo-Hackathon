from datetime import date
from decimal import Decimal
from backend.app.extensions import db
from backend.app.models.catalog import Product, Plan
from backend.app.models.quotation import Quotation, QuotationLine
from backend.app.models.subscription import Subscription


def test_subscription_lifecycle_and_plan_flags(client, app, admin_token, customer_user):
    with app.app_context():
        # Plan that forbids pausing and closing early
        strict_plan = Plan(
            name="Strict Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=date.today(),
            allow_pause=False,
            allow_close=False,
            allow_renew=False,
            is_active=True,
        )
        db.session.add(strict_plan)
        db.session.flush()

        product = Product(name="Test Item", sales_price=Decimal("100.00"), is_active=True)
        db.session.add(product)
        db.session.flush()

        sub = Subscription(
            subscription_number="SUB-STRICT-1",
            customer_id=customer_user.id,
            plan_id=strict_plan.id,
            status="confirmed",
            start_date=date.today(),
            current_period_start=date.today(),
            current_period_end=date.today(),
            next_billing_date=date.today(),
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

    # 1. Activate confirmed subscription
    res_act = client.post(
        f"/api/v1/subscriptions/{sub_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_act.status_code == 200
    assert res_act.get_json()["data"]["status"] == "active"

    # 2. Pause blocked because plan forbids pausing
    res_pause = client.post(
        f"/api/v1/subscriptions/{sub_id}/pause",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_pause.status_code in (409, 422)

    # 3. Close blocked because plan forbids closing
    res_close = client.post(
        f"/api/v1/subscriptions/{sub_id}/close",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_close.status_code in (409, 422)

    # Now test with flexible plan
    with app.app_context():
        flex_plan = Plan(
            name="Flex Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=date.today(),
            allow_pause=True,
            allow_close=True,
            allow_renew=True,
            is_active=True,
        )
        db.session.add(flex_plan)
        db.session.flush()

        sub_flex = Subscription(
            subscription_number="SUB-FLEX-1",
            customer_id=customer_user.id,
            plan_id=flex_plan.id,
            status="active",
            start_date=date.today(),
            current_period_start=date.today(),
            current_period_end=date.today(),
            next_billing_date=date.today(),
        )
        db.session.add(sub_flex)
        db.session.commit()
        flex_id = sub_flex.id

    # Pause passes
    res_flex_pause = client.post(
        f"/api/v1/subscriptions/{flex_id}/pause",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_flex_pause.status_code == 200
    assert res_flex_pause.get_json()["data"]["status"] == "paused"

    # Reactivate from paused
    res_flex_reactivate = client.post(
        f"/api/v1/subscriptions/{flex_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_flex_reactivate.status_code == 200
    assert res_flex_reactivate.get_json()["data"]["status"] == "active"

    # Close passes
    res_flex_close = client.post(
        f"/api/v1/subscriptions/{flex_id}/close",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_flex_close.status_code == 200
    assert res_flex_close.get_json()["data"]["status"] == "closed"

    # Cannot activate a closed subscription
    res_reopen = client.post(
        f"/api/v1/subscriptions/{flex_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_reopen.status_code in (409, 422)

