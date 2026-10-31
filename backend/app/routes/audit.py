from flask import Blueprint, request

from backend.app.models.audit import AuditLog
from backend.app.utils.decorators import role_required
from backend.app.utils.pagination import get_pagination_params, paginated_response

audit_bp = Blueprint("audit", __name__, url_prefix="/audit-logs")


@audit_bp.route("", methods=["GET"])
@role_required("admin")
def list_audit_logs():
    page, per_page = get_pagination_params()
    query = AuditLog.query.order_by(AuditLog.id.desc())

    entity_type = request.args.get("entity_type")
    if entity_type:
        query = query.filter_by(entity_type=entity_type)

    action = request.args.get("action")
    if action:
        query = query.filter_by(action=action)

    auth_id = request.args.get("auth_id") or request.args.get("user_id")
    if auth_id:
        query = query.filter_by(auth_id=int(auth_id))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return paginated_response([log.to_dict() for log in items], total, page, per_page)

