from datetime import datetime, timezone, date
from flask import Blueprint, request

from backend.app.extensions import db
from backend.app.models.subscription import Subscription
from backend.app.services.billing_service import add_billing_period
from backend.app.utils.decorators import (
    role_required,
    get_current_user_info,
    enforce_customer_isolation,
)
from backend.app.utils.errors import (
    NotFoundError,
    ConflictError,
    success_response,
)
from backend.app.utils.pagination import get_pagination_params, paginated_response

subscriptions_bp = Blueprint("subscriptions", __name__, url_prefix="/subscriptions")


@subscriptions_bp.route("", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_subscriptions():
    auth_id, role, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Subscription.query.order_by(Subscription.id.desc())
    if role == "customer":
        query = query.filter_by(customer_id=customer_id)
    else:
        req_customer_id = request.args.get("customer_id")
        if req_customer_id:
            query = query.filter_by(customer_id=req_customer_id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    plan_id = request.args.get("plan_id")
    if plan_id:
        query = query.filter_by(plan_id=plan_id)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@subscriptions_bp.route("/<int:subscription_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription with ID {subscription_id} not found.")

    enforce_customer_isolation(subscription.customer_id)
    return success_response(subscription.to_dict())


@subscriptions_bp.route("/<int:subscription_id>/activate", methods=["POST"])
@role_required("admin", "staff", "customer")
def activate_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription with ID {subscription_id} not found.")

    enforce_customer_isolation(subscription.customer_id)

    # Valid transitions: confirmed -> active, paused -> active, draft -> active
    if subscription.status not in ("confirmed", "paused", "draft"):
        raise ConflictError(
            f"Cannot activate subscription from status '{subscription.status}'."
        )

    subscription.status = "active"
    subscription.paused_at = None
    db.session.commit()

    return success_response(
        subscription.to_dict(),
        status_code=200,
        message="Subscription activated successfully.",
    )


@subscriptions_bp.route("/<int:subscription_id>/pause", methods=["POST"])
@role_required("admin", "staff", "customer")
def pause_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription with ID {subscription_id} not found.")

    enforce_customer_isolation(subscription.customer_id)

    if not subscription.plan.allow_pause:
        return (
            {
                "error": {
                    "code": "ACTION_NOT_ALLOWED",
                    "message": "The associated plan does not allow pausing.",
                    "details": {},
                }
            },
            409,
        )

    if subscription.status != "active":
        raise ConflictError(
            f"Cannot pause subscription in status '{subscription.status}'. Only active subscriptions can be paused."
        )

    subscription.status = "paused"
    subscription.paused_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(
        subscription.to_dict(),
        status_code=200,
        message="Subscription paused successfully.",
    )


@subscriptions_bp.route("/<int:subscription_id>/close", methods=["POST"])
@role_required("admin", "staff", "customer")
def close_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription with ID {subscription_id} not found.")

    enforce_customer_isolation(subscription.customer_id)

    if not subscription.plan.allow_close:
        return (
            {
                "error": {
                    "code": "ACTION_NOT_ALLOWED",
                    "message": "The associated plan does not allow early cancellation/closing.",
                    "details": {},
                }
            },
            409,
        )

    if subscription.status == "closed":
        raise ConflictError("Subscription is already closed.")

    subscription.status = "closed"
    subscription.cancelled_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(
        subscription.to_dict(),
        status_code=200,
        message="Subscription closed successfully.",
    )


@subscriptions_bp.route("/<int:subscription_id>/renew", methods=["POST"])
@role_required("admin", "staff", "customer")
def renew_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription with ID {subscription_id} not found.")

    enforce_customer_isolation(subscription.customer_id)

    if not subscription.plan.allow_renew:
        return (
            {
                "error": {
                    "code": "ACTION_NOT_ALLOWED",
                    "message": "The associated plan does not allow renewal.",
                    "details": {},
                }
            },
            409,
        )

    today = date.today()
    subscription.status = "active"
    subscription.current_period_start = today
    subscription.current_period_end = add_billing_period(today, subscription.plan.billing_period)
    subscription.next_billing_date = today
    subscription.cancelled_at = None
    subscription.paused_at = None
    db.session.commit()

    return success_response(
        subscription.to_dict(),
        status_code=200,
        message="Subscription renewed successfully.",
    )
