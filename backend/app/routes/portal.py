from flask import Blueprint, request

from backend.app.extensions import db
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice
from backend.app.utils.decorators import role_required, get_current_user_info
from backend.app.utils.errors import success_response
from backend.app.utils.pagination import get_pagination_params, paginated_response

portal_bp = Blueprint("portal", __name__, url_prefix="/me")


@portal_bp.route("/subscriptions", methods=["GET"])
@role_required("customer")
def my_subscriptions():
    _, _, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Subscription.query.filter_by(customer_id=customer_id).order_by(
        Subscription.id.desc()
    )
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([s.to_dict() for s in items], total, page, per_page)


@portal_bp.route("/invoices", methods=["GET"])
@role_required("customer")
def my_invoices():
    _, _, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Invoice.query.filter_by(customer_id=customer_id).order_by(
        Invoice.id.desc()
    )
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([i.to_dict() for i in items], total, page, per_page)


@portal_bp.route("/dashboard", methods=["GET"])
@role_required("customer")
def my_dashboard():
    _, _, customer_id, _ = get_current_user_info()

    active_subs_count = Subscription.query.filter_by(
        customer_id=customer_id, status="active"
    ).count()

    invoices = Invoice.query.filter_by(customer_id=customer_id).all()
    total_spent = sum(float(inv.amount_paid) for inv in invoices)

    pending_invoices = [
        inv
        for inv in invoices
        if inv.status in ("draft", "confirmed") and inv.amount_paid < inv.total
    ]
    pending_amount = sum(float(inv.total - inv.amount_paid) for inv in pending_invoices)

    recent_invoices = [
        inv.to_dict()
        for inv in Invoice.query.filter_by(customer_id=customer_id)
        .order_by(Invoice.id.desc())
        .limit(5)
        .all()
    ]

    recent_subscriptions = [
        sub.to_dict()
        for sub in Subscription.query.filter_by(customer_id=customer_id)
        .order_by(Subscription.id.desc())
        .limit(5)
        .all()
    ]

    data = {
        "active_subscriptions_count": active_subs_count,
        "total_spent_paise": int(round(total_spent * 100)),
        "total_spent": total_spent,
        "pending_invoices_count": len(pending_invoices),
        "pending_amount_paise": int(round(pending_amount * 100)),
        "pending_amount": pending_amount,
        "recent_invoices": recent_invoices,
        "recent_subscriptions": recent_subscriptions,
    }

    return success_response(data, status_code=200)

