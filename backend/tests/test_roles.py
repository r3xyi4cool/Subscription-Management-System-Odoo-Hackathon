from datetime import date
from decimal import Decimal
from backend.app.extensions import db
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice
from backend.app.models.catalog import Plan


def test_role_restrictions_on_admin_routes(client, admin_token, staff_token, customer_token):
    # Admin can create staff
    staff_payload = {
        "email": "finance@example.com",
        "password": "StaffPassword@123",
        "name": "Finance Guy",
        "department": "Finance",
    }
    res_admin = client.post(
        "/api/v1/staff",
        json=staff_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 201

    # Staff cannot create staff (403)
    res_staff = client.post(
        "/api/v1/staff",
        json={"email": "staff2@example.com", "password": "StaffPassword@123", "name": "S2"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert res_staff.status_code == 403

    # Customer cannot create staff (403)
    res_cust = client.post(
        "/api/v1/staff",
        json={"email": "staff3@example.com", "password": "StaffPassword@123", "name": "S3"},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res_cust.status_code == 403

    # Staff blocked from creating product (403)
    res_staff_prod = client.post(
        "/api/v1/products",
        json={"name": "Prod by Staff", "sales_price": 50.0},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert res_staff_prod.status_code == 403

    # Customer blocked from creating product (403)
    res_cust_prod = client.post(
        "/api/v1/products",
        json={"name": "Prod by Customer", "sales_price": 50.0},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res_cust_prod.status_code == 403


def test_customer_isolation(client, app, customer_user, customer_token, customer2_user, customer2_token):
    with app.app_context():
        plan = Plan(
            name="Iso Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=date.today(),
            is_active=True,
        )
        db.session.add(plan)
        db.session.flush()

        sub1 = Subscription(
            subscription_number="SUB-CUST1",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="active",
            start_date=date.today(),
            current_period_start=date.today(),
            current_period_end=date.today(),
            next_billing_date=date.today(),
        )
        db.session.add(sub1)
        db.session.flush()

        inv1 = Invoice(
            invoice_number="INV-CUST1",
            subscription_id=sub1.id,
            customer_id=customer_user.id,
            status="confirmed",
            issue_date=date.today(),
            due_date=date.today(),
            billing_period_start=date.today(),
            billing_period_end=date.today(),
            total=Decimal("100.00"),
        )
        db.session.add(inv1)
        db.session.commit()
        inv1_id = inv1.id
        sub1_id = sub1.id

    # Customer 1 can read own invoice and subscription
    res_own_inv = client.get(
        f"/api/v1/invoices/{inv1_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res_own_inv.status_code == 200

    res_own_sub = client.get(
        f"/api/v1/subscriptions/{sub1_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res_own_sub.status_code == 200

    # Customer 2 gets 403 or 404 for customer 1's invoice and subscription
    res_other_inv = client.get(
        f"/api/v1/invoices/{inv1_id}",
        headers={"Authorization": f"Bearer {customer2_token}"},
    )
    assert res_other_inv.status_code in (403, 404)

    res_other_sub = client.get(
        f"/api/v1/subscriptions/{sub1_id}",
        headers={"Authorization": f"Bearer {customer2_token}"},
    )
    assert res_other_sub.status_code in (403, 404)

