import uuid
from datetime import date, timezone
from decimal import Decimal
from flask import Blueprint, request

from backend.app.extensions import db
from backend.app.models.billing import Invoice, Payment, Refund
from backend.app.services.audit_service import log_audit
from backend.app.utils.decorators import (
    role_required,
    get_current_user_info,
    enforce_customer_isolation,
)
from backend.app.utils.errors import (
    NotFoundError,
    BadRequestError,
    success_response,
)
from backend.app.utils.pagination import get_pagination_params, paginated_response

refunds_bp = Blueprint("refunds", __name__, url_prefix="/refunds")


@refunds_bp.route("", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_refunds():
    auth_id, role, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Refund.query.order_by(Refund.id.desc())

    if role == "customer":
        query = query.join(Invoice, Refund.invoice_id == Invoice.id).filter(
            Invoice.customer_id == customer_id
        )
    else:
        req_customer_id = request.args.get("customer_id")
        if req_customer_id:
            query = query.join(Invoice, Refund.invoice_id == Invoice.id).filter(
                Invoice.customer_id == req_customer_id
            )

    invoice_id = request.args.get("invoice_id")
    if invoice_id:
        query = query.filter(Refund.invoice_id == invoice_id)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([r.to_dict() for r in items], total, page, per_page)


@refunds_bp.route("/<int:refund_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_refund(refund_id):
    refund = db.session.get(Refund, refund_id)
    if not refund:
        raise NotFoundError(f"Refund with ID {refund_id} not found.")

    if refund.invoice:
        enforce_customer_isolation(refund.invoice.customer_id)
    return success_response(refund.to_dict())


@refunds_bp.route("", methods=["POST"])
@role_required("admin", "staff")
def create_refund():
    data = request.get_json(silent=True) or {}
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        raise BadRequestError("Field 'invoice_id' is required.")

    invoice = db.session.get(Invoice, int(invoice_id))
    if not invoice:
        raise NotFoundError(f"Invoice with ID {invoice_id} not found.")

    amount_val = data.get("amount")
    if amount_val is None and "amount_paise" in data:
        amount_val = Decimal(str(data["amount_paise"])) / Decimal("100.00")
    elif amount_val is not None:
        amount_val = Decimal(str(amount_val))
    else:
        raise BadRequestError("Field 'amount' or 'amount_paise' is required.")

    if amount_val <= 0:
        raise BadRequestError("Refund amount must be greater than zero.")

    total_refunded = (
        db.session.query(
            db.func.coalesce(db.func.sum(Refund.amount), Decimal("0.00"))
        )
        .filter(Refund.invoice_id == invoice.id)
        .scalar()
    )
    max_refundable = invoice.amount_paid - total_refunded
    if amount_val > max_refundable:
        return (
            {
                "error": {
                    "code": "REFUND_EXCEEDS_PAID",
                    "message": f"Refund amount (${float(amount_val):.2f}) exceeds max refundable amount (${float(max_refundable):.2f}).",
                    "details": {
                        "amount_paid": float(invoice.amount_paid),
                        "already_refunded": float(total_refunded),
                        "max_refundable": float(max_refundable),
                    },
                }
            },
            400,
        )

    refund = Refund(
        refund_number=f"REF-{uuid.uuid4().hex[:8].upper()}",
        invoice_id=invoice.id,
        payment_id=data.get("payment_id"),
        amount=amount_val,
        reason=data.get("reason"),
        date=data.get("date") or date.today(),
    )
    db.session.add(refund)
    db.session.flush()

    # An invoice that was paid in full remains paid; refunds do not cause paid invoices to reappear as overdue or outstanding
    if invoice.status != "paid":
        invoice.amount_paid = max(Decimal("0.00"), invoice.amount_paid - amount_val)
        if invoice.amount_paid < invoice.total:
            invoice.status = "confirmed"

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="refund",
        entity_id=refund.id,
        action="create",
        new_values=refund.to_dict(),
    )
    db.session.commit()

    return success_response(refund.to_dict(), status_code=201, message="Refund processed successfully.")


@refunds_bp.route("/<int:refund_id>", methods=["PATCH"])
@role_required("admin", "staff")
def update_refund(refund_id):
    refund = db.session.get(Refund, refund_id)
    if not refund:
        raise NotFoundError(f"Refund with ID {refund_id} not found.")

    old_values = refund.to_dict()
    data = request.get_json(silent=True) or {}
    if "reason" in data:
        refund.reason = data["reason"]

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="refund",
        entity_id=refund.id,
        action="update",
        old_values=old_values,
        new_values=refund.to_dict(),
    )
    db.session.commit()
    return success_response(refund.to_dict(), message="Refund updated successfully.")

