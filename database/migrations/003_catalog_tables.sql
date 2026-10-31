-- Migration: 003_catalog_tables.sql
-- Description: Catalog tables: Product, Product Variant, Plan, Tax, Discount
-- Scope: D2 - Catalog Tables (Brightloop SMS)

-- 1. Product table
-- Core product catalog entries. Base price is sales_price.
CREATE TABLE IF NOT EXISTS product (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'service',
    sales_price NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    cost_price NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_product_type CHECK (type IN ('service', 'software', 'add-on', 'physical')),
    CONSTRAINT chk_product_sales_price CHECK (sales_price >= 0),
    CONSTRAINT chk_product_cost_price CHECK (cost_price >= 0)
);

CREATE TRIGGER trg_product_updated_at
BEFORE UPDATE ON product
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 2. Product Variant table
-- Variants add extra_price to the base sales_price (e.g., brand = 'Odoo' adds Rs 560).
CREATE TABLE IF NOT EXISTS product_variant (
    variant_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL,
    attribute VARCHAR(100) NOT NULL,
    value VARCHAR(100) NOT NULL,
    extra_price NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_variant_product FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE,
    CONSTRAINT chk_variant_extra_price CHECK (extra_price >= 0),
    CONSTRAINT uq_product_variant UNIQUE (product_id, attribute, value)
);

CREATE TRIGGER trg_product_variant_updated_at
BEFORE UPDATE ON product_variant
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 3. Plan table
-- Subscription plans driving recurring schedules and customer permissions.
CREATE TABLE IF NOT EXISTS plan (
    plan_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    billing_period VARCHAR(20) NOT NULL,
    min_quantity INTEGER NOT NULL DEFAULT 1,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE,
    auto_close BOOLEAN NOT NULL DEFAULT FALSE,
    allow_early_close BOOLEAN NOT NULL DEFAULT TRUE,
    allow_pause BOOLEAN NOT NULL DEFAULT TRUE,
    allow_renewal BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_plan_billing_period CHECK (billing_period IN ('daily', 'weekly', 'monthly', 'yearly')),
    CONSTRAINT chk_plan_price CHECK (price >= 0),
    CONSTRAINT chk_plan_min_quantity CHECK (min_quantity > 0),
    CONSTRAINT chk_plan_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TRIGGER trg_plan_updated_at
BEFORE UPDATE ON plan
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 4. Tax table
-- Governs line-level and total tax calculations.
CREATE TABLE IF NOT EXISTS tax (
    tax_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rate NUMERIC(5,2) NOT NULL,
    applies_to VARCHAR(100) NOT NULL DEFAULT 'all',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_tax_rate CHECK (rate >= 0.00 AND rate <= 100.00)
);

CREATE TRIGGER trg_tax_updated_at
BEFORE UPDATE ON tax
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 5. Discount table
-- Rule engine for fixed-amount and percentage discounts with atomic usage limits.
CREATE TABLE IF NOT EXISTS discount (
    discount_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    type VARCHAR(20) NOT NULL,
    value NUMERIC(12,2) NOT NULL,
    scope VARCHAR(50) NOT NULL DEFAULT 'subscription',
    product_id BIGINT,
    min_amount NUMERIC(12,2) DEFAULT 0.00,
    min_qty INTEGER DEFAULT 0,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE,
    usage_limit INTEGER,
    times_used INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_discount_product FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE SET NULL,
    CONSTRAINT chk_discount_type CHECK (type IN ('fixed', 'percent')),
    CONSTRAINT chk_discount_value CHECK (value > 0),
    CONSTRAINT chk_discount_percent CHECK (type != 'percent' OR value <= 100.00),
    CONSTRAINT chk_discount_scope CHECK (scope IN ('product', 'subscription')),
    CONSTRAINT chk_discount_min_amount CHECK (min_amount >= 0),
    CONSTRAINT chk_discount_min_qty CHECK (min_qty >= 0),
    CONSTRAINT chk_discount_dates CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT chk_discount_usage_limit CHECK (usage_limit IS NULL OR usage_limit > 0),
    CONSTRAINT chk_discount_times_used CHECK (times_used >= 0),
    CONSTRAINT chk_discount_limit_cap CHECK (usage_limit IS NULL OR times_used <= usage_limit)
);

CREATE TRIGGER trg_discount_updated_at
BEFORE UPDATE ON discount
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 6. Discount Product Junction (Many-to-Many link between Discounts and Products)
CREATE TABLE IF NOT EXISTS discount_product (
    discount_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_discount_product PRIMARY KEY (discount_id, product_id),
    CONSTRAINT fk_dp_discount FOREIGN KEY (discount_id) REFERENCES discount(discount_id) ON DELETE CASCADE,
    CONSTRAINT fk_dp_product FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE
);

COMMENT ON TABLE product IS 'Items and services available for subscription.';
COMMENT ON TABLE product_variant IS 'Product variations adding specific extra charges.';
COMMENT ON TABLE plan IS 'Billing frequency and feature flag constraints for subscriptions.';
COMMENT ON TABLE tax IS 'Tax rates and category application rules.';
COMMENT ON TABLE discount IS 'Admin-defined promotional discounts and conditions.';
COMMENT ON TABLE discount_product IS 'Junction mapping discounts to specific products (many-to-many).';
