from datetime import datetime, timezone
from backend.app.extensions import db


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(
        db.Integer, db.ForeignKey("auth.id"), unique=True, nullable=True, index=True
    )
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    role = db.Column(db.String(50), nullable=False, default="staff")
    department = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    auth = db.relationship("Auth", back_populates="staff_profile")

    def to_dict(self):
        return {
            "id": self.id,
            "auth_id": self.auth_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "department": self.department,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

