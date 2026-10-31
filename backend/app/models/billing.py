from datetime import datetime, timezone
from decimal import Decimal
from backend.app.extensions import db


class Invoice(db.Model):
    __tablename__ = "invoice"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    subscription_id = db.Column(
        db.Integer, db.ForeignKey("subscription.id"), nullable=True, index=True
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

    customer = db.relationship("Customer", back_populates="invoices")
    subscription = db.relationship("Subscription", back_populates="invoices")
    lines = db.relationship(
        "InvoiceLine", back_populates="invoice", cascade="all, delete-orphan", lazy="joined"
    )
    payments = db.relationship("Payment", back_populates="invoice", lazy="dynamic")
    refunds = db.relationship("Refund", back_populates="invoice", lazy="dynamic")

    __table_args__ = (
        db.UniqueConstraint(
            "subscription_id",
            "billing_period_start",
            "billing_period_end",
            name="uq_invoice_subscription_period",
        ),
    )

    def to_dict(self):
        sub_val = float(self.subtotal) if self.subtotal is not None else 0.0
        tax_val = float(self.tax_amount) if self.tax_amount is not None else 0.0
        disc_val = float(self.discount_amount) if self.discount_amount is not None else 0.0
        tot_val = float(self.total) if self.total is not None else 0.0
        paid_val = float(self.amount_paid) if self.amount_paid is not None else 0.0
        bal_val = max(0.0, tot_val - paid_val)
        taxable_val = max(0.0, sub_val - disc_val)

        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "subscription_id": self.subscription_id,
            "subscription_number": self.subscription.subscription_number if self.subscription else None,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else None,
            "customer_email": self.customer.email if self.customer else None,
            "status": self.status,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "billing_period_start": self.billing_period_start.isoformat()
            if self.billing_period_start
            else None,
            "billing_period_end": self.billing_period_end.isoformat()
            if self.billing_period_end
            else None,
            "subtotal": sub_val,
            "lines_subtotal_paise": int(round(sub_val * 100)),
            "subtotal_paise": int(round(sub_val * 100)),
            "tax_amount": tax_val,
            "tax_total_paise": int(round(tax_val * 100)),
            "tax_paise": int(round(tax_val * 100)),
            "taxable_amount_paise": int(round(taxable_val * 100)),
            "discount_amount": disc_val,
            "discount_paise": int(round(disc_val * 100)),
            "total": tot_val,
            "total_paise": int(round(tot_val * 100)),
            "amount_paid": paid_val,
            "amount_paid_paise": int(round(paid_val * 100)),
            "balance_due": bal_val,
            "balance_due_paise": int(round(bal_val * 100)),
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
        up = float(self.unit_price) if self.unit_price is not None else 0.0
        vp = float(self.variant_price) if self.variant_price is not None else 0.0
        da = float(self.discount_amount) if self.discount_amount is not None else 0.0
        ta = float(self.tax_amount) if self.tax_amount is not None else 0.0
        lt = float(self.line_total) if self.line_total is not None else 0.0
        sub_total = (up + vp) * self.quantity

        prod_name = self.product.name if self.product else (self.description or "Line Item")
        var_name = self.variant.name if self.variant else None

        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "product_id": self.product_id,
            "product_name": prod_name,
            "variant_id": self.variant_id,
            "variant_name": var_name,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": up,
            "unit_price_paise": int(round(up * 100)),
            "variant_price": vp,
            "variant_price_paise": int(round(vp * 100)),
            "line_subtotal_paise": int(round(sub_total * 100)),
            "discount_amount": da,
            "discount_paise": int(round(da * 100)),
            "tax_amount": ta,
            "line_tax_paise": int(round(ta * 100)),
            "tax_rate_percent": round((ta / sub_total * 100), 2) if sub_total > 0 else 0.0,
            "line_total": lt,
            "line_total_paise": int(round(lt * 100)),
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
    )  # cash, card, bank_transfer, etc.
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(50), default="completed", nullable=False
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
        a = float(self.amount) if self.amount is not None else 0.0
        return {
            "id": self.id,
            "payment_number": self.payment_number,
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice.invoice_number if self.invoice else None,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else None,
            "amount": a,
            "amount_paise": int(round(a * 100)),
            "method": self.method,
            "payment_method": self.method,
            "date": self.date.isoformat() if self.date else None,
            "payment_date": self.date.isoformat() if self.date else None,
            "note": self.note,
            "notes": self.note,
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
        a = float(self.amount) if self.amount is not None else 0.0
        cust_id = self.invoice.customer_id if self.invoice else None
        cust_name = self.invoice.customer.name if self.invoice and self.invoice.customer else None
        inv_num = self.invoice.invoice_number if self.invoice else None

        return {
            "id": self.id,
            "refund_number": self.refund_number,
            "invoice_id": self.invoice_id,
            "invoice_number": inv_num,
            "payment_id": self.payment_id,
            "customer_id": cust_id,
            "customer_name": cust_name,
            "amount": a,
            "amount_paise": int(round(a * 100)),
            "reason": self.reason,
            "notes": self.reason,
            "status": "processed",
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
