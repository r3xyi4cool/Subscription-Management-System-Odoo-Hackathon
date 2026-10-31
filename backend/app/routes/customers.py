import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request
from marshmallow import ValidationError

from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.customer import Customer
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

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")


def customer_to_detail(c):
    data = c.to_dict()
    active_subs = c.subscriptions.filter_by(status="active").count()
    total_invoiced = sum(float(inv.total) for inv in c.invoices)
    balance_due = sum(
        float(inv.total - inv.amount_paid)
        for inv in c.invoices
        if inv.status in ("draft", "confirmed")
    )
    data["active_subscriptions_count"] = active_subs
    data["total_invoiced"] = total_invoiced
    data["total_invoiced_paise"] = int(round(total_invoiced * 100))
    data["outstanding_balance"] = balance_due
    data["outstanding_balance_paise"] = int(round(balance_due * 100))
    data["is_active"] = c.auth.is_active if c.auth else True
    return data


@customers_bp.route("", methods=["GET"])
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
    return paginated_response([customer_to_detail(c) for c in items], total, page, per_page)


@customers_bp.route("/<int:customer_id>", methods=["GET"])
@role_required("admin", "staff", "customer")
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")

    enforce_customer_isolation(customer.id)
    return success_response(customer_to_detail(customer))


@customers_bp.route("", methods=["POST"])
@role_required("admin", "staff")
def create_customer():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    name = data.get("name")
    if not email or not name:
        raise BadRequestError("Customer 'name' and 'email' are required.")

    existing_auth = Auth.query.filter_by(email=email).first()
    if existing_auth:
        raise ConflictError(f"An account with email '{email}' already exists.")

    temp_password = data.get("password") or secrets.token_urlsafe(16) + "A1!"
    auth = Auth(email=email, role="customer", is_active=data.get("is_active", True))
    auth.set_password(temp_password)
    db.session.add(auth)
    db.session.flush()

    customer = Customer(
        auth_id=auth.id,
        name=name,
        email=email,
        phone=data.get("phone"),
        company=data.get("company_name") or data.get("company"),
        billing_address=data.get("billing_address"),
    )
    db.session.add(customer)
    db.session.commit()

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="customer",
        entity_id=customer.id,
        action="create",
        new_values=customer.to_dict(),
    )
    db.session.commit()

    return success_response(customer_to_detail(customer), status_code=201, message="Customer created successfully.")


@customers_bp.route("/<int:customer_id>", methods=["PATCH"])
@role_required("admin", "staff")
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")

    old_values = customer.to_dict()
    data = request.get_json(silent=True) or {}

    if "name" in data:
        customer.name = data["name"]
    if "phone" in data:
        customer.phone = data["phone"]
    if "company_name" in data or "company" in data:
        customer.company = data.get("company_name") or data.get("company")
    if "billing_address" in data:
        customer.billing_address = data["billing_address"]
    if "is_active" in data and customer.auth:
        customer.auth.is_active = bool(data["is_active"])

    auth_id, _, _, _ = get_current_user_info()
    log_audit(
        auth_id=auth_id,
        entity_type="customer",
        entity_id=customer.id,
        action="update",
        old_values=old_values,
        new_values=customer.to_dict(),
    )
    db.session.commit()

    return success_response(customer_to_detail(customer), message="Customer updated successfully.")


@customers_bp.route("/<int:customer_id>/send-reset-link", methods=["POST"])
@role_required("admin", "staff")
def send_customer_reset_link(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")

    auth = customer.auth
    if not auth:
        raise BadRequestError("Customer does not have an active authentication account.")

    reset_token = secrets.token_urlsafe(32)
    auth.reset_token = reset_token
    auth.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=60)
    auth.reset_token_used = False
    db.session.commit()

    MailService.send_password_reset_email(auth.email, reset_token)

    return success_response(
        {"message": f"Password reset link sent to {auth.email}."},
        status_code=200,
    )
