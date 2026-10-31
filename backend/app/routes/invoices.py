import uuid
from datetime import date, timezone, datetime
from decimal import Decimal
from flask import Blueprint, request, make_response
from marshmallow import ValidationError

from backend.app.extensions import db
from backend.app.models.billing import Invoice, Payment, Refund
from backend.app.schemas.billing_schemas import RefundCreateSchema
from backend.app.services.pdf_service import PDFService
from backend.app.services.mail_service import MailService
from backend.app.services.audit_service import log_audit
from backend.app.utils.decorators import (
    role_required,
    get_current_user_info,
    enforce_customer_isolation,
)
from backend.app.utils.errors import (
    NotFoundError,
    BadRequestError,
    ConflictError,
    success_response,
)
from backend.app.utils.pagination import get_pagination_params, paginated_response

invoices_bp = Blueprint("invoices", __name__, url_prefix="/invoices")


@invoices_bp.route("", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_invoices():
    auth_id, role, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Invoice.query.order_by(Invoice.id.desc())

    if role == "customer":
        query = query.filter_by(customer_id=customer_id)
    else:
        req_customer_id = request.args.get("customer_id")
        if req_customer_id:
            query = query.filter_by(customer_id=req_customer_id)

    subscription_id = request.args.get("subscription_id")
    if subscription_id:
        query = query.filter_by(subscription_id=subscription_id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@invoices_bp.route("/overdue", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_overdue_invoices():
    auth_id, role, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    today = date.today()
    query = Invoice.query.filter(
        Invoice.status.in_(["draft", "confirmed"]),
        Invoice.due_date < today,
        Invoice.amount_paid < Invoice.total,
    ).order_by(Invoice.due_date.asc())

    if role == "customer":
        query = query.filter_by(customer_id=customer_id)
    else:
        req_customer_id = request.args.get("customer_id")
        if req_customer_id:
            query = query.filter_by(customer_id=req_customer_id)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@invoices_bp.route("/outstanding", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_outstanding_invoices():
    auth_id, role, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Invoice.query.filter(
        Invoice.status.in_(["draft", "confirmed"]),
        Invoice.amount_paid < Invoice.total,
    ).order_by(Invoice.due_date.asc())

    if role == "customer":
        query = query.filter_by(customer_id=customer_id)
    else:
        req_customer_id = request.args.get("customer_id")
        if req_customer_id:
            query = query.filter_by(customer_id=req_customer_id)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@invoices_bp.route("/<int:invoice_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        raise NotFoundError(f"Invoice with ID {invoice_id} not found.")

    enforce_customer_isolation(invoice.customer_id)
    return success_response(invoice.to_dict())


@invoices_bp.route("/<int:invoice_id>/confirm", methods=["POST"])
@role_required("admin", "staff")
def confirm_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        raise NotFoundError(f"Invoice with ID {invoice_id} not found.")

    if invoice.status != "draft":
        raise ConflictError(
            f"Cannot confirm invoice in status '{invoice.status}'. Only draft invoices can be confirmed."
        )

    invoice.status = "confirmed"
    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="invoice",
        entity_id=invoice.id,
        action="confirm",
        new_values=invoice.to_dict(),
    )
    db.session.commit()

    return success_response(
        invoice.to_dict(), status_code=200, message="Invoice confirmed successfully."
    )


@invoices_bp.route("/<int:invoice_id>/pdf", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_invoice_pdf(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        raise NotFoundError(f"Invoice with ID {invoice_id} not found.")

    enforce_customer_isolation(invoice.customer_id)

    pdf_bytes = PDFService.generate_invoice_pdf(invoice)

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f"inline; filename=invoice_{invoice.invoice_number}.pdf"
    )
    return response


@invoices_bp.route("/<int:invoice_id>/send", methods=["POST"])
@role_required("admin", "staff")
def send_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        raise NotFoundError(f"Invoice with ID {invoice_id} not found.")

    pdf_bytes = PDFService.generate_invoice_pdf(invoice)
    MailService.send_invoice_email(invoice.customer.email, invoice, pdf_bytes)

    return success_response(
        {"message": f"Invoice #{invoice.invoice_number} sent to {invoice.customer.email}."},
        status_code=200,
    )


@invoices_bp.route("/<int:invoice_id>/cancel", methods=["POST"])
@role_required("admin", "staff")
def cancel_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        raise NotFoundError(f"Invoice with ID {invoice_id} not found.")

    if invoice.status == "paid" or invoice.amount_paid > 0 or invoice.payments.count() > 0:
        raise ConflictError("Cannot cancel an invoice with payments recorded. Please issue a refund instead.")

    invoice.status = "cancelled"
    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="invoice",
        entity_id=invoice.id,
        action="cancel",
        new_values=invoice.to_dict(),
    )
    db.session.commit()

    return success_response(
        invoice.to_dict(), status_code=200, message="Invoice cancelled successfully."
    )


@invoices_bp.route("/<int:invoice_id>/refund", methods=["POST"])
@role_required("admin", "staff")
def refund_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        raise NotFoundError(f"Invoice with ID {invoice_id} not found.")

    json_data = request.get_json(silent=True) or {}
    schema = RefundCreateSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid refund data",
                    "details": err.messages,
                }
            },
            400,
        )

    refund_amount = Decimal(str(data["amount"]))
    if refund_amount <= 0:
        raise BadRequestError("Refund amount must be greater than zero.")

    # Calculate total already refunded
    total_refunded = db.session.query(
        db.func.coalesce(db.func.sum(Refund.amount), Decimal("0.00"))
    ).filter(Refund.invoice_id == invoice.id).scalar()

    max_refundable = invoice.amount_paid - total_refunded
    if refund_amount > max_refundable:
        return (
            {
                "error": {
                    "code": "REFUND_EXCEEDS_PAID",
                    "message": f"Refund amount (${float(refund_amount):.2f}) exceeds max refundable amount (${float(max_refundable):.2f}).",
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
        amount=refund_amount,
        reason=data.get("reason"),
        date=data.get("date") or date.today(),
    )
    db.session.add(refund)
    db.session.flush()

    # Adjust invoice amount_paid
    invoice.amount_paid -= refund_amount
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
