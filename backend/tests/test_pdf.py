from datetime import date
from decimal import Decimal
from backend.app.extensions import db
from backend.app.models.catalog import Plan, Product
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice, InvoiceLine


def test_invoice_pdf_endpoint_returns_valid_pdf(client, app, admin_token, customer_user):
    with app.app_context():
        plan = Plan(
            name="PDF Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=date.today(),
            is_active=True,
        )
        product = Product(name="PDF Item", sales_price=Decimal("120.00"), is_active=True)
        db.session.add_all([plan, product])
        db.session.flush()

        sub = Subscription(
            subscription_number="SUB-PDF",
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

        inv = Invoice(
            invoice_number="INV-PDF-101",
            subscription_id=sub.id,
            customer_id=customer_user.id,
            status="confirmed",
            issue_date=date.today(),
            due_date=date.today(),
            billing_period_start=date.today(),
            billing_period_end=date.today(),
            subtotal=Decimal("120.00"),
            tax_amount=Decimal("12.00"),
            discount_amount=Decimal("0.00"),
            total=Decimal("132.00"),
            amount_paid=Decimal("0.00"),
        )
        db.session.add(inv)
        db.session.flush()

        inv_line = InvoiceLine(
            invoice_id=inv.id,
            product_id=product.id,
            description="PDF Item Service",
            quantity=1,
            unit_price=Decimal("120.00"),
            variant_price=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("12.00"),
            line_total=Decimal("132.00"),
        )
        db.session.add(inv_line)
        db.session.commit()
        inv_id = inv.id

    res = client.get(
        f"/api/v1/invoices/{inv_id}/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.content_type == "application/pdf"
    assert res.data.startswith(b"%PDF")

