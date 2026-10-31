import re
from marshmallow import Schema, fields, validate, validates, ValidationError


def validate_password_strength(password: str):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValidationError(
            "Password must contain at least one special character (e.g. !@#$%^&*)."
        )


class SignupSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate_password_strength)
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    phone = fields.String(load_default=None)
    company = fields.String(load_default=None)
    company_name = fields.String(load_default=None)
    billing_address = fields.String(load_default=None)


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    token = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate_password_strength)


class StaffCreateSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate_password_strength)
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    department = fields.String(load_default=None)
    role = fields.String(
        load_default="staff", validate=validate.OneOf(["staff", "admin"])
    )


class StaffUpdateSchema(Schema):
    name = fields.String()
    department = fields.String()
    is_active = fields.Boolean()


class ChangePasswordSchema(Schema):
    current_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate_password_strength)


