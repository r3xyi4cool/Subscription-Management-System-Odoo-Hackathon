import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
)
from marshmallow import ValidationError

from backend.app.extensions import db
from backend.app.models.auth import Auth, TokenBlocklist
from backend.app.models.customer import Customer
from backend.app.schemas.auth_schemas import (
    SignupSchema,
    LoginSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema,
)
from backend.app.services.mail_service import MailService
from backend.app.utils.errors import (
    BadRequestError,
    UnauthorizedError,
    ConflictError,
    success_response,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def user_to_dict(auth):
    name = ""
    phone = None
    company_name = None
    customer_id = None
    staff_id = None
    billing_address = None
    if auth.customer_profile:
        name = auth.customer_profile.name or ""
        phone = auth.customer_profile.phone
        company_name = auth.customer_profile.company
        billing_address = auth.customer_profile.billing_address
        customer_id = auth.customer_profile.id
    elif auth.staff_profile:
        name = auth.staff_profile.name or ""
        phone = getattr(auth.staff_profile, "phone", None)
        staff_id = auth.staff_profile.id

    return {
        "id": str(auth.id),
        "auth_id": auth.id,
        "email": auth.email,
        "role": auth.role,
        "name": name,
        "phone": phone,
        "company_name": company_name,
        "billing_address": billing_address,
        "customer_id": customer_id,
        "staff_id": staff_id,
        "is_active": auth.is_active,
        "created_at": auth.created_at.isoformat() if getattr(auth, "created_at", None) else None,
        "updated_at": auth.updated_at.isoformat() if getattr(auth, "updated_at", None) else None,
    }


@auth_bp.route("/signup", methods=["POST"])
def signup():
    json_data = request.get_json(silent=True) or {}
    schema = SignupSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid signup data",
                    "details": err.messages,
                }
            },
            400,
        )

    # Check duplicate email
    existing_auth = Auth.query.filter_by(email=data["email"]).first()
    if existing_auth:
        return (
            {
                "error": {
                    "code": "DUPLICATE_EMAIL",
                    "message": "An account with this email already exists.",
                    "details": {"email": ["Email already registered"]},
                }
            },
            400,
        )

    auth = Auth(email=data["email"], role="customer", is_active=True)
    auth.set_password(data["password"])
    db.session.add(auth)
    db.session.flush()

    customer = Customer(
        auth_id=auth.id,
        name=data["name"],
        email=data["email"],
        phone=data.get("phone"),
        company=data.get("company_name") or data.get("company"),
        billing_address=data.get("billing_address"),
    )
    db.session.add(customer)
    db.session.commit()

    customer_id = customer.id
    token = create_access_token(
        identity=str(auth.id),
        additional_claims={
            "role": auth.role,
            "email": auth.email,
            "customer_id": customer_id,
            "staff_id": None,
        },
    )

    user_dict = user_to_dict(auth)
    response_data = {
        "access_token": token,
        "session_token": token,
        "token_type": "Bearer",
        "id": customer.id,
        "customer_id": customer.id,
        "auth_id": auth.id,
        "email": auth.email,
        "name": customer.name,
        "role": auth.role,
        "user": user_dict,
    }
    return success_response(response_data, status_code=201, message="Account created successfully.")


@auth_bp.route("/login", methods=["POST"])
def login():
    json_data = request.get_json(silent=True) or {}
    schema = LoginSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid login data",
                    "details": err.messages,
                }
            },
            400,
        )

    auth = Auth.query.filter_by(email=data["email"]).first()
    if not auth or not auth.check_password(data["password"]):
        return (
            {
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": {},
                }
            },
            401,
        )

    if not auth.is_active:
        return (
            {
                "error": {
                    "code": "ACCOUNT_DEACTIVATED",
                    "message": "Account has been deactivated. Please contact support.",
                    "details": {},
                }
            },
            401,
        )

    customer_id = auth.customer_profile.id if auth.customer_profile else None
    staff_id = auth.staff_profile.id if auth.staff_profile else None

    token = create_access_token(
        identity=str(auth.id),
        additional_claims={
            "role": auth.role,
            "email": auth.email,
            "customer_id": customer_id,
            "staff_id": staff_id,
        },
    )

    user_dict = user_to_dict(auth)
    resp_payload = {
        "access_token": token,
        "session_token": token,
        "token_type": "Bearer",
        "id": auth.id,
        "customer_id": customer_id,
        "staff_id": staff_id,
        "user": user_dict,
    }
    return success_response(resp_payload, status_code=200, message="Login successful.")


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    identity = get_jwt_identity()
    auth = Auth.query.get(int(identity))
    if not auth:
        return (
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "User not found",
                    "details": {},
                }
            },
            404,
        )
    return success_response(user_to_dict(auth), status_code=200)


@auth_bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_me():
    identity = get_jwt_identity()
    auth = Auth.query.get(int(identity))
    if not auth:
        return (
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "User not found",
                    "details": {},
                }
            },
            404,
        )

    data = request.get_json(silent=True) or {}
    if auth.role == "customer" and auth.customer_profile:
        if "name" in data:
            auth.customer_profile.name = data["name"]
        if "phone" in data:
            auth.customer_profile.phone = data["phone"]
        if "company_name" in data:
            auth.customer_profile.company = data["company_name"]
        if "company" in data:
            auth.customer_profile.company = data["company"]
        if "billing_address" in data:
            auth.customer_profile.billing_address = data["billing_address"]
    elif auth.role in ("admin", "staff") and auth.staff_profile:
        if "name" in data:
            auth.staff_profile.name = data["name"]
        if "phone" in data and hasattr(auth.staff_profile, "phone"):
            auth.staff_profile.phone = data["phone"]

    db.session.commit()
    return success_response(user_to_dict(auth), status_code=200)


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    blocklist_entry = TokenBlocklist(jti=jti)
    db.session.add(blocklist_entry)
    db.session.commit()
    return success_response({"message": "Successfully logged out."}, status_code=200)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    json_data = request.get_json(silent=True) or {}
    schema = ForgotPasswordSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid email format",
                    "details": err.messages,
                }
            },
            400,
        )

    auth = Auth.query.filter_by(email=data["email"]).first()
    reset_token = None
    if auth and auth.is_active:
        reset_token = secrets.token_urlsafe(32)
        auth.reset_token = reset_token
        auth.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        auth.reset_token_used = False
        db.session.commit()

        MailService.send_password_reset_email(auth.email, reset_token)

    resp_data = {
        "message": "If an active account exists with that email, a password reset link has been sent.",
    }
    if current_app.config.get("TESTING") and reset_token:
        resp_data["reset_token"] = reset_token

    return success_response(resp_data, status_code=200)


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    json_data = request.get_json(silent=True) or {}
    schema = ResetPasswordSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Validation failed",
                    "details": err.messages,
                }
            },
            400,
        )

    token = data["token"]
    auth = Auth.query.filter_by(reset_token=token).first()

    now = datetime.now(timezone.utc)
    if (
        not auth
        or auth.reset_token_used
        or not auth.reset_token_expires_at
        or auth.reset_token_expires_at.replace(tzinfo=timezone.utc) < now
    ):
        return (
            {
                "error": {
                    "code": "INVALID_RESET_TOKEN",
                    "message": "Password reset token is invalid, expired, or has already been used.",
                    "details": {},
                }
            },
            400,
        )

    auth.set_password(data["new_password"])
    auth.reset_token_used = True
    auth.reset_token = None
    auth.reset_token_expires_at = None
    db.session.commit()

    return success_response(
        {"message": "Password has been successfully reset. You may now log in."},
        status_code=200,
    )
