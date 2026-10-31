from decimal import Decimal
from flask import Blueprint, request
from marshmallow import ValidationError

from backend.app.extensions import db
from backend.app.models.catalog import Product, Variant, Plan, Discount, Tax
from backend.app.schemas.catalog_schemas import (
    TaxSchema,
    DiscountSchema,
    ProductSchema,
    VariantSchema,
    PlanSchema,
)
from backend.app.services.audit_service import log_audit
from backend.app.utils.decorators import role_required, get_current_user_info
from backend.app.utils.errors import NotFoundError, success_response
from backend.app.utils.pagination import get_pagination_params, paginated_response

catalog_bp = Blueprint("catalog", __name__)


# ---------------- TAXES ----------------
@catalog_bp.route("/taxes", methods=["POST"])
@role_required("admin")
def create_tax():
    json_data = request.get_json(silent=True) or {}
    schema = TaxSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid tax data",
                    "details": err.messages,
                }
            },
            400,
        )

    tax = Tax(
        name=data["name"],
        rate=Decimal(str(data["rate"])),
        is_active=data.get("is_active", True),
    )
    db.session.add(tax)
    db.session.flush()

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="tax",
        entity_id=tax.id,
        action="create",
        new_values=tax.to_dict(),
    )
    db.session.commit()

    return success_response(tax.to_dict(), status_code=201, message="Tax created successfully.")


@catalog_bp.route("/taxes", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_taxes():
    page, per_page = get_pagination_params()
    query = Tax.query.order_by(Tax.id.asc())

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter_by(is_active=is_active.lower() in ("true", "1"))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


# ---------------- DISCOUNTS ----------------
@catalog_bp.route("/discounts", methods=["POST"])
@role_required("admin")
def create_discount():
    json_data = request.get_json(silent=True) or {}
    schema = DiscountSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid discount data",
                    "details": err.messages,
                }
            },
            400,
        )

    if Discount.query.filter_by(code=data["code"]).first():
        return (
            {
                "error": {
                    "code": "DUPLICATE_CODE",
                    "message": "Discount code already exists.",
                    "details": {"code": ["Code already in use."]},
                }
            },
            400,
        )

    discount = Discount(
        code=data["code"],
        description=data.get("description"),
        discount_type=data["discount_type"],
        value=Decimal(str(data["value"])),
        min_quantity=data.get("min_quantity", 0),
        min_purchase=Decimal(str(data.get("min_purchase", 0.0))),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        usage_limit=data.get("usage_limit"),
        applies_to=data.get("applies_to", "all"),
        is_active=data.get("is_active", True),
    )
    db.session.add(discount)
    db.session.flush()

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="discount",
        entity_id=discount.id,
        action="create",
        new_values=discount.to_dict(),
    )
    db.session.commit()

    return success_response(discount.to_dict(), status_code=201, message="Discount created successfully.")


@catalog_bp.route("/discounts", methods=["GET"])
@role_required("admin", "staff")
def list_discounts():
    page, per_page = get_pagination_params()
    query = Discount.query.order_by(Discount.id.asc())

    applies_to = request.args.get("applies_to")
    if applies_to:
        query = query.filter_by(applies_to=applies_to)

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter_by(is_active=is_active.lower() in ("true", "1"))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


# ---------------- PRODUCTS ----------------
@catalog_bp.route("/products", methods=["POST"])
@role_required("admin")
def create_product():
    json_data = request.get_json(silent=True) or {}
    schema = ProductSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid product data",
                    "details": err.messages,
                }
            },
            400,
        )

    product = Product(
        name=data["name"],
        description=data.get("description"),
        sales_price=Decimal(str(data["sales_price"])),
        cost_price=Decimal(str(data.get("cost_price", 0.0))),
        is_active=data.get("is_active", True),
    )
    db.session.add(product)
    db.session.flush()

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="product",
        entity_id=product.id,
        action="create",
        new_values=product.to_dict(),
    )
    db.session.commit()

    return success_response(product.to_dict(), status_code=201, message="Product created successfully.")


@catalog_bp.route("/products", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_products():
    page, per_page = get_pagination_params()
    query = Product.query.order_by(Product.id.asc())

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter_by(is_active=is_active.lower() in ("true", "1"))

    search = request.args.get("search")
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


# ---------------- VARIANTS ----------------
@catalog_bp.route("/products/<int:product_id>/variants", methods=["POST"])
@role_required("admin")
def create_variant(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        raise NotFoundError(f"Product with ID {product_id} not found.")

    json_data = request.get_json(silent=True) or {}
    schema = VariantSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid variant data",
                    "details": err.messages,
                }
            },
            400,
        )

    variant = Variant(
        product_id=product_id,
        name=data["name"],
        extra_price=Decimal(str(data["extra_price"])),
        is_active=data.get("is_active", True),
    )
    db.session.add(variant)
    db.session.flush()

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="variant",
        entity_id=variant.id,
        action="create",
        new_values=variant.to_dict(),
    )
    db.session.commit()

    return success_response(variant.to_dict(), status_code=201, message="Variant created successfully.")


# ---------------- PLANS ----------------
@catalog_bp.route("/plans", methods=["POST"])
@role_required("admin")
def create_plan():
    json_data = request.get_json(silent=True) or {}
    schema = PlanSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid plan data",
                    "details": err.messages,
                }
            },
            400,
        )

    plan = Plan(
        name=data["name"],
        description=data.get("description"),
        billing_period=data["billing_period"],
        min_quantity=data.get("min_quantity", 1),
        start_date=data["start_date"],
        end_date=data.get("end_date"),
        allow_pause=data.get("allow_pause", True),
        allow_close=data.get("allow_close", True),
        allow_renew=data.get("allow_renew", True),
        is_active=data.get("is_active", True),
    )
    db.session.add(plan)
    db.session.flush()

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="plan",
        entity_id=plan.id,
        action="create",
        new_values=plan.to_dict(),
    )
    db.session.commit()

    return success_response(plan.to_dict(), status_code=201, message="Plan created successfully.")


@catalog_bp.route("/plans", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_plans():
    page, per_page = get_pagination_params()
    query = Plan.query.order_by(Plan.id.asc())

    billing_period = request.args.get("billing_period")
    if billing_period:
        query = query.filter_by(billing_period=billing_period)

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter_by(is_active=is_active.lower() in ("true", "1"))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)
