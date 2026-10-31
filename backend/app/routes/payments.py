import uuid
from datetime import date
from decimal import Decimal
from flask import Blueprint, request
from marshmallow import ValidationError

from backend.app.extensions import db
from backend.app.models.billing import Invoice, Payment
from backend.app.schemas.billing_schemas import PaymentCreateSchema
from backend.app.services.audit_service import log_audit
from backend.app.services.notification_service import NotificationService
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

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("", methods=["POST"])
@role_required("admin", "staff")
def create_payment():
    json_data = request.get_json(silent=True) or {}
    schema = PaymentCreateSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid payment data",
                    "details": err.messages,
                }
            },
            400,
        )

    # Row-lock invoice to serialize concurrent payments and prevent overpayment race conditions
    invoice = db.session.query(Invoice).with_for_update().filter_by(id=data["invoice_id"]).first()
    if not invoice:
        raise NotFoundError(f"Invoice with ID {data['invoice_id']} not found.")

    payment_amount = Decimal(str(data["amount"]))
    if payment_amount <= 0:
        raise BadRequestError("Payment amount must be greater than zero.")

    remaining_due = invoice.total - invoice.amount_paid
    if payment_amount > remaining_due:
        return (
            {
                "error": {
                    "code": "OVERPAYMENT_REJECTED",
                    "message": f"Payment amount (${float(payment_amount):.2f}) exceeds remaining balance (${float(remaining_due):.2f}). Overpayment is not allowed.",
                    "details": {
                        "total": float(invoice.total),
                        "amount_paid": float(invoice.amount_paid),
                        "remaining_due": float(remaining_due),
                    },
                }
            },
            400,
        )

    payment_date = data.get("date") or date.today()
    payment_number = f"PAY-{uuid.uuid4().hex[:8].upper()}"

    payment = Payment(
        payment_number=payment_number,
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        amount=payment_amount,
        method=data["method"],
        date=payment_date,
        note=data.get("note"),
        status="completed",
    )
    db.session.add(payment)
    db.session.flush()

    # Update invoice amount paid and status
    invoice.amount_paid += payment_amount
    if invoice.amount_paid >= invoice.total:
        invoice.status = "paid"
    else:
        # If invoice was draft, move it to confirmed upon receiving partial payment
        if invoice.status == "draft":
            invoice.status = "confirmed"

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="payment",
        entity_id=payment.id,
        action="create",
        new_values=payment.to_dict(),
    )
    NotificationService.create_notification(
        customer_id=payment.customer_id,
        title="Payment Received",
        message=f"Payment of ₹{float(payment.amount):.2f} received for invoice {invoice.invoice_number or f'INV-{invoice.id}'}. Thank you!",
        type="payment",
        link_url=f"/me/invoices/{invoice.invoice_number or invoice.id}",
        dedupe_key=f"pay_rec_{payment.id}",
    )
    db.session.commit()

    return success_response(payment.to_dict(), status_code=201, message="Payment recorded successfully.")


@payments_bp.route("", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_payments():
    auth_id, role, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Payment.query.order_by(Payment.id.desc())

    if role == "customer":
        query = query.filter_by(customer_id=customer_id)
    else:
        req_customer_id = request.args.get("customer_id")
        if req_customer_id:
            query = query.filter_by(customer_id=req_customer_id)

    invoice_id = request.args.get("invoice_id")
    if invoice_id:
        query = query.filter_by(invoice_id=invoice_id)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@payments_bp.route("/<int:payment_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_payment(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        raise NotFoundError(f"Payment with ID {payment_id} not found.")

    enforce_customer_isolation(payment.customer_id)
    return success_response(payment.to_dict())


@payments_bp.route("/<int:payment_id>", methods=["PATCH"])
@role_required("admin", "staff")
def update_payment(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        raise NotFoundError(f"Payment with ID {payment_id} not found.")

    old_values = payment.to_dict()
    data = request.get_json(silent=True) or {}

    if "note" in data:
        payment.note = data["note"]
    if "status" in data:
        payment.status = data["status"]

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="payment",
        entity_id=payment.id,
        action="update",
        old_values=old_values,
        new_values=payment.to_dict(),
    )
    db.session.commit()
    return success_response(payment.to_dict(), message="Payment updated successfully.")
