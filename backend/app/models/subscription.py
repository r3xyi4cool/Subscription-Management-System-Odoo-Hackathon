from datetime import datetime, timezone
from decimal import Decimal
from backend.app.extensions import db


class Subscription(db.Model):
    __tablename__ = "subscription"

    id = db.Column(db.Integer, primary_key=True)
    subscription_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True
    )
    plan_id = db.Column(
        db.Integer, db.ForeignKey("plan.id"), nullable=False, index=True
    )
    quotation_id = db.Column(
        db.Integer, db.ForeignKey("quotation.id"), nullable=True, index=True
    )
    status = db.Column(
        db.String(50), default="confirmed", nullable=False, index=True
    )  # draft, quotation, confirmed, active, paused, closed
    start_date = db.Column(db.Date, nullable=False)
    current_period_start = db.Column(db.Date, nullable=False)
    current_period_end = db.Column(db.Date, nullable=False)
    next_billing_date = db.Column(db.Date, nullable=False, index=True)

    cancelled_at = db.Column(db.DateTime, nullable=True)
    paused_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    customer = db.relationship("Customer", back_populates="subscriptions")
    plan = db.relationship("Plan", back_populates="subscriptions")
    quotation = db.relationship("Quotation")
    lines = db.relationship(
        "SubscriptionLine",
        back_populates="subscription",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    invoices = db.relationship(
        "Invoice", back_populates="subscription", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "subscription_number": self.subscription_number,
            "customer_id": self.customer_id,
            "plan_id": self.plan_id,
            "quotation_id": self.quotation_id,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "current_period_start": self.current_period_start.isoformat()
            if self.current_period_start
            else None,
            "current_period_end": self.current_period_end.isoformat()
            if self.current_period_end
            else None,
            "next_billing_date": self.next_billing_date.isoformat()
            if self.next_billing_date
            else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "lines": [line.to_dict() for line in self.lines] if self.lines else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SubscriptionLine(db.Model):
    __tablename__ = "subscription_line"

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(
        db.Integer, db.ForeignKey("subscription.id"), nullable=False, index=True
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id"), nullable=False, index=True
    )
    variant_id = db.Column(
        db.Integer, db.ForeignKey("variant.id"), nullable=True, index=True
    )
    quantity = db.Column(db.Integer, default=1, nullable=False)
    tax_id = db.Column(
        db.Integer, db.ForeignKey("tax.id"), nullable=True, index=True
    )
    discount_id = db.Column(
        db.Integer, db.ForeignKey("discount.id"), nullable=True, index=True
    )

    unit_price = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    variant_price = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    discount_amount = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    tax_amount = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    line_total = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subscription = db.relationship("Subscription", back_populates="lines")
    product = db.relationship("Product")
    variant = db.relationship("Variant")
    tax = db.relationship("Tax")
    discount = db.relationship("Discount")

    def to_dict(self):
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "product_id": self.product_id,
            "variant_id": self.variant_id,
            "quantity": self.quantity,
            "tax_id": self.tax_id,
            "discount_id": self.discount_id,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0.0,
            "variant_price": float(self.variant_price) if self.variant_price is not None else 0.0,
            "discount_amount": float(self.discount_amount) if self.discount_amount is not None else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount is not None else 0.0,
            "line_total": float(self.line_total) if self.line_total is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

