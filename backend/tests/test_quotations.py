from datetime import date, timedelta
from decimal import Decimal
from backend.app.extensions import db
from backend.app.models.catalog import Product, Plan, Tax, Discount


def test_quotation_creation_and_confirm(client, app, admin_token, customer_user):
    with app.app_context():
        tax = Tax(name="Standard Tax", rate=Decimal("10.00"), is_active=True)
        discount = Discount(
            code="DEAL10",
            discount_type="percentage",
            value=Decimal("10.00"),
            min_quantity=1,
            is_active=True,
        )
        plan = Plan(
            name="Quarterly Enterprise",
            billing_period="monthly",
            min_quantity=1,
            start_date=date.today(),
            is_active=True,
        )
        prod = Product(name="Enterprise Engine", sales_price=Decimal("100.00"), is_active=True)
        db.session.add_all([tax, discount, plan, prod])
        db.session.commit()

        tax_id = tax.id
        disc_id = discount.id
        plan_id = plan.id
        prod_id = prod.id

    # Create quotation
    q_payload = {
        "customer_id": customer_user.id,
        "plan_id": plan_id,
        "validity_days": 30,
        "lines": [
            {
                "product_id": prod_id,
                "quantity": 2,
                "tax_id": tax_id,
                "discount_id": disc_id,
            }
        ],
    }
    q_res = client.post(
        "/api/v1/quotations",
        json=q_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert q_res.status_code == 201
    q_data = q_res.get_json()["data"]
    q_id = q_data["id"]

    # Confirm quotation -> creates subscription
    c_res = client.post(
        f"/api/v1/quotations/{q_id}/confirm",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert c_res.status_code == 201
    c_data = c_res.get_json()["data"]
    assert "subscription_id" in c_data or "id" in c_data
    assert c_data["status"] == "confirmed"

