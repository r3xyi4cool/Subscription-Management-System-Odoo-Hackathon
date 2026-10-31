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
    )  # invoice, payment, refund, product, discount, tax, subscription
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
        return {
            "id": self.id,
            "auth_id": self.auth_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
