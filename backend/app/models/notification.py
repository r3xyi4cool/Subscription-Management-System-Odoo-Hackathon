from datetime import datetime, timezone
from backend.app.extensions import db


class Notification(db.Model):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("auth.id"), nullable=True, index=True
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customer.id"), nullable=True, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(
        db.String(50), nullable=False, default="system"
    )  # invoice, payment, reminder, system
    link_url = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    dedupe_key = db.Column(db.String(255), unique=True, nullable=True, index=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        db.Index("idx_notification_user_read_created", "user_id", "is_read", "created_at"),
        db.Index("idx_notification_customer_read_created", "customer_id", "is_read", "created_at"),
    )

    user = db.relationship("Auth", foreign_keys=[user_id])
    customer = db.relationship("Customer", foreign_keys=[customer_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "link_url": self.link_url,
            "is_read": self.is_read,
            "dedupe_key": self.dedupe_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

