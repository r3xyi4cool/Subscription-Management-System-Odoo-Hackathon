from datetime import date
from backend.app.services.billing_service import BillingService


def scheduled_billing_task(app):
    with app.app_context():
        try:
            today = date.today()
            print(f"[JOB] Running daily billing cycle for {today}...")
            result = BillingService.generate_invoices_for_due_subscriptions(
                as_of_date=today
            )
            print(
                f"[JOB] Billing complete: {result['created_count']} created, {result['skipped_count']} skipped."
            )
        except Exception as e:
            print(f"[JOB ERROR] Error in billing job: {e}")

