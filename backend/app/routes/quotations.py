import uuid
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from flask import Blueprint, request
from marshmallow import ValidationError

from backend.app.extensions import db
from backend.app.models.customer import Customer
from backend.app.models.catalog import Product, Variant, Plan, Tax, Discount
from backend.app.models.quotation import Quotation, QuotationLine, QuotationTemplate
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.schemas.quotation_schemas import QuotationCreateSchema
from backend.app.services.pricing_service import PricingService
from backend.app.services.billing_service import add_billing_period
from backend.app.utils.decorators import (
    role_required,
    get_current_user_info,
    enforce_customer_isolation,
)
from backend.app.utils.errors import (
    NotFoundError,
    BadRequestError,
    ConflictError,
    ValidationError as CustomValidationError,
    success_response,
)
from backend.app.utils.pagination import get_pagination_params, paginated_response

quotations_bp = Blueprint("quotations", __name__)


# ---------------- CUSTOMERS ----------------
@quotations_bp.route("/customers", methods=["GET"])
@role_required("admin", "staff")
def list_customers():
    page, per_page = get_pagination_params()
    query = Customer.query.order_by(Customer.id.asc())

    search = request.args.get("search")
    if search:
        query = query.filter(
            Customer.name.ilike(f"%{search}%") | Customer.email.ilike(f"%{search}%")
        )

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([c.to_dict() for c in items], total, page, per_page)


# ---------------- QUOTATIONS ----------------
@quotations_bp.route("/quotations", methods=["POST"])
@role_required("admin", "staff", "customer")
def create_quotation():
    json_data = request.get_json(silent=True) or {}
    schema = QuotationCreateSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid quotation data",
                    "details": err.messages,
                }
            },
            400,
        )

    auth_id, role, caller_cust_id, _ = get_current_user_info()
    customer_id = data["customer_id"]
    if role == "customer" and caller_cust_id != customer_id:
        return (
            {
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Customers cannot create quotations for other customers.",
                    "details": {},
                }
            },
            403,
        )

    customer = db.session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")

    plan = db.session.get(Plan, data["plan_id"])
    if not plan or not plan.is_active:
        raise NotFoundError(f"Plan with ID {data['plan_id']} not found or inactive.")

    validity_days = data.get("validity_days", 30)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=validity_days)

    quotation_number = f"QT-{uuid.uuid4().hex[:8].upper()}"

    quotation = Quotation(
        quotation_number=quotation_number,
        customer_id=customer.id,
        plan_id=plan.id,
        template_id=data.get("template_id"),
        status="draft",
        validity_days=validity_days,
        expires_at=expires_at,
        total_amount=Decimal("0.00"),
    )
    db.session.add(quotation)
    db.session.flush()

    total_amount = Decimal("0.00")
    total_qty = 0

    for line_data in data["lines"]:
        product = db.session.get(Product, line_data["product_id"])
        if not product or not product.is_active:
            raise NotFoundError(f"Product ID {line_data['product_id']} not found or inactive.")

        variant = None
        if line_data.get("variant_id"):
            variant = Variant.query.filter_by(
                id=line_data["variant_id"], product_id=product.id
            ).first()
            if not variant:
                raise NotFoundError(f"Variant ID {line_data['variant_id']} not found for product.")

        tax = None
        if line_data.get("tax_id"):
            tax = db.session.get(Tax, line_data["tax_id"])

        discount = None
        if line_data.get("discount_id"):
            discount = db.session.get(Discount, line_data["discount_id"])

        quantity = line_data.get("quantity", 1)
        total_qty += quantity

        calc = PricingService.calculate_line(
            product=product,
            quantity=quantity,
            variant=variant,
            discount=discount,
            tax=tax,
            as_of_date=now.date(),
            context="product",
        )

        q_line = QuotationLine(
            quotation_id=quotation.id,
            product_id=product.id,
            variant_id=variant.id if variant else None,
            quantity=quantity,
            tax_id=tax.id if tax else None,
            discount_id=discount.id if discount else None,
            unit_price=calc["unit_price"],
            variant_price=calc["variant_price"],
            discount_amount=calc["discount_amount"],
            tax_amount=calc["tax_amount"],
            line_total=calc["line_total"],
        )
        db.session.add(q_line)
        total_amount += calc["line_total"]

    if total_qty < plan.min_quantity:
        raise BadRequestError(
            f"Plan '{plan.name}' requires a minimum quantity of {plan.min_quantity}. Given: {total_qty}."
        )

    quotation.total_amount = total_amount
    db.session.commit()

    return success_response(quotation.to_dict(), status_code=201, message="Quotation created successfully.")


