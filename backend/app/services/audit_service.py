import json
from datetime import datetime, timezone
from backend.app.extensions import db
from backend.app.models.audit import AuditLog


def log_audit(auth_id, entity_type, entity_id, action, old_values=None, new_values=None):
    try:
        old_json = json.dumps(old_values, default=str) if old_values is not None else None
        new_json = json.dumps(new_values, default=str) if new_values is not None else None

        entry = AuditLog(
            auth_id=auth_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=old_json,
            new_values=new_json,
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add(entry)
        # Note: commit is left to the caller's transaction
    except Exception as e:
        # Avoid breaking the main flow on audit log failures
        pass

