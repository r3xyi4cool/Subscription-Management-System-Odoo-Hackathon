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


def test_pricing_rounding_edge_cases():
    # 1. 0.005 half-up rounding on discount: 10.05 * 0.05 = 0.5025 -> 0.50
    p1 = Product(sales_price=Decimal("10.05"))
    d1 = Discount(code="D1", discount_type="percentage", value=Decimal("5.00"), is_active=True)
    c1 = PricingService.calculate_line(product=p1, quantity=1, discount=d1)
    assert c1["discount_amount"] == Decimal("0.50")
    assert c1["subtotal"] == Decimal("10.05")
    assert c1["line_total"] == Decimal("9.55")

    # 2. 0.0075 half-up rounding: 10.15 * 0.05 = 0.5075 -> 0.51
    p2 = Product(sales_price=Decimal("10.15"))
    c2 = PricingService.calculate_line(product=p2, quantity=1, discount=d1)
    assert c2["discount_amount"] == Decimal("0.51")
    assert c2["line_total"] == Decimal("9.64")

    # 3. Tax rounding half-up: 7.5% on 19.95 = 1.49625 -> 1.50
    p3 = Product(sales_price=Decimal("19.95"))
    t1 = Tax(name="GST", rate=Decimal("7.50"), is_active=True)
    c3 = PricingService.calculate_line(product=p3, quantity=1, tax=t1)
    assert c3["tax_amount"] == Decimal("1.50")
    assert c3["line_total"] == Decimal("21.45")

    # 4. Strict half-up boundary: 0.10 * 0.05 = 0.005 -> 0.01
    p4 = Product(sales_price=Decimal("0.10"))
    t2 = Tax(name="LowTax", rate=Decimal("5.00"), is_active=True)
    c4 = PricingService.calculate_line(product=p4, quantity=1, tax=t2)
    assert c4["tax_amount"] == Decimal("0.01")
    assert c4["line_total"] == Decimal("0.11")

    # 5. Combined precision: Product with variant price ending in odd cent
    p5 = Product(sales_price=Decimal("33.33"))
    v5 = Variant(extra_price=Decimal("0.34"))  # 33.67
    d5 = Discount(code="D5", discount_type="percentage", value=Decimal("15.00"), is_active=True)
    t5 = Tax(name="Tax18", rate=Decimal("18.00"), is_active=True)
    c5 = PricingService.calculate_line(product=p5, quantity=3, variant=v5, discount=d5, tax=t5)
    assert c5["subtotal"] == Decimal("101.01")
    assert c5["discount_amount"] == Decimal("15.15")
    assert c5["tax_amount"] == Decimal("15.45")
    assert c5["line_total"] == Decimal("101.31")

