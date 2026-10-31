from datetime import datetime, timezone
from decimal import Decimal
from backend.app.extensions import db


class Invoice(db.Model):
    __tablename__ = "invoice"
    __table_args__ = (
        db.UniqueConstraint(
            "subscription_id", "billing_period_start", name="uq_invoice_sub_period"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    subscription_id = db.Column(
        db.Integer, db.ForeignKey("subscription.id"), nullable=False, index=True
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True
    )
    status = db.Column(
        db.String(50), default="draft", nullable=False, index=True
    )  # draft, confirmed, paid, cancelled
    issue_date = db.Column(db.Date, nullable=False, index=True)
    due_date = db.Column(db.Date, nullable=False, index=True)
    billing_period_start = db.Column(db.Date, nullable=False)
    billing_period_end = db.Column(db.Date, nullable=False)

    subtotal = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    tax_amount = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    discount_amount = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total = db.Column(
        db.Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    amount_paid = db.Column(
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

    subscription = db.relationship("Subscription", back_populates="invoices")
    customer = db.relationship("Customer", back_populates="invoices")
    lines = db.relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    payments = db.relationship("Payment", back_populates="invoice", lazy="dynamic")
    refunds = db.relationship("Refund", back_populates="invoice", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "subscription_id": self.subscription_id,
            "customer_id": self.customer_id,
            "status": self.status,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "billing_period_start": self.billing_period_start.isoformat()
            if self.billing_period_start
            else None,
            "billing_period_end": self.billing_period_end.isoformat()
            if self.billing_period_end
            else None,
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount is not None else 0.0,
            "discount_amount": float(self.discount_amount)
            if self.discount_amount is not None
            else 0.0,
            "total": float(self.total) if self.total is not None else 0.0,
            "amount_paid": float(self.amount_paid) if self.amount_paid is not None else 0.0,
            "balance_due": float(self.total - self.amount_paid)
            if (self.total is not None and self.amount_paid is not None)
            else 0.0,
            "lines": [line.to_dict() for line in self.lines] if self.lines else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InvoiceLine(db.Model):
    __tablename__ = "invoice_line"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer, db.ForeignKey("invoice.id"), nullable=False, index=True
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id"), nullable=True, index=True
    )
    variant_id = db.Column(
        db.Integer, db.ForeignKey("variant.id"), nullable=True, index=True
    )
    description = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
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

    invoice = db.relationship("Invoice", back_populates="lines")
    product = db.relationship("Product")
    variant = db.relationship("Variant")

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "product_id": self.product_id,
            "variant_id": self.variant_id,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0.0,
            "variant_price": float(self.variant_price)
            if self.variant_price is not None
            else 0.0,
            "discount_amount": float(self.discount_amount)
            if self.discount_amount is not None
            else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount is not None else 0.0,
            "line_total": float(self.line_total) if self.line_total is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Payment(db.Model):
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    invoice_id = db.Column(
        db.Integer, db.ForeignKey("invoice.id"), nullable=False, index=True
    )
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(
        db.String(50), nullable=False
    )  # credit_card, bank_transfer, cash, etc.
    date = db.Column(db.Date, nullable=False, index=True)
    note = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(50), default="completed", nullable=False, index=True
    )  # completed, refunded, partially_refunded

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    invoice = db.relationship("Invoice", back_populates="payments")
    customer = db.relationship("Customer", back_populates="payments")
    refunds = db.relationship("Refund", back_populates="payment", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "payment_number": self.payment_number,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "amount": float(self.amount) if self.amount is not None else 0.0,
            "method": self.method,
            "date": self.date.isoformat() if self.date else None,
            "note": self.note,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Refund(db.Model):
    __tablename__ = "refund"

    id = db.Column(db.Integer, primary_key=True)
    refund_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    invoice_id = db.Column(
        db.Integer, db.ForeignKey("invoice.id"), nullable=False, index=True
    )
    payment_id = db.Column(
        db.Integer, db.ForeignKey("payment.id"), nullable=True, index=True
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    invoice = db.relationship("Invoice", back_populates="refunds")
    payment = db.relationship("Payment", back_populates="refunds")

    def to_dict(self):
        return {
            "id": self.id,
            "refund_number": self.refund_number,
            "invoice_id": self.invoice_id,
            "payment_id": self.payment_id,
            "amount": float(self.amount) if self.amount is not None else 0.0,
            "reason": self.reason,
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

