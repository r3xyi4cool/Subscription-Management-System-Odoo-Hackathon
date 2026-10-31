from datetime import datetime, timezone
from decimal import Decimal
from backend.app.extensions import db


class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sales_price = db.Column(db.Numeric(12, 2), nullable=False)
    cost_price = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
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

    variants = db.relationship(
        "Variant", back_populates="product", cascade="all, delete-orphan", lazy="joined"
    )

    def to_dict(self):
        sp = float(self.sales_price) if self.sales_price is not None else 0.0
        cp = float(self.cost_price) if self.cost_price is not None else 0.0
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sales_price": sp,
            "sales_price_paise": int(round(sp * 100)),
            "cost_price": cp,
            "cost_price_paise": int(round(cp * 100)),
            "is_active": self.is_active,
            "variants": [v.to_dict() for v in self.variants],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Variant(db.Model):
    __tablename__ = "variant"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id"), nullable=False, index=True
    )
    name = db.Column(db.String(255), nullable=False)
    extra_price = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
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

    product = db.relationship("Product", back_populates="variants")

    def to_dict(self):
        ep = float(self.extra_price) if self.extra_price is not None else 0.0
        return {
            "id": self.id,
            "product_id": self.product_id,
            "name": self.name,
            "extra_price": ep,
            "extra_price_paise": int(round(ep * 100)),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Plan(db.Model):
    __tablename__ = "plan"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    billing_period = db.Column(
        db.String(50), nullable=False
    )  # daily, weekly, monthly, yearly
    min_quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(12, 2), default=Decimal("0.00"), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    auto_close = db.Column(db.Boolean, default=False, nullable=True)
    allow_pause = db.Column(db.Boolean, default=True, nullable=False)
    allow_close = db.Column(db.Boolean, default=True, nullable=False)
    allow_renew = db.Column(db.Boolean, default=True, nullable=False)
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

    subscriptions = db.relationship("Subscription", back_populates="plan", lazy="dynamic")

    @property
    def allow_early_close(self):
        return self.allow_close

    @allow_early_close.setter
    def allow_early_close(self, val):
        self.allow_close = val

    @property
    def allow_renewal(self):
        return self.allow_renew

    @allow_renewal.setter
    def allow_renewal(self, val):
        self.allow_renew = val

    def to_dict(self):
        p_val = float(self.price) if self.price is not None else 0.0
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "billing_period": self.billing_period,
            "min_quantity": self.min_quantity,
            "price": p_val,
            "price_paise": int(round(p_val * 100)),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "allow_pause": self.allow_pause,
            "allow_close": self.allow_close,
            "allow_early_close": self.allow_close,
            "allow_renew": self.allow_renew,
            "allow_renewal": self.allow_renew,
            "auto_close": bool(self.auto_close),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Discount(db.Model):
    __tablename__ = "discount"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    discount_type = db.Column(db.String(50), nullable=False)  # percentage, fixed
    value = db.Column(db.Numeric(12, 2), nullable=False)
    min_quantity = db.Column(db.Integer, nullable=False, default=0)
    min_purchase = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    usage_limit = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, nullable=False, default=0)
    applies_to = db.Column(
        db.String(50), nullable=False, default="all"
    )  # product, subscription, all
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
        v = float(self.value) if self.value is not None else 0.0
        mp = float(self.min_purchase) if self.min_purchase is not None else 0.0
        dtype = "percent" if self.discount_type in ("percentage", "percent") else "fixed"
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "discount_type": dtype,
            "type": dtype,
            "value": v,
            "value_paise": int(round(v * 100)) if dtype == "fixed" else int(v),
            "min_quantity": self.min_quantity,
            "min_purchase": mp,
            "min_purchase_paise": int(round(mp * 100)),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "usage_limit": self.usage_limit,
            "used_count": self.used_count,
            "applies_to": self.applies_to,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Tax(db.Model):
    __tablename__ = "tax"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    rate = db.Column(db.Numeric(12, 2), nullable=False)  # e.g., 10.00 for 10%
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
        r = float(self.rate) if self.rate is not None else 0.0
        return {
            "id": self.id,
            "name": self.name,
            "rate": r,
            "percentage": r,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
