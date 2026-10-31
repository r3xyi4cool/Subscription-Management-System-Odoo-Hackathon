import json
from datetime import datetime, timezone
from backend.app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(
        db.Integer, db.ForeignKey("auth.id"), nullable=True, index=True
    )
    entity_type = db.Column(
        db.String(50), nullable=False, index=True
    )  # invoice, payment, refund, product, discount, tax, subscription, customer
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    action = db.Column(
        db.String(50), nullable=False
    )  # create, update, delete, confirm, pay, refund, cancel
    old_values = db.Column(db.Text, nullable=True)  # JSON formatted
    new_values = db.Column(db.Text, nullable=True)  # JSON formatted
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    auth = db.relationship("Auth")

    def to_dict(self):
        user_name = None
        user_email = None
        if self.auth:
            user_email = self.auth.email
            if self.auth.staff_profile:
                user_name = self.auth.staff_profile.name
            elif self.auth.customer_profile:
                user_name = self.auth.customer_profile.name

        details = None
        if self.new_values:
            try:
                details = json.loads(self.new_values)
            except Exception:
                details = {"raw": self.new_values}

        return {
            "id": str(self.id),
            "auth_id": self.auth_id,
            "user_id": str(self.auth_id) if self.auth_id else None,
            "user_name": user_name,
            "user_email": user_email,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "action": self.action,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "details": details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.timestamp.isoformat() if self.timestamp else None,
        }
