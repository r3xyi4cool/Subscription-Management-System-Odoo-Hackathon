from decimal import Decimal
from datetime import date, timedelta
from backend.app.models.catalog import Product, Variant, Discount, Tax
from backend.app.services.pricing_service import PricingService


def test_pricing_percentage_and_tax():
    product = Product(sales_price=Decimal("100.00"))
    variant = Variant(extra_price=Decimal("20.00"))
    discount = Discount(
        code="TEN",
        discount_type="percentage",
        value=Decimal("10.00"),
        is_active=True,
    )
    tax = Tax(name="VAT", rate=Decimal("10.00"), is_active=True)

    # (100 + 20) * 2 = 240.00
    # 10% discount on 240.00 = 24.00 -> 216.00
    # 10% tax on 216.00 = 21.60 -> total 237.60
    calc = PricingService.calculate_line(
        product=product,
        quantity=2,
        variant=variant,
        discount=discount,
        tax=tax,
    )
    assert calc["subtotal"] == Decimal("240.00")
    assert calc["discount_amount"] == Decimal("24.00")
    assert calc["tax_amount"] == Decimal("21.60")
    assert calc["line_total"] == Decimal("237.60")


def test_pricing_fixed_discount():
    product = Product(sales_price=Decimal("100.00"))
    discount = Discount(
        code="FIXED30",
        discount_type="fixed",
        value=Decimal("30.00"),
        is_active=True,
    )
    tax = Tax(name="VAT", rate=Decimal("5.00"), is_active=True)

    # 100 * 2 = 200.00
    # Fixed discount = 30.00 -> 170.00
    # 5% tax on 170.00 = 8.50 -> total 178.50
    calc = PricingService.calculate_line(
        product=product,
        quantity=2,
        discount=discount,
        tax=tax,
    )
    assert calc["subtotal"] == Decimal("200.00")
    assert calc["discount_amount"] == Decimal("30.00")
    assert calc["tax_amount"] == Decimal("8.50")
    assert calc["line_total"] == Decimal("178.50")


def test_pricing_min_quantity_restriction():
    product = Product(sales_price=Decimal("50.00"))
    discount = Discount(
        code="MIN5",
        discount_type="percentage",
        value=Decimal("20.00"),
        min_quantity=5,
        is_active=True,
    )

    # Qty 3 is below min_quantity 5 -> no discount applied!
    calc = PricingService.calculate_line(
        product=product,
        quantity=3,
        discount=discount,
    )
    assert calc["discount_amount"] == Decimal("0.00")
    assert calc["line_total"] == Decimal("150.00")

    # Qty 5 meets min_quantity 5 -> discount applied!
    calc5 = PricingService.calculate_line(
        product=product,
        quantity=5,
        discount=discount,
    )
    assert calc5["discount_amount"] == Decimal("50.00")  # 20% of 250
    assert calc5["line_total"] == Decimal("200.00")


def test_pricing_expired_and_usage_limit():
    product = Product(sales_price=Decimal("100.00"))

    # Expired discount
    expired_disc = Discount(
        code="EXP",
        discount_type="percentage",
        value=Decimal("50.00"),
        start_date=date.today() - timedelta(days=60),
        end_date=date.today() - timedelta(days=1),
        is_active=True,
    )
    calc_exp = PricingService.calculate_line(product=product, quantity=1, discount=expired_disc)
    assert calc_exp["discount_amount"] == Decimal("0.00")

    # Usage limit reached
    limit_disc = Discount(
        code="LIM",
        discount_type="percentage",
        value=Decimal("50.00"),
        usage_limit=10,
        used_count=10,
        is_active=True,
    )
    calc_lim = PricingService.calculate_line(product=product, quantity=1, discount=limit_disc)
    assert calc_lim["discount_amount"] == Decimal("0.00")

