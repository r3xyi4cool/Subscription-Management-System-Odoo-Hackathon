import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from flask import Blueprint, request

from backend.app.extensions import db
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.catalog import Plan
from backend.app.services.billing_service import add_billing_period
from backend.app.services.audit_service import log_audit
from backend.app.utils.decorators import (
    role_required,
    get_current_user_info,
    enforce_customer_isolation,
)
from backend.app.utils.errors import (
    NotFoundError,
    ConflictError,
    BadRequestError,
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


@subscriptions_bp.route("", methods=["POST"])
@role_required("admin", "staff")
def create_subscription():
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    plan_id = data.get("plan_id")
    if not customer_id or not plan_id:
        raise BadRequestError("'customer_id' and 'plan_id' are required.")

    plan = db.session.get(Plan, int(plan_id))
    if not plan:
        raise NotFoundError(f"Plan with ID {plan_id} not found.")

    today = date.today()
    next_period_end = add_billing_period(today, plan.billing_period)
    sub_num = f"SUB-{uuid.uuid4().hex[:8].upper()}"

    subscription = Subscription(
        subscription_number=sub_num,
        customer_id=int(customer_id),
        plan_id=plan.id,
        status=data.get("status", "draft"),
        start_date=today,
        current_period_start=today,
        current_period_end=next_period_end,
        next_billing_date=today,
    )
    db.session.add(subscription)
    db.session.flush()

    lines_data = data.get("lines") or []
    for l in lines_data:
        sub_line = SubscriptionLine(
            subscription_id=subscription.id,
            product_id=int(l["product_id"]),
            variant_id=int(l["variant_id"]) if l.get("variant_id") else None,
            quantity=int(l.get("quantity", 1)),
            tax_id=int(l["tax_id"]) if l.get("tax_id") else None,
            discount_id=int(l["discount_id"]) if l.get("discount_id") else None,
            unit_price=Decimal(str(l.get("unit_price", "0.00"))),
            variant_price=Decimal(str(l.get("variant_price", "0.00"))),
            discount_amount=Decimal(str(l.get("discount_amount", "0.00"))),
            tax_amount=Decimal(str(l.get("tax_amount", "0.00"))),
            line_total=Decimal(str(l.get("line_total", "0.00"))),
        )
        db.session.add(sub_line)

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="subscription",
        entity_id=subscription.id,
        action="create",
        new_values=subscription.to_dict(),
    )
    db.session.commit()
    return success_response(subscription.to_dict(), status_code=201, message="Subscription created.")


@subscriptions_bp.route("/<int:subscription_id>", methods=["PATCH"])
@role_required("admin", "staff")
def update_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription with ID {subscription_id} not found.")

    old_values = subscription.to_dict()
    data = request.get_json(silent=True) or {}

    if "plan_id" in data:
        subscription.plan_id = int(data["plan_id"])
    if "status" in data:
        subscription.status = data["status"]

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="subscription",
        entity_id=subscription.id,
        action="update",
        old_values=old_values,
        new_values=subscription.to_dict(),
    )
    db.session.commit()
    return success_response(subscription.to_dict(), message="Subscription updated.")


@subscriptions_bp.route("/<int:subscription_id>/confirm", methods=["POST"])
@role_required("admin", "staff")
def confirm_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription with ID {subscription_id} not found.")

    if subscription.status not in ("draft", "quotation"):
        raise ConflictError(
            f"Cannot confirm subscription in status '{subscription.status}'."
        )

    subscription.status = "confirmed"
    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="subscription",
        entity_id=subscription.id,
        action="confirm",
        new_values=subscription.to_dict(),
    )
    db.session.commit()

    return success_response(
        subscription.to_dict(),
        status_code=200,
        message="Subscription confirmed successfully.",
    )


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


@subscriptions_bp.route("/<int:subscription_id>/resume", methods=["POST"])
@role_required("admin", "staff", "customer")
def resume_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription with ID {subscription_id} not found.")

    enforce_customer_isolation(subscription.customer_id)

    if subscription.status != "paused":
        raise ConflictError(
            f"Cannot resume subscription in status '{subscription.status}'. Only paused subscriptions can be resumed."
        )

    subscription.status = "active"
    subscription.paused_at = None
    db.session.commit()

    return success_response(
        subscription.to_dict(),
        status_code=200,
        message="Subscription resumed successfully.",
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
