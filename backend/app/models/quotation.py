from datetime import datetime, timezone
from decimal import Decimal
from backend.app.extensions import db


class QuotationTemplate(db.Model):
    __tablename__ = "quotation_template"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    validity_days = db.Column(db.Integer, default=30, nullable=False)
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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "validity_days": self.validity_days,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Quotation(db.Model):
    __tablename__ = "quotation"

    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True
    )
    plan_id = db.Column(
        db.Integer, db.ForeignKey("plan.id"), nullable=False, index=True
    )
    template_id = db.Column(
        db.Integer, db.ForeignKey("quotation_template.id"), nullable=True
    )
    status = db.Column(
        db.String(50), default="draft", nullable=False, index=True
    )  # draft, confirmed, expired, cancelled
    validity_days = db.Column(db.Integer, default=30, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    total_amount = db.Column(
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

    customer = db.relationship("Customer", back_populates="quotations")
    plan = db.relationship("Plan")
    lines = db.relationship(
        "QuotationLine",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "quotation_number": self.quotation_number,
            "customer_id": self.customer_id,
            "plan_id": self.plan_id,
            "template_id": self.template_id,
            "status": self.status,
            "validity_days": self.validity_days,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "total_amount": float(self.total_amount) if self.total_amount is not None else 0.0,
            "lines": [line.to_dict() for line in self.lines] if self.lines else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class QuotationLine(db.Model):
    __tablename__ = "quotation_line"

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(
        db.Integer, db.ForeignKey("quotation.id"), nullable=False, index=True
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

    quotation = db.relationship("Quotation", back_populates="lines")
    product = db.relationship("Product")
    variant = db.relationship("Variant")
    tax = db.relationship("Tax")
    discount = db.relationship("Discount")

    def to_dict(self):
        return {
            "id": self.id,
            "quotation_id": self.quotation_id,
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

