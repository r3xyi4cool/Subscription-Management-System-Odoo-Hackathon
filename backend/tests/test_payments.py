from datetime import date, timedelta
from decimal import Decimal

from backend.app.extensions import db
from backend.app.models.billing import Invoice
from backend.app.models.catalog import Plan
from backend.app.models.subscription import Subscription


def test_payments_partial_full_overpayment_and_refunds(client, app, admin_token, customer_user):
    with app.app_context():
        plan = Plan(
            name="Pay Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=date.today(),
            is_active=True,
        )
        db.session.add(plan)
        db.session.flush()

        sub = Subscription(
            subscription_number="SUB-PAY",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="active",
            start_date=date.today(),
            current_period_start=date.today(),
            current_period_end=date.today(),
            next_billing_date=date.today(),
        )
        db.session.add(sub)
        db.session.flush()

        past_due = date.today() - timedelta(days=5)
        inv = Invoice(
            invoice_number="INV-PAY-1",
            subscription_id=sub.id,
            customer_id=customer_user.id,
            status="confirmed",
            issue_date=past_due - timedelta(days=14),
            due_date=past_due,
            billing_period_start=past_due - timedelta(days=14),
            billing_period_end=past_due,
            subtotal=Decimal("200.00"),
            total=Decimal("200.00"),
            amount_paid=Decimal("0.00"),
        )
        db.session.add(inv)
        db.session.commit()
        inv_id = inv.id

    # 1. Appears in overdue list
    overdue_res = client.get(
        "/api/v1/invoices/overdue",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert overdue_res.status_code == 200
    assert any(i["id"] == inv_id for i in overdue_res.get_json().get("items", []))

    # 2. Partial payment ($80)
    pay1_res = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": 80.0,
            "method": "credit_card",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pay1_res.status_code == 201

    inv_chk1 = client.get(
        f"/api/v1/invoices/{inv_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert inv_chk1.get_json()["data"]["amount_paid"] == 80.0
    assert inv_chk1.get_json()["data"]["status"] == "confirmed"

    # 3. Overpayment rejected ($150 > remaining $120)
    overpay_res = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": 150.0,
            "method": "credit_card",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert overpay_res.status_code in (400, 422)

    # 4. Full payment ($120) -> status becomes Paid
    pay2_res = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": 120.0,
            "method": "credit_card",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pay2_res.status_code == 201

    inv_chk2 = client.get(
        f"/api/v1/invoices/{inv_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert inv_chk2.get_json()["data"]["amount_paid"] == 200.0
    assert inv_chk2.get_json()["data"]["status"] == "paid"

    # No longer in overdue list
    overdue_res2 = client.get(
        "/api/v1/invoices/overdue",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert not any(i["id"] == inv_id for i in overdue_res2.get_json().get("items", []))

    # 5. Refund
    # Valid partial refund ($50)
    ref_res1 = client.post(
        f"/api/v1/invoices/{inv_id}/refund",
        json={"amount": 50.0, "reason": "Customer discount adjustment"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ref_res1.status_code == 201

    # Excessive refund ($200 > remaining refundable $150)
    ref_res2 = client.post(
        f"/api/v1/invoices/{inv_id}/refund",
        json={"amount": 200.0, "reason": "Too much"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ref_res2.status_code in (400, 422)

