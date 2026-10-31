from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import Optional


class PricingService:
    @staticmethod
    def to_decimal(val) -> Decimal:
        if val is None:
            return Decimal("0.00")
        if isinstance(val, Decimal):
            return val
        return Decimal(str(val))

    @classmethod
    def calculate_line(
        cls,
        product,
        quantity: int = 1,
        variant=None,
        discount=None,
        tax=None,
        as_of_date: Optional[date] = None,
        context: str = "product",  # 'product' or 'subscription'
    ):
        if as_of_date is None:
            as_of_date = date.today()

        unit_price = cls.to_decimal(
            getattr(product, "sales_price", product)
        )
        variant_price = (
            cls.to_decimal(getattr(variant, "extra_price", 0.0))
            if variant
            else Decimal("0.00")
        )
        quantity_dec = cls.to_decimal(quantity)

        combined_unit = unit_price + variant_price
        subtotal_raw = (combined_unit * quantity_dec).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        discount_amount = Decimal("0.00")
        discount_applied = False

        if discount:
            is_active = getattr(discount, "is_active", True)
            if is_active is None:
                is_active = True

            start_date = getattr(discount, "start_date", None)
            end_date = getattr(discount, "end_date", None)
            usage_limit = getattr(discount, "usage_limit", None)
            used_count = getattr(discount, "used_count", 0) or 0
            min_quantity = getattr(discount, "min_quantity", 0) or 0
            min_purchase = cls.to_decimal(getattr(discount, "min_purchase", 0.0) or 0.0)
            applies_to = getattr(discount, "applies_to", None) or "all"
            disc_type = getattr(discount, "discount_type", "percentage") or "percentage"
            disc_value = cls.to_decimal(getattr(discount, "value", 0.0) or 0.0)

            eligible = is_active
            if start_date and as_of_date < start_date:
                eligible = False
            if end_date and as_of_date > end_date:
                eligible = False
            if usage_limit is not None and used_count >= usage_limit:
                eligible = False
            if min_quantity and quantity < min_quantity:
                eligible = False
            if min_purchase and subtotal_raw < min_purchase:
                eligible = False
            if applies_to not in ("all", context):
                eligible = False

            if eligible:
                if disc_type == "percentage":
                    discount_amount = (
                        subtotal_raw * (disc_value / Decimal("100.00"))
                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:  # fixed
                    discount_amount = min(subtotal_raw, disc_value).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                discount_applied = True

        discounted_subtotal = max(Decimal("0.00"), subtotal_raw - discount_amount)

        tax_amount = Decimal("0.00")
        if tax:
            is_tax_active = getattr(tax, "is_active", True)
            if is_tax_active is None:
                is_tax_active = True
            tax_rate = cls.to_decimal(getattr(tax, "rate", 0.0) or 0.0)
            if is_tax_active and tax_rate > 0:
                tax_amount = (
                    discounted_subtotal * (tax_rate / Decimal("100.00"))
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        line_total = (discounted_subtotal + tax_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "unit_price": unit_price,
            "variant_price": variant_price,
            "quantity": quantity,
            "subtotal": subtotal_raw,
            "discount_amount": discount_amount,
            "discount_applied": discount_applied,
            "tax_amount": tax_amount,
            "line_total": line_total,
        }
