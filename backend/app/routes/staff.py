from flask import Blueprint, request
from marshmallow import ValidationError

from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.staff import Staff
from backend.app.schemas.auth_schemas import StaffCreateSchema, StaffUpdateSchema
from backend.app.utils.decorators import role_required, get_current_user_info
from backend.app.utils.errors import (
    NotFoundError,
    success_response,
)
from backend.app.utils.pagination import get_pagination_params, paginated_response

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("", methods=["POST"])
@role_required("admin")
def create_staff():
    json_data = request.get_json(silent=True) or {}
    schema = StaffCreateSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid staff data",
                    "details": err.messages,
                }
            },
            400,
        )

    if Auth.query.filter_by(email=data["email"]).first():
        return (
            {
                "error": {
                    "code": "DUPLICATE_EMAIL",
                    "message": "An account with this email already exists.",
                    "details": {"email": ["Email already in use."]},
                }
            },
            400,
        )

    auth = Auth(email=data["email"], role=data.get("role", "staff"), is_active=True)
    auth.set_password(data["password"])
    db.session.add(auth)
    db.session.flush()

    staff = Staff(
        auth_id=auth.id,
        name=data["name"],
        email=data["email"],
        role=data.get("role", "staff"),
        department=data.get("department"),
        is_active=True,
    )
    db.session.add(staff)
    db.session.commit()

    staff_dict = staff.to_dict()
    return success_response(staff_dict, status_code=201, message="Staff created successfully.")


@staff_bp.route("", methods=["GET"])
@role_required("admin")
def list_staff():
    page, per_page = get_pagination_params()
    query = Staff.query.order_by(Staff.id.asc())

    department = request.args.get("department")
    if department:
        query = query.filter_by(department=department)

    is_active = request.args.get("is_active")
    if is_active is not None:
        active_bool = is_active.lower() in ("true", "1")
        query = query.filter_by(is_active=active_bool)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([item.to_dict() for item in items], total, page, per_page)


@staff_bp.route("/<int:staff_id>", methods=["PATCH"])
@role_required("admin")
def update_staff(staff_id):
    staff = db.session.get(Staff, staff_id)
    if not staff:
        raise NotFoundError(f"Staff member with ID {staff_id} not found.")

    json_data = request.get_json(silent=True) or {}
    schema = StaffUpdateSchema()
    try:
        data = schema.load(json_data)
    except ValidationError as err:
        return (
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid staff update data",
                    "details": err.messages,
                }
            },
            400,
        )

    if "name" in data:
        staff.name = data["name"]
    if "department" in data:
        staff.department = data["department"]
    if "is_active" in data:
        staff.is_active = data["is_active"]
        if staff.auth:
            staff.auth.is_active = data["is_active"]

    db.session.commit()
    return success_response(staff.to_dict(), status_code=200, message="Staff updated successfully.")
