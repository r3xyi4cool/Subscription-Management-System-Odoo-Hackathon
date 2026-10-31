from datetime import date
from flask import Blueprint, request
from backend.app.services.billing_service import BillingService
from backend.app.utils.decorators import role_required, get_current_user_info
from backend.app.utils.errors import success_response

billing_trigger_bp = Blueprint("billing_trigger", __name__, url_prefix="/billing")


@billing_trigger_bp.route("/run", methods=["POST"])
@billing_trigger_bp.route("/trigger", methods=["POST"])
@role_required("admin")
def run_billing():
    json_data = request.get_json(silent=True) or {}
    as_of_date_str = json_data.get("as_of_date")
    as_of_date = None
    if as_of_date_str:
        try:
            as_of_date = date.fromisoformat(as_of_date_str)
        except ValueError:
            pass

    auth_id, _, _, _ = get_current_user_info()
    result = BillingService.generate_invoices_for_due_subscriptions(
        as_of_date=as_of_date, auth_id=auth_id
    )

    return success_response(
        result,
        status_code=200,
        message=f"Billing run completed. {result['created_count']} invoices created, {result['skipped_count']} skipped.",
    )

