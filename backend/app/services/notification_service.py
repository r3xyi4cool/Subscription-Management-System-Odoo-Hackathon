import logging
from datetime import date
from backend.app.extensions import db
from backend.app.models.notification import Notification
from backend.app.models.customer import Customer

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def create_notification(
        user_id=None,
        customer_id=None,
        title="",
        message="",
        type="system",
        link_url=None,
        dedupe_key=None,
    ) -> Notification:
        """
        Creates an in-app notification with deduplication support.
        """
        if user_id is None and customer_id is not None:
            customer = db.session.get(Customer, customer_id)
            if customer and customer.auth_id:
                user_id = customer.auth_id

        if dedupe_key:
            existing = Notification.query.filter_by(dedupe_key=dedupe_key).first()
            if existing:
                logger.info("Notification with dedupe_key %s already exists. Skipping duplicate.", dedupe_key)
                return existing

        notification = Notification(
            user_id=user_id,
            customer_id=customer_id,
            title=title,
            message=message,
            type=type,
            link_url=link_url,
            is_read=False,
            dedupe_key=dedupe_key,
        )
        db.session.add(notification)
        db.session.flush()
        logger.info("[NOTIFICATION] [%s] %s -> User: %s, Customer: %s", type.upper(), title, user_id, customer_id)
        return notification

    @staticmethod
    def send_payment_reminder(invoice, days_until_due=None) -> Notification:
        """
        Generates an automated payment reminder notification for an invoice.
        """
        today = date.today()
        is_overdue = (days_until_due is not None and days_until_due < 0) or (invoice.due_date < today)
        balance = invoice.total - invoice.amount_paid

        if is_overdue:
            msg = f"Invoice {invoice.invoice_number} is overdue. Amount due: ₹{float(balance):.2f}."
            title = f"Overdue Invoice: {invoice.invoice_number}"
        else:
            days_str = f"in {days_until_due} days" if days_until_due is not None else f"on {invoice.due_date}"
            msg = f"Invoice {invoice.invoice_number} is due {days_str}. Amount due: ₹{float(balance):.2f}."
            title = f"Payment Reminder: {invoice.invoice_number}"

        dedupe_key = f"reminder_{invoice.id}_{today.isoformat()}"
        return NotificationService.create_notification(
            customer_id=invoice.customer_id,
            title=title,
            message=msg,
            type="reminder",
            link_url=f"/me/invoices/{invoice.invoice_number or invoice.id}",
            dedupe_key=dedupe_key,
        )

