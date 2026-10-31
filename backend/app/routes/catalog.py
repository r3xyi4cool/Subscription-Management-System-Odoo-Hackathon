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
from backend.app.utils.errors import NotFoundError, success_response, BadRequestError
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


@catalog_bp.route("/taxes/<int:tax_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_tax(tax_id):
    tax = db.session.get(Tax, tax_id)
    if not tax:
        raise NotFoundError(f"Tax with ID {tax_id} not found.")
    return success_response(tax.to_dict())


@catalog_bp.route("/taxes/<int:tax_id>", methods=["PATCH"])
@role_required("admin")
def update_tax(tax_id):
    tax = db.session.get(Tax, tax_id)
    if not tax:
        raise NotFoundError(f"Tax with ID {tax_id} not found.")

    old_values = tax.to_dict()
    data = request.get_json(silent=True) or {}
    if "name" in data:
        tax.name = data["name"]
    if "rate" in data:
        tax.rate = Decimal(str(data["rate"]))
    if "is_active" in data:
        tax.is_active = bool(data["is_active"])

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="tax",
        entity_id=tax.id,
        action="update",
        old_values=old_values,
        new_values=tax.to_dict(),
    )
    db.session.commit()
    return success_response(tax.to_dict(), message="Tax updated successfully.")


@catalog_bp.route("/taxes/<int:tax_id>", methods=["DELETE"])
@role_required("admin")
def delete_tax(tax_id):
    tax = db.session.get(Tax, tax_id)
    if not tax:
        raise NotFoundError(f"Tax with ID {tax_id} not found.")

    tax.is_active = False
    db.session.commit()
    return success_response({"message": "Tax deactivated successfully."}, status_code=200)


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
                    "message": "A discount with this code already exists.",
                    "details": {},
                }
            },
            400,
        )

    discount_type = data["discount_type"]
    if discount_type == "percent":
        discount_type = "percentage"

    discount = Discount(
        code=data["code"],
        description=data.get("description"),
        discount_type=discount_type,
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
@role_required("admin", "staff", "customer")
def list_discounts():
    page, per_page = get_pagination_params()
    query = Discount.query.order_by(Discount.id.asc())

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter_by(is_active=is_active.lower() in ("true", "1"))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@catalog_bp.route("/discounts/<int:discount_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_discount(discount_id):
    discount = db.session.get(Discount, discount_id)
    if not discount:
        raise NotFoundError(f"Discount with ID {discount_id} not found.")
    return success_response(discount.to_dict())


@catalog_bp.route("/discounts/<int:discount_id>", methods=["PATCH"])
@role_required("admin")
def update_discount(discount_id):
    discount = db.session.get(Discount, discount_id)
    if not discount:
        raise NotFoundError(f"Discount with ID {discount_id} not found.")

    old_values = discount.to_dict()
    data = request.get_json(silent=True) or {}

    if "description" in data:
        discount.description = data["description"]
    if "value" in data:
        discount.value = Decimal(str(data["value"]))
    if "min_quantity" in data:
        discount.min_quantity = int(data["min_quantity"])
    if "min_purchase" in data:
        discount.min_purchase = Decimal(str(data["min_purchase"]))
    if "start_date" in data:
        discount.start_date = data["start_date"]
    if "end_date" in data:
        discount.end_date = data["end_date"]
    if "usage_limit" in data:
        discount.usage_limit = int(data["usage_limit"]) if data["usage_limit"] else None
    if "is_active" in data:
        discount.is_active = bool(data["is_active"])

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="discount",
        entity_id=discount.id,
        action="update",
        old_values=old_values,
        new_values=discount.to_dict(),
    )
    db.session.commit()
    return success_response(discount.to_dict(), message="Discount updated successfully.")


@catalog_bp.route("/discounts/<int:discount_id>", methods=["DELETE"])
@role_required("admin")
def delete_discount(discount_id):
    discount = db.session.get(Discount, discount_id)
    if not discount:
        raise NotFoundError(f"Discount with ID {discount_id} not found.")

    discount.is_active = False
    db.session.commit()
    return success_response({"message": "Discount deactivated successfully."}, status_code=200)


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

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@catalog_bp.route("/products/<int:product_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        raise NotFoundError(f"Product with ID {product_id} not found.")
    return success_response(product.to_dict())


@catalog_bp.route("/products/<int:product_id>", methods=["PATCH"])
@role_required("admin")
def update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        raise NotFoundError(f"Product with ID {product_id} not found.")

    old_values = product.to_dict()
    data = request.get_json(silent=True) or {}
    if "name" in data:
        product.name = data["name"]
    if "description" in data:
        product.description = data["description"]
    if "sales_price" in data:
        product.sales_price = Decimal(str(data["sales_price"]))
    if "cost_price" in data:
        product.cost_price = Decimal(str(data["cost_price"]))
    if "is_active" in data:
        product.is_active = bool(data["is_active"])

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="product",
        entity_id=product.id,
        action="update",
        old_values=old_values,
        new_values=product.to_dict(),
    )
    db.session.commit()
    return success_response(product.to_dict(), message="Product updated successfully.")


@catalog_bp.route("/products/<int:product_id>", methods=["DELETE"])
@role_required("admin")
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        raise NotFoundError(f"Product with ID {product_id} not found.")

    product.is_active = False
    db.session.commit()
    return success_response({"message": "Product deactivated successfully."}, status_code=200)


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
        product_id=product.id,
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


@catalog_bp.route("/products/<int:product_id>/variants", methods=["GET"])
@role_required("admin", "staff", "customer")
def list_variants(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        raise NotFoundError(f"Product with ID {product_id} not found.")
    return success_response([v.to_dict() for v in product.variants])


@catalog_bp.route("/products/<int:product_id>/variants/<int:variant_id>", methods=["PATCH"])
@role_required("admin")
def update_variant(product_id, variant_id):
    variant = db.session.get(Variant, variant_id)
    if not variant or variant.product_id != product_id:
        raise NotFoundError(f"Variant with ID {variant_id} not found for product {product_id}.")

    data = request.get_json(silent=True) or {}
    if "name" in data:
        variant.name = data["name"]
    if "extra_price" in data:
        variant.extra_price = Decimal(str(data["extra_price"]))
    if "is_active" in data:
        variant.is_active = bool(data["is_active"])

    db.session.commit()
    return success_response(variant.to_dict(), message="Variant updated successfully.")


@catalog_bp.route("/products/<int:product_id>/variants/<int:variant_id>", methods=["DELETE"])
@role_required("admin")
def delete_variant(product_id, variant_id):
    variant = db.session.get(Variant, variant_id)
    if not variant or variant.product_id != product_id:
        raise NotFoundError(f"Variant with ID {variant_id} not found for product {product_id}.")

    variant.is_active = False
    db.session.commit()
    return success_response({"message": "Variant deactivated successfully."}, status_code=200)


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


@catalog_bp.route("/plans/<int:plan_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_plan(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan:
        raise NotFoundError(f"Plan with ID {plan_id} not found.")
    return success_response(plan.to_dict())


@catalog_bp.route("/plans/<int:plan_id>", methods=["PATCH"])
@role_required("admin")
def update_plan(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan:
        raise NotFoundError(f"Plan with ID {plan_id} not found.")

    old_values = plan.to_dict()
    data = request.get_json(silent=True) or {}
    if "name" in data:
        plan.name = data["name"]
    if "description" in data:
        plan.description = data["description"]
    if "billing_period" in data:
        plan.billing_period = data["billing_period"]
    if "min_quantity" in data:
        plan.min_quantity = int(data["min_quantity"])
    if "allow_pause" in data:
        plan.allow_pause = bool(data["allow_pause"])
    if "allow_close" in data:
        plan.allow_close = bool(data["allow_close"])
    if "allow_early_close" in data:
        plan.allow_close = bool(data["allow_early_close"])
    if "allow_renew" in data:
        plan.allow_renew = bool(data["allow_renew"])
    if "allow_renewal" in data:
        plan.allow_renew = bool(data["allow_renewal"])
    if "is_active" in data:
        plan.is_active = bool(data["is_active"])

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="plan",
        entity_id=plan.id,
        action="update",
        old_values=old_values,
        new_values=plan.to_dict(),
    )
    db.session.commit()
    return success_response(plan.to_dict(), message="Plan updated successfully.")


@catalog_bp.route("/plans/<int:plan_id>", methods=["DELETE"])
@role_required("admin")
def delete_plan(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan:
        raise NotFoundError(f"Plan with ID {plan_id} not found.")

    plan.is_active = False
    db.session.commit()
    return success_response({"message": "Plan deactivated successfully."}, status_code=200)