@quotations_bp.route("/quotations", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_quotations():
    auth_id, role, customer_id, _ = get_current_user_info()
    page, per_page = get_pagination_params()

    query = Quotation.query.order_by(Quotation.id.desc())
    if role == "customer":
        query = query.filter_by(customer_id=customer_id)
    else:
        req_customer_id = request.args.get("customer_id")
        if req_customer_id:
            query = query.filter_by(customer_id=req_customer_id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@quotations_bp.route("/quotations/<int:quotation_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_quotation(quotation_id):
    quotation = db.session.get(Quotation, quotation_id)
    if not quotation:
        raise NotFoundError(f"Quotation with ID {quotation_id} not found.")

    enforce_customer_isolation(quotation.customer_id)
    return success_response(quotation.to_dict())


@quotations_bp.route("/quotations/<int:quotation_id>/confirm", methods=["POST"])
@role_required("admin", "staff", "customer")
def confirm_quotation(quotation_id):
    quotation = db.session.get(Quotation, quotation_id)
    if not quotation:
        raise NotFoundError(f"Quotation with ID {quotation_id} not found.")

    enforce_customer_isolation(quotation.customer_id)

    # Check status
    if quotation.status != "draft":
        raise ConflictError(
            f"Cannot confirm quotation in status '{quotation.status}'."
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    if quotation.expires_at.replace(tzinfo=timezone.utc) < now:
        quotation.status = "expired"
        db.session.commit()
        return (
            {
                "error": {
                    "code": "QUOTATION_EXPIRED",
                    "message": "Quotation has expired and cannot be confirmed.",
                    "details": {},
                }
            },
            409,
        )

    quotation.status = "confirmed"

    # Create subscription
    plan = quotation.plan
    today = date.today()
    next_period_end = add_billing_period(today, plan.billing_period)

    sub_number = f"SUB-{uuid.uuid4().hex[:8].upper()}"
    subscription = Subscription(
        subscription_number=sub_number,
        customer_id=quotation.customer_id,
        plan_id=quotation.plan_id,
        quotation_id=quotation.id,
        status="confirmed",
        start_date=today,
        current_period_start=today,
        current_period_end=next_period_end,
        next_billing_date=today,
    )
    db.session.add(subscription)
    db.session.flush()

    for q_line in quotation.lines:
        sub_line = SubscriptionLine(
            subscription_id=subscription.id,
            product_id=q_line.product_id,
            variant_id=q_line.variant_id,
            quantity=q_line.quantity,
            tax_id=q_line.tax_id,
            discount_id=q_line.discount_id,
            unit_price=q_line.unit_price,
            variant_price=q_line.variant_price,
            discount_amount=q_line.discount_amount,
            tax_amount=q_line.tax_amount,
            line_total=q_line.line_total,
        )
        db.session.add(sub_line)

    db.session.commit()

    resp_data = subscription.to_dict()
    resp_data["subscription_id"] = subscription.id
    return success_response(
        resp_data,
        status_code=201,
        message="Quotation confirmed and subscription created successfully.",
    )


# ---------------- QUOTATION TEMPLATES ----------------
@quotations_bp.route("/quotation-templates", methods=["GET"])
@role_required("admin", "staff")
def list_quotation_templates():
    page, per_page = get_pagination_params()
    query = QuotationTemplate.query.order_by(QuotationTemplate.id.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([t.to_dict() for t in items], total, page, per_page)


@quotations_bp.route("/quotation-templates", methods=["POST"])
@role_required("admin", "staff")
def create_quotation_template():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        raise BadRequestError("Template 'name' is required.")

    template = QuotationTemplate(
        name=name,
        description=data.get("description"),
        validity_days=int(data.get("validity_days", 30)),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(template)
    db.session.commit()
    return success_response(template.to_dict(), status_code=201, message="Quotation template created.")


@quotations_bp.route("/quotation-templates/<int:template_id>", methods=["GET"])
@role_required("admin", "staff")
def get_quotation_template(template_id):
    template = db.session.get(QuotationTemplate, template_id)
    if not template:
        raise NotFoundError(f"Quotation template with ID {template_id} not found.")
    return success_response(template.to_dict())


@quotations_bp.route("/quotation-templates/<int:template_id>", methods=["PATCH"])
@role_required("admin", "staff")
def update_quotation_template(template_id):
    template = db.session.get(QuotationTemplate, template_id)
    if not template:
        raise NotFoundError(f"Quotation template with ID {template_id} not found.")

    data = request.get_json(silent=True) or {}
    if "name" in data:
        template.name = data["name"]
    if "description" in data:
        template.description = data["description"]
    if "validity_days" in data:
        template.validity_days = int(data["validity_days"])
    if "is_active" in data:
        template.is_active = bool(data["is_active"])

    db.session.commit()
    return success_response(template.to_dict(), message="Quotation template updated.")


@quotations_bp.route("/quotation-templates/<int:template_id>", methods=["DELETE"])
@role_required("admin")
def delete_quotation_template(template_id):
    template = db.session.get(QuotationTemplate, template_id)
    if not template:
        raise NotFoundError(f"Quotation template with ID {template_id} not found.")

    template.is_active = False
    db.session.commit()
    return success_response({"message": "Quotation template deactivated."}, status_code=200)
