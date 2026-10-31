from datetime import date
from decimal import Decimal
from flask import Blueprint, request
from sqlalchemy import func

from backend.app.extensions import db
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice, Payment
from backend.app.utils.decorators import role_required, get_current_user_info
from backend.app.utils.errors import success_response

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/summary", methods=["GET"])
@role_required("admin", "staff")
def summary():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    customer_id = request.args.get("customer_id")
    plan_id = request.args.get("plan_id")

    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            pass

    today = date.today()

    # Base query filters for subscriptions
    sub_query = db.session.query(
        func.count(Subscription.id).label("total_subs"),
        func.count(
            func.nullif(Subscription.status == "active", False)
        ).label("active_subs"),
    )
    if customer_id:
        sub_query = sub_query.filter(Subscription.customer_id == customer_id)
    if plan_id:
        sub_query = sub_query.filter(Subscription.plan_id == plan_id)
    if start_date:
        sub_query = sub_query.filter(Subscription.start_date >= start_date)
    if end_date:
        sub_query = sub_query.filter(Subscription.start_date <= end_date)

    sub_res = sub_query.first()
    total_subscriptions = sub_res[0] if sub_res else 0
    active_subscriptions = sub_res[1] if sub_res else 0

    # Invoices aggregate query
    inv_query = db.session.query(
        func.count(Invoice.id).label("total_invoices"),
        func.coalesce(
            func.sum(
                db.case(
                    (Invoice.status.in_(["confirmed", "paid"]), Invoice.total),
                    else_=Decimal("0.00"),
                )
            ),
            Decimal("0.00"),
        ).label("revenue"),
        func.coalesce(
            func.sum(
                db.case(
                    (
                        Invoice.status.in_(["draft", "confirmed"]),
                        Invoice.total - Invoice.amount_paid,
                    ),
                    else_=Decimal("0.00"),
                )
            ),
            Decimal("0.00"),
        ).label("amount_owed"),
        func.count(
            db.case(
                (
                    (Invoice.status.in_(["draft", "confirmed"]))
                    & (Invoice.due_date < today)
                    & (Invoice.amount_paid < Invoice.total),
                    Invoice.id,
                ),
                else_=None,
            )
        ).label("overdue_count"),
        func.coalesce(
            func.sum(
                db.case(
                    (
                        (Invoice.status.in_(["draft", "confirmed"]))
                        & (Invoice.due_date < today)
                        & (Invoice.amount_paid < Invoice.total),
                        Invoice.total - Invoice.amount_paid,
                    ),
                    else_=Decimal("0.00"),
                )
            ),
            Decimal("0.00"),
        ).label("overdue_amount"),
    )
    if customer_id:
        inv_query = inv_query.filter(Invoice.customer_id == customer_id)
    if plan_id:
        inv_query = inv_query.join(Invoice.subscription).filter(
            Subscription.plan_id == plan_id
        )
    if start_date:
        inv_query = inv_query.filter(Invoice.issue_date >= start_date)
    if end_date:
        inv_query = inv_query.filter(Invoice.issue_date <= end_date)

    inv_res = inv_query.first()
    total_invoices = inv_res[0] if inv_res else 0
    revenue = float(inv_res[1]) if inv_res and inv_res[1] is not None else 0.0
    amount_owed = float(inv_res[2]) if inv_res and inv_res[2] is not None else 0.0
    overdue_invoices_count = inv_res[3] if inv_res else 0
    overdue_amount = float(inv_res[4]) if inv_res and inv_res[4] is not None else 0.0

    # Payments aggregate query
    pay_query = db.session.query(
        func.count(Payment.id).label("payments_count"),
        func.coalesce(func.sum(Payment.amount), Decimal("0.00")).label(
            "payments_total"
        ),
    ).filter(Payment.status == "completed")
    if customer_id:
        pay_query = pay_query.filter(Payment.customer_id == customer_id)
    if start_date:
        pay_query = pay_query.filter(Payment.date >= start_date)
    if end_date:
        pay_query = pay_query.filter(Payment.date <= end_date)

    pay_res = pay_query.first()
    payments_count = pay_res[0] if pay_res else 0
    payments_total = float(pay_res[1]) if pay_res and pay_res[1] is not None else 0.0

    data = {
        "active_subscriptions": active_subscriptions,
        "total_subscriptions": total_subscriptions,
        "revenue": revenue,
        "payments": payments_total,
        "payments_count": payments_count,
        "amount_owed": amount_owed,
        "overdue_invoices": overdue_invoices_count,
        "overdue_amount": overdue_amount,
        "total_invoices": total_invoices,
    }

    return success_response(data, status_code=200)

