import os
from datetime import date, timedelta
from decimal import Decimal

from backend.app.config import Config
from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.customer import Customer
from backend.app.models.staff import Staff
from backend.app.models.catalog import Product, Variant, Plan, Discount, Tax
from backend.app.models.quotation import QuotationTemplate, Quotation, QuotationLine
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.billing import Invoice, InvoiceLine, Payment
from backend.app.services.billing_service import add_billing_period


def run_seed():
    db.create_all()

    admin_email = os.getenv("ADMIN_EMAIL", Config.ADMIN_EMAIL)
    admin_password = os.getenv("ADMIN_PASSWORD", Config.ADMIN_PASSWORD)

    # 1. Admin
    admin_auth = Auth.query.filter_by(email=admin_email).first()
    if not admin_auth:
        admin_auth = Auth(email=admin_email, role="admin", is_active=True)
        admin_auth.set_password(admin_password)
        db.session.add(admin_auth)
        db.session.flush()

    # 2. Staff (2 staff members)
    staff_data = [
        {"email": "staff1@example.com", "name": "Alice Smith", "department": "Sales"},
        {"email": "staff2@example.com", "name": "Bob Jones", "department": "Support"},
    ]
    for s_info in staff_data:
        s_auth = Auth.query.filter_by(email=s_info["email"]).first()
        if not s_auth:
            s_auth = Auth(email=s_info["email"], role="staff", is_active=True)
            s_auth.set_password("Staff@12345")
            db.session.add(s_auth)
            db.session.flush()

            staff = Staff(
                auth_id=s_auth.id,
                name=s_info["name"],
                email=s_info["email"],
                department=s_info["department"],
                role="staff",
                is_active=True,
            )
            db.session.add(staff)

    # 3. Customers (3 customers)
    customers_data = [
        {
            "email": "customer1@example.com",
            "name": "Acme Corp",
            "company": "Acme Inc",
            "phone": "555-0101",
            "address": "100 Acme Way, Metropolis",
        },
        {
            "email": "customer2@example.com",
            "name": "Beta LLC",
            "company": "Beta Logistics",
            "phone": "555-0102",
            "address": "200 Beta Blvd, Gotham",
        },
        {
            "email": "customer3@example.com",
            "name": "Gamma Tech",
            "company": "Gamma Software",
            "phone": "555-0103",
            "address": "300 Gamma St, Star City",
        },
    ]
    seeded_customers = []
    for c_info in customers_data:
        c_auth = Auth.query.filter_by(email=c_info["email"]).first()
        if not c_auth:
            c_auth = Auth(email=c_info["email"], role="customer", is_active=True)
            c_auth.set_password("Cust@12345")
            db.session.add(c_auth)
            db.session.flush()

            customer = Customer(
                auth_id=c_auth.id,
                name=c_info["name"],
                email=c_info["email"],
                company=c_info["company"],
                phone=c_info["phone"],
                billing_address=c_info["address"],
            )
            db.session.add(customer)
            db.session.flush()
            seeded_customers.append(customer)
        else:
            seeded_customers.append(c_auth.customer_profile)

    # 4. Taxes (2 taxes)
    tax_10 = Tax.query.filter_by(name="Standard VAT (10%)").first()
    if not tax_10:
        tax_10 = Tax(name="Standard VAT (10%)", rate=Decimal("10.00"), is_active=True)
        db.session.add(tax_10)

    tax_5 = Tax.query.filter_by(name="Reduced Tax (5%)").first()
    if not tax_5:
        tax_5 = Tax(name="Reduced Tax (5%)", rate=Decimal("5.00"), is_active=True)
        db.session.add(tax_5)

    # 5. Discounts (one expired, one with usage limit, plus standard)
    disc_expired = Discount.query.filter_by(code="EXPIRED10").first()
    if not disc_expired:
        disc_expired = Discount(
            code="EXPIRED10",
            description="Expired 10% discount",
            discount_type="percentage",
            value=Decimal("10.00"),
            start_date=date(2019, 1, 1),
            end_date=date(2020, 1, 1),
            is_active=True,
        )
        db.session.add(disc_expired)

    disc_limit = Discount.query.filter_by(code="LIMIT5").first()
    if not disc_limit:
        disc_limit = Discount(
            code="LIMIT5",
            description="Discount that reached usage limit",
            discount_type="percentage",
            value=Decimal("15.00"),
            usage_limit=5,
            used_count=5,  # Exceeded limit
            is_active=True,
        )
        db.session.add(disc_limit)

    disc_active = Discount.query.filter_by(code="WELCOME20").first()
    if not disc_active:
        disc_active = Discount(
            code="WELCOME20",
            description="Active welcome 20% discount",
            discount_type="percentage",
            value=Decimal("20.00"),
            min_quantity=1,
            is_active=True,
        )
        db.session.add(disc_active)

    # 6. Products & Variants (with Odoo +560)
    p_erp = Product.query.filter_by(name="Cloud ERP Enterprise").first()
    if not p_erp:
        p_erp = Product(
            name="Cloud ERP Enterprise",
            description="Full-scale ERP system for enterprises",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("300.00"),
            is_active=True,
        )
        db.session.add(p_erp)
        db.session.flush()

        v_odoo = Variant(
            product_id=p_erp.id,
            name="Odoo Enterprise Module",
            extra_price=Decimal("560.00"),
            is_active=True,
        )
        db.session.add(v_odoo)

    p_crm = Product.query.filter_by(name="CRM Professional").first()
    if not p_crm:
        p_crm = Product(
            name="CRM Professional",
            description="Modern CRM suite",
            sales_price=Decimal("200.00"),
            cost_price=Decimal("50.00"),
            is_active=True,
        )
        db.session.add(p_crm)

    # 7. Plans of each billing period (daily, weekly, monthly, yearly)
    plans = [
        {"name": "Daily Trial Plan", "period": "daily", "min_qty": 1},
        {"name": "Weekly Sprint Plan", "period": "weekly", "min_qty": 1},
        {"name": "Monthly Business Plan", "period": "monthly", "min_qty": 1},
        {"name": "Yearly Enterprise Plan", "period": "yearly", "min_qty": 1},
    ]
    seeded_plans = {}
    for p_info in plans:
        plan = Plan.query.filter_by(name=p_info["name"]).first()
        if not plan:
            plan = Plan(
                name=p_info["name"],
                description=f"Standard {p_info['period']} subscription plan",
                billing_period=p_info["period"],
                min_quantity=p_info["min_qty"],
                start_date=date(2026, 1, 1),
                allow_pause=True,
                allow_close=True,
                allow_renew=True,
                is_active=True,
            )
            db.session.add(plan)
            db.session.flush()
        seeded_plans[p_info["period"]] = plan

    # 8. Quotation Template
    template = QuotationTemplate.query.filter_by(name="Standard SaaS Template").first()
    if not template:
        template = QuotationTemplate(
            name="Standard SaaS Template",
            description="Default quotation template for new enterprise accounts",
            validity_days=30,
            is_active=True,
        )
        db.session.add(template)

    # 9. Subscriptions, Invoices, Payments
    c1 = seeded_customers[0]
    sub1 = Subscription.query.filter_by(customer_id=c1.id).first()
    today = date.today()
    if not sub1:
        monthly_plan = seeded_plans["monthly"]
        sub1 = Subscription(
            subscription_number="SUB-SEED-001",
            customer_id=c1.id,
            plan_id=monthly_plan.id,
            status="active",
            start_date=today - timedelta(days=60),
            current_period_start=today,
            current_period_end=add_billing_period(today, "monthly"),
            next_billing_date=add_billing_period(today, "monthly"),
        )
        db.session.add(sub1)
        db.session.flush()

        sub_line = SubscriptionLine(
            subscription_id=sub1.id,
            product_id=p_erp.id,
            quantity=1,
            tax_id=tax_10.id if tax_10 else None,
            unit_price=p_erp.sales_price,
            variant_price=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("100.00"),
            line_total=Decimal("1100.00"),
        )
        db.session.add(sub_line)
        db.session.flush()

        # Seed an invoice for period 1 (paid)
        p1_start = today - timedelta(days=60)
        p1_end = today - timedelta(days=30)
        inv1 = Invoice(
            invoice_number=f"INV-SEED-001",
            subscription_id=sub1.id,
            customer_id=c1.id,
            status="paid",
            issue_date=p1_start,
            due_date=p1_start + timedelta(days=14),
            billing_period_start=p1_start,
            billing_period_end=p1_end,
            subtotal=Decimal("1000.00"),
            tax_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            total=Decimal("1100.00"),
            amount_paid=Decimal("1100.00"),
        )
        db.session.add(inv1)
        db.session.flush()

        inv1_line = InvoiceLine(
            invoice_id=inv1.id,
            product_id=p_erp.id,
            description="Cloud ERP Enterprise (Monthly)",
            quantity=1,
            unit_price=Decimal("1000.00"),
            tax_amount=Decimal("100.00"),
            line_total=Decimal("1100.00"),
        )
        db.session.add(inv1_line)

        # Seed payment for inv1
        pay1 = Payment(
            payment_number="PAY-SEED-001",
            invoice_id=inv1.id,
            customer_id=c1.id,
            amount=Decimal("1100.00"),
            method="credit_card",
            date=p1_start + timedelta(days=2),
            note="Auto-pay online",
            status="completed",
        )
        db.session.add(pay1)

        # Seed an overdue invoice for period 2 (unpaid)
        p2_start = today - timedelta(days=30)
        p2_end = today
        inv2 = Invoice(
            invoice_number=f"INV-SEED-002",
            subscription_id=sub1.id,
            customer_id=c1.id,
            status="confirmed",
            issue_date=p2_start,
            due_date=p2_start + timedelta(days=14),  # 16 days ago -> overdue!
            billing_period_start=p2_start,
            billing_period_end=p2_end,
            subtotal=Decimal("1000.00"),
            tax_amount=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            total=Decimal("1100.00"),
            amount_paid=Decimal("0.00"),
        )
        db.session.add(inv2)
        db.session.flush()

        inv2_line = InvoiceLine(
            invoice_id=inv2.id,
            product_id=p_erp.id,
            description="Cloud ERP Enterprise (Monthly)",
            quantity=1,
            unit_price=Decimal("1000.00"),
            tax_amount=Decimal("100.00"),
            line_total=Decimal("1100.00"),
        )
        db.session.add(inv2_line)

    db.session.commit()
    print("Database seeding completed.")


if __name__ == "__main__":
    from backend.app import create_app

    app = create_app()
    with app.app_context():
        run_seed()

