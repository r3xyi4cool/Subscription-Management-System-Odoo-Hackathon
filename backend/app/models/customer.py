from datetime import datetime, timezone
from backend.app.extensions import db


class Customer(db.Model):
    __tablename__ = "customer"

    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(
        db.Integer, db.ForeignKey("auth.id"), unique=True, nullable=True, index=True
    )
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    billing_address = db.Column(db.String(500), nullable=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    auth = db.relationship("Auth", back_populates="customer_profile")
    quotations = db.relationship("Quotation", back_populates="customer", lazy="dynamic")
    subscriptions = db.relationship(
        "Subscription", back_populates="customer", lazy="dynamic"
    )
    invoices = db.relationship("Invoice", back_populates="customer", lazy="dynamic")
    payments = db.relationship("Payment", back_populates="customer", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "auth_id": self.auth_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "billing_address": self.billing_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

