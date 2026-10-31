import argparse
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

from filelock import FileLock, Timeout

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice
from backend.app.models.notification import Notification
from backend.app.services.billing_service import BillingService
from backend.app.services.notification_service import NotificationService
from backend.app.services.audit_service import log_audit

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [Worker] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("worker")

LOCK_FILE = os.path.join(project_root, ".worker.lock")


def run_worker_tick(as_of_date: date = None) -> dict:
    """
    Executes a single tick of the local worker:
    1. Billing catch-up for due subscriptions.
    2. Automated payment reminders for invoices due in <= 3 days or overdue.
    3. Subscription lifecycle closure for expired subscriptions.
    """
    if as_of_date is None:
        as_of_date = date.today()

    logger.info("Starting worker tick for date: %s", as_of_date)

    # 1. Billing catch-up
    billing_res = BillingService.generate_invoices_for_due_subscriptions(
        as_of_date=as_of_date, auth_id=None
    )
    invoices_created = billing_res["created_count"]
    invoices_skipped = billing_res["skipped_count"]

    # 2. Payment reminders (due in <= 3 days or overdue)
    due_threshold = as_of_date + timedelta(days=3)
    due_invoices = Invoice.query.filter(
        Invoice.status.in_(["draft", "confirmed"]),
        Invoice.due_date <= due_threshold,
        Invoice.amount_paid < Invoice.total,
    ).all()

    reminders_sent = 0
    today_str = as_of_date.isoformat()
    for inv in due_invoices:
        days_until_due = (inv.due_date - as_of_date).days
        dedupe_key = f"reminder_{inv.id}_{today_str}"
        existing = Notification.query.filter_by(dedupe_key=dedupe_key).first()
        if not existing:
            NotificationService.send_payment_reminder(inv, days_until_due=days_until_due)
            reminders_sent += 1

    # 3. Subscription expiration checks (active subscriptions with auto_close plans past period end)
    active_subs = Subscription.query.filter(
        Subscription.status == "active",
        Subscription.current_period_end < as_of_date,
    ).all()

    subs_closed = 0
    for sub in active_subs:
        if sub.plan and sub.plan.auto_close:
            sub.status = "closed"
            subs_closed += 1
            log_audit(
                auth_id=None,
                entity_type="subscription",
                entity_id=sub.id,
                action="auto_close",
                new_values={"status": "closed", "reason": "auto_close_period_end"},
            )

    db.session.commit()

    logger.info(
        "Worker tick completed: %d invoices generated (%d skipped), %d reminders sent, %d expired subs closed.",
        invoices_created,
        invoices_skipped,
        reminders_sent,
        subs_closed,
    )

    return {
        "as_of_date": as_of_date.isoformat(),
        "invoices_created": invoices_created,
        "invoices_skipped": invoices_skipped,
        "reminders_sent": reminders_sent,
        "subs_closed": subs_closed,
    }


def run_worker_loop(once: bool = False, interval: int = 60, as_of: str = None):
    """
    Runs the worker with single-instance file lock.
    """
    app = create_app()
    lock = FileLock(LOCK_FILE, timeout=0.1)

    try:
        lock.acquire()
    except Timeout:
        logger.error("Another worker instance is already running (locked by %s). Exiting.", LOCK_FILE)
        sys.exit(1)

    logger.info("Worker lock acquired. Starting worker (once=%s, interval=%ds)...", once, interval)

    as_of_date = None
    if as_of:
        try:
            as_of_date = date.fromisoformat(as_of)
        except ValueError:
            logger.error("Invalid as_of date format: %s. Expected YYYY-MM-DD", as_of)
            lock.release()
            sys.exit(1)

    try:
        with app.app_context():
            if once:
                run_worker_tick(as_of_date=as_of_date)
                logger.info("One-shot worker run complete.")
                return

            while True:
                try:
                    run_worker_tick(as_of_date=as_of_date)
                except Exception as e:
                    logger.exception("Error during worker tick: %s", e)

                time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user (Ctrl+C).")
    finally:
        try:
            lock.release()
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
        except Exception:
            pass
        logger.info("Worker lock released. Clean shutdown.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SMS Background Billing & Reminder Worker")
    parser.add_argument("--once", action="store_true", help="Run a single tick and exit")
    parser.add_argument("--interval", type=int, default=60, help="Loop interval in seconds (default 60)")
    parser.add_argument("--as-of", type=str, default=None, help="Date override in YYYY-MM-DD format")
    args = parser.parse_args()

    run_worker_loop(once=args.once, interval=args.interval, as_of=args.as_of)
