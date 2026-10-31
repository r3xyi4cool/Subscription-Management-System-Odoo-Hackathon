from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.utils.errors import UnauthorizedError, ForbiddenError


def role_required(*roles):
    """
    Decorator that checks JWT authenticity, user active status,
    and role membership.
    Example:
        @role_required('admin')
        @role_required('admin', 'staff')
        @role_required()  # Any authenticated role
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")

            user_id = get_jwt_identity()
            if not user_id:
                raise UnauthorizedError("Invalid token identity.")

            auth = db.session.get(Auth, int(user_id))
            if not auth or not auth.is_active:
                raise UnauthorizedError("User is inactive or deleted.")

            if roles and user_role not in roles:
                raise ForbiddenError(f"Access denied. Required roles: {list(roles)}")

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_info():
    """
    Returns (auth_id, role, customer_id, staff_id)
    """
    claims = get_jwt()
    auth_id = int(get_jwt_identity())
    role = claims.get("role")
    customer_id = claims.get("customer_id")
    staff_id = claims.get("staff_id")
    return auth_id, role, customer_id, staff_id


def enforce_customer_isolation(resource_customer_id):
    """
    If the caller is a customer, ensures they only access their own resource.
    Admins and staff can access any customer's resource.
    """
    auth_id, role, customer_id, _ = get_current_user_info()
    if role == "customer":
        if customer_id is None or int(customer_id) != int(resource_customer_id):
            raise ForbiddenError("You do not have permission to access this resource.")
