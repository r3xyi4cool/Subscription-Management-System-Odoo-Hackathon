import concurrent.futures
from datetime import date, timedelta
from decimal import Decimal
import pytest

from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.customer import Customer
from backend.app.models.catalog import Product, Plan, Discount
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.billing import Invoice, Payment
from backend.app.services.billing_service import BillingService


def test_concurrent_parallel_invoice_generation(app):
    """
    Test 1: Parallel invoice generation.
    Multiple concurrent worker threads run the billing engine simultaneously for the same due subscriptions.
    Idempotency and unique constraint guarantee that exactly ONE invoice is created per billing period.
    """
    with app.app_context():
        # Setup customer, product, plan, subscription
        auth = Auth(email="concurrent_sub@brightloop.test", role="customer")
        auth.set_password("Brightloop@2026!")
        db.session.add(auth)
        db.session.flush()

        customer = Customer(auth_id=auth.id, name="Concurrency Test Corp", is_active=True)
        db.session.add(customer)
        db.session.flush()

        product = Product(name="Concurrent Cloud", sales_price=Decimal("500.00"), is_active=True)
        plan = Plan(name="Monthly Standard", price=Decimal("500.00"), billing_period="monthly", is_active=True)
        db.session.add_all([product, plan])
        db.session.flush()

        today = date.today()
        sub = Subscription(
            subscription_number="SUB-CONCUR-001",
            customer_id=customer.id,
            plan_id=plan.id,
            status="active",
            start_date=today - timedelta(days=30),
            current_period_start=today - timedelta(days=30),
            current_period_end=today,
            next_billing_date=today,
        )
        db.session.add(sub)
        db.session.flush()

        sub_line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.sales_price,
            amount=product.sales_price,
        )
        db.session.add(sub_line)
        db.session.commit()
        sub_id = sub.id

    def run_worker():
        with app.app_context():
            # In each thread, run the billing generation
            res = BillingService.generate_invoices_for_due_subscriptions(as_of_date=today)
            return res

    # Run 8 concurrent threads simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(run_worker) for _ in range(8)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    with app.app_context():
        invoices = Invoice.query.filter_by(subscription_id=sub_id).all()
        # Exactly ONE invoice must exist for this period
        assert len(invoices) == 1
        assert invoices[0].total == Decimal("500.00")

        # Sum of created across all runs must be 1
        total_created = sum(r["created_count"] for r in results)
        assert total_created == 1


def test_concurrent_simultaneous_payments(client, admin_headers):
    """
    Test 2: Simultaneous payments and overpayment race prevention.
    When multiple requests attempt to pay an invoice concurrently, row-level locks
    guarantee that payments never exceed invoice balance.
    """
    # Create invoice of 1000.00
    res = client.post(
        "/api/v1/auth/signup",
        json={"email": "concur_pay@brightloop.test", "password": "Password123!", "company_name": "Pay Test"},
    )
    assert res.status_code == 201

    with client.application.app_context():
        cust = Customer.query.join(Auth).filter(Auth.email == "concur_pay@brightloop.test").first()
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

    # Test 2A: Two concurrent payments of 500 each (exact sum)
    def pay_amount(amount):
        return client.post(
            "/api/v1/payments",
            headers=admin_headers,
            json={"invoice_id": inv_id, "amount": amount, "method": "card"},
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(pay_amount, 500.00)
        f2 = executor.submit(pay_amount, 500.00)
        r1 = f1.result()
        r2 = f2.result()

    assert r1.status_code == 201
    assert r2.status_code == 201

    with client.application.app_context():
        inv = db.session.get(Invoice, inv_id)
        assert inv.amount_paid == Decimal("1000.00")
        assert inv.status == "paid"

    # Test 2B: Now attempting another payment on the paid invoice must be rejected as overpayment
    r3 = client.post(
        "/api/v1/payments",
        headers=admin_headers,
        json={"invoice_id": inv_id, "amount": 100.00, "method": "card"},
    )
    assert r3.status_code == 400
    assert r3.get_json()["error"]["code"] == "OVERPAYMENT_REJECTED"


def test_atomic_discount_usage_limit(app):
    """
    Test 3: Atomic discount usage limit.
    When a discount has a strict usage limit (e.g. 3), concurrent billing runs
    or increments must never exceed the usage limit.
    """
    with app.app_context():
        discount = Discount(
            name="Limited Concurrency Voucher",
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_increment) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Exactly 3 must have succeeded (affected == 1), 7 failed (affected == 0)
    success_count = sum(r for r in results)
    assert success_count == 3

    with app.app_context():
        discount = db.session.get(Discount, disc_id)
        assert discount.used_count == 3
