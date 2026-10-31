from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from backend.app.extensions import db
from backend.app.models.customer import Customer
from backend.app.models.catalog import Plan, Product
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.billing import Invoice, InvoiceLine
from backend.app.models.notification import Notification
from backend.app.services.notification_service import NotificationService
from backend.app.services.billing_service import BillingService


def test_notification_creation_and_deduplication(app, customer_user):
    with app.app_context():
        # Create notification
        n1 = NotificationService.create_notification(
            customer_id=customer_user.id,
            title="System Alert",
            message="Your account has been created.",
            type="system",
            link_url="/portal/account",
            dedupe_key="sys_welcome_1",
        )
        db.session.commit()
        assert n1.id is not None
        assert n1.is_read is False
        assert n1.user_id == customer_user.auth_id

        # Try duplicate
        n2 = NotificationService.create_notification(
            customer_id=customer_user.id,
            title="System Alert Duplicate",
            message="Your account has been created again.",
            type="system",
            dedupe_key="sys_welcome_1",
        )
        assert n2.id == n1.id
        assert n2.title == "System Alert"  # Existing returned intact


def test_billing_job_triggers_invoice_notification(app, customer_user):
    with app.app_context():
        plan = Plan(
            name="Notif Plan",
            billing_period="monthly",
            min_quantity=1,
            start_date=date.today(),
            is_active=True,
        )
        product = Product(name="Notif Product", sales_price=Decimal("200.00"), is_active=True)
        db.session.add_all([plan, product])
        db.session.flush()

        today = date.today()
        sub = Subscription(
            subscription_number="SUB-NOTIF-1",
            customer_id=customer_user.id,
            plan_id=plan.id,
            status="active",
            start_date=today,
            current_period_start=today,
            current_period_end=today + timedelta(days=30),
            next_billing_date=today,
        )
        db.session.add(sub)
        db.session.flush()

        line = SubscriptionLine(
            subscription_id=sub.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("200.00"),
            variant_price=Decimal("0.00"),
            line_total=Decimal("200.00"),
        )
        db.session.add(line)
        db.session.commit()

        # Run billing generator
        res = BillingService.run_billing_job(as_of_date=today, auth_id=1)
        assert res["created_count"] >= 1

        # Check notification
        notif = Notification.query.filter_by(
            customer_id=customer_user.id, type="invoice"
        ).order_by(Notification.id.desc()).first()
        assert notif is not None
        assert "New invoice" in notif.message
        assert notif.is_read is False


def test_invoice_send_and_payment_triggers_notifications(client, app, admin_token, customer_user):
    with app.app_context():
        inv = Invoice(
            invoice_number="INV-SEND-99",
            customer_id=customer_user.id,
            status="confirmed",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            billing_period_start=date.today(),
            billing_period_end=date.today() + timedelta(days=30),
            subtotal=Decimal("500.00"),
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total=Decimal("500.00"),
            amount_paid=Decimal("0.00"),
        )
        db.session.add(inv)
        db.session.commit()
        inv_id = inv.id

    # 1. Staff triggers /send
    send_res = client.post(
        f"/api/v1/invoices/{inv_id}/send",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert send_res.status_code == 200

    with app.app_context():
        sent_notif = Notification.query.filter_by(
            customer_id=customer_user.id, dedupe_key=f"inv_sent_{inv_id}"
        ).first()
        assert sent_notif is not None
        assert "has been sent" in sent_notif.message

    # 2. Staff records payment
    pay_res = client.post(
        "/api/v1/payments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "invoice_id": inv_id,
            "amount": "500.00",
            "method": "credit_card",
        },
    )
    assert pay_res.status_code == 201

    with app.app_context():
        pay_notif = Notification.query.filter_by(
            customer_id=customer_user.id, type="payment"
        ).order_by(Notification.id.desc()).first()
        assert pay_notif is not None
        assert "Payment of ₹500.00 received" in pay_notif.message


def test_payment_reminder_deduplication(app, customer_user):
    with app.app_context():
        inv = Invoice(
            invoice_number="INV-REMIND-01",
            customer_id=customer_user.id,
            status="confirmed",
            issue_date=date.today() - timedelta(days=10),
            due_date=date.today() + timedelta(days=3),
            billing_period_start=date.today() - timedelta(days=10),
            billing_period_end=date.today() + timedelta(days=20),
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total=Decimal("100.00"),
            amount_paid=Decimal("0.00"),
        )
        db.session.add(inv)
        db.session.commit()

        # Send reminder
        r1 = NotificationService.send_payment_reminder(inv, days_until_due=3)
        assert r1.type == "reminder"
        assert "due in 3 days" in r1.message

        # Send again today -> deduplicated
        r2 = NotificationService.send_payment_reminder(inv, days_until_due=3)
        assert r2.id == r1.id


def test_portal_notifications_lifecycle(client, app, customer_token, customer_user):
    with app.app_context():
        # Clear existing notifications for test isolation
        Notification.query.filter_by(customer_id=customer_user.id).delete()
        db.session.commit()

        # Create two notifications
        n1 = NotificationService.create_notification(
            customer_id=customer_user.id,
            title="Notice 1",
            message="Message 1",
            type="system",
        )
        n2 = NotificationService.create_notification(
            customer_id=customer_user.id,
            title="Notice 2",
            message="Message 2",
            type="reminder",
        )
        db.session.commit()
        n1_id = n1.id

    auth_hdr = {"Authorization": f"Bearer {customer_token}"}

    # 1. Unread count
    c_res = client.get("/api/v1/me/notifications/unread-count", headers=auth_hdr)
    assert c_res.status_code == 200
    assert c_res.get_json()["data"]["count"] == 2

    # 2. List notifications
    l_res = client.get("/api/v1/me/notifications", headers=auth_hdr)
    assert l_res.status_code == 200
    data = l_res.get_json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 3. Mark one read
    read_res = client.patch(f"/api/v1/me/notifications/{n1_id}/read", headers=auth_hdr)
    assert read_res.status_code == 200
    assert read_res.get_json()["data"]["is_read"] is True

    # Check unread count decremented
    c_res2 = client.get("/api/v1/me/notifications/unread-count", headers=auth_hdr)
    assert c_res2.get_json()["data"]["count"] == 1

    # 4. Mark all read
    all_res = client.post("/api/v1/me/notifications/read-all", headers=auth_hdr)
    assert all_res.status_code == 200

    c_res3 = client.get("/api/v1/me/notifications/unread-count", headers=auth_hdr)
    assert c_res3.get_json()["data"]["count"] == 0
