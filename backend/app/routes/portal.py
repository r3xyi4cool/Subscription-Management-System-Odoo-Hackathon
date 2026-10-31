from flask import Blueprint, request
from sqlalchemy import or_

from backend.app.extensions import db
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice
from backend.app.models.notification import Notification
from backend.app.utils.decorators import role_required, get_current_user_info
from backend.app.utils.errors import NotFoundError, success_response
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
    auth_id, _, customer_id, _ = get_current_user_info()

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

    unread_notifications_count = Notification.query.filter(
        or_(Notification.user_id == auth_id, Notification.customer_id == customer_id),
        Notification.is_read.is_(False),
    ).count()

    recent_notifications = [
        n.to_dict()
        for n in Notification.query.filter(
            or_(Notification.user_id == auth_id, Notification.customer_id == customer_id)
        )
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(5)
        .all()
    ]

    # Find earliest upcoming next_billing_date from active subscriptions
    active_subs = (
        Subscription.query.filter_by(customer_id=customer_id, status="active")
        .order_by(Subscription.next_billing_date.asc())
        .all()
    )
    next_renewal_date = (
        active_subs[0].next_billing_date.isoformat()
        if active_subs and active_subs[0].next_billing_date
        else None
    )

    data = {
        "active_subscriptions_count": active_subs_count,
        "total_spent_paise": int(round(total_spent * 100)),
        "total_spent": total_spent,
        "pending_invoices_count": len(pending_invoices),
        "pending_amount_paise": int(round(pending_amount * 100)),
        "pending_amount": pending_amount,
        "balance_due_paise": int(round(pending_amount * 100)),
        "balance_due": pending_amount,
        "next_renewal_date": next_renewal_date,
        "recent_invoices": recent_invoices,
        "recent_subscriptions": recent_subscriptions,
        "unread_notifications_count": unread_notifications_count,
        "recent_notifications": recent_notifications,
    }

    return success_response(data, status_code=200)


@portal_bp.route("/notifications", methods=["GET"])
@role_required("customer")
def my_notifications():
    auth_id, _, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Notification.query.filter(
        or_(Notification.user_id == auth_id, Notification.customer_id == customer_id)
    ).order_by(Notification.created_at.desc(), Notification.id.desc())

    is_read = request.args.get("is_read")
    if is_read is not None:
        if is_read.lower() in ("true", "1"):
            query = query.filter_by(is_read=True)
        elif is_read.lower() in ("false", "0"):
            query = query.filter_by(is_read=False)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([n.to_dict() for n in items], total, page, per_page)


@portal_bp.route("/notifications/unread-count", methods=["GET"])
@role_required("customer")
def my_notifications_unread_count():
    auth_id, _, customer_id, _ = get_current_user_info()
    count = Notification.query.filter(
        or_(Notification.user_id == auth_id, Notification.customer_id == customer_id),
        Notification.is_read.is_(False),
    ).count()
    return success_response({"count": count, "unread_count": count})


@portal_bp.route("/notifications/<int:notification_id>/read", methods=["PATCH"])
@role_required("customer")
def mark_notification_read(notification_id):
    auth_id, _, customer_id, _ = get_current_user_info()
    notification = db.session.get(Notification, notification_id)
    if not notification:
        raise NotFoundError(f"Notification with ID {notification_id} not found.")

    if notification.user_id != auth_id and notification.customer_id != customer_id:
        raise NotFoundError(f"Notification with ID {notification_id} not found.")

    notification.is_read = True
    db.session.commit()
    return success_response(notification.to_dict(), message="Notification marked as read.")


@portal_bp.route("/notifications/read-all", methods=["POST"])
@role_required("customer")
def mark_all_notifications_read():
    auth_id, _, customer_id, _ = get_current_user_info()
    Notification.query.filter(
        or_(Notification.user_id == auth_id, Notification.customer_id == customer_id),
        Notification.is_read.is_(False),
    ).update({Notification.is_read: True}, synchronize_session=False)
    db.session.commit()
    return success_response({"message": "All notifications marked as read."})
