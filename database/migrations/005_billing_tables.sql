-- Migration: 005_billing_tables.sql
-- Description: Billing tables: Invoice, Invoice Line, Payment, and Refund
-- Scope: D4 - Billing Tables & D5 - Constraints (Brightloop SMS)

-- 1. Invoice table
-- Financial document generated per billing period.
-- Enforces: UNIQUE (subscription_id, billing_period) to prevent double billing.
CREATE TABLE IF NOT EXISTS invoice (
    invoice_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    number VARCHAR(50) NOT NULL UNIQUE,
    subscription_id BIGINT,
    customer_id BIGINT NOT NULL,
    billing_period VARCHAR(50) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    discount_total NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    tax_total NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    total NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_invoice_subscription FOREIGN KEY (subscription_id) REFERENCES subscription(subscription_id) ON DELETE RESTRICT,
    CONSTRAINT fk_invoice_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE RESTRICT,
    CONSTRAINT chk_invoice_status CHECK (status IN ('draft', 'confirmed', 'paid', 'cancelled')),
    CONSTRAINT chk_invoice_due_date CHECK (due_date >= issue_date),
    CONSTRAINT chk_invoice_subtotal CHECK (subtotal >= 0),
    CONSTRAINT chk_invoice_discount_total CHECK (discount_total >= 0),
    CONSTRAINT chk_invoice_tax_total CHECK (tax_total >= 0),
    CONSTRAINT chk_invoice_total CHECK (total >= 0),
    -- D5 guarantee: No subscription is billed twice for the same billing period
    CONSTRAINT uq_invoice_subscription_period UNIQUE (subscription_id, billing_period)
);

CREATE TRIGGER trg_invoice_updated_at
BEFORE UPDATE ON invoice
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 2. Invoice Line table
-- Calculation order: line base amount (qty * unit_price) -> discount -> tax -> line total amount
CREATE TABLE IF NOT EXISTS invoice_line (
    line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    product_id BIGINT,
    variant_id BIGINT,
    description VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    tax_id BIGINT,
    tax_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    amount NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_il_invoice FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id) ON DELETE CASCADE,
    CONSTRAINT fk_il_product FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE RESTRICT,
    CONSTRAINT fk_il_variant FOREIGN KEY (variant_id) REFERENCES product_variant(variant_id) ON DELETE RESTRICT,
    CONSTRAINT fk_il_tax FOREIGN KEY (tax_id) REFERENCES tax(tax_id) ON DELETE RESTRICT,
    CONSTRAINT chk_il_quantity CHECK (quantity > 0),
    CONSTRAINT chk_il_unit_price CHECK (unit_price >= 0),
    CONSTRAINT chk_il_discount_amount CHECK (discount_amount >= 0),
    CONSTRAINT chk_il_tax_amount CHECK (tax_amount >= 0),
    CONSTRAINT chk_il_amount CHECK (amount >= 0)
);

-- 3. Payment table
-- Payments recorded against specific invoices.
CREATE TABLE IF NOT EXISTS payment (
    payment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    method VARCHAR(50) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    payment_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    recorded_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_invoice FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_recorded_by FOREIGN KEY (recorded_by) REFERENCES auth(id) ON DELETE SET NULL,
    CONSTRAINT chk_payment_amount CHECK (amount > 0),
    CONSTRAINT chk_payment_method CHECK (method IN ('card', 'bank_transfer', 'upi', 'cash', 'cheque', 'other'))
);

CREATE TRIGGER trg_payment_updated_at
BEFORE UPDATE ON payment
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 4. Refund table
-- Refund issued against an invoice payment.
CREATE TABLE IF NOT EXISTS refund (
    refund_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_id BIGINT NOT NULL,
    invoice_id BIGINT NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'requested',
    processed_date TIMESTAMPTZ,
    approved_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_refund_payment FOREIGN KEY (payment_id) REFERENCES payment(payment_id) ON DELETE RESTRICT,
    CONSTRAINT fk_refund_invoice FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id) ON DELETE RESTRICT,
    CONSTRAINT fk_refund_approved_by FOREIGN KEY (approved_by) REFERENCES auth(id) ON DELETE SET NULL,
    CONSTRAINT chk_refund_amount CHECK (amount > 0),
    CONSTRAINT chk_refund_status CHECK (status IN ('requested', 'approved', 'processed', 'rejected'))
);

CREATE TRIGGER trg_refund_updated_at
BEFORE UPDATE ON refund
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

COMMENT ON TABLE invoice IS 'Periodic financial statements for subscription billing cycles.';
COMMENT ON TABLE invoice_line IS 'Itemized line charges including price, discount, and tax calculations.';
COMMENT ON TABLE payment IS 'Payment receipts credited towards specific invoices.';
COMMENT ON TABLE refund IS 'Disbursements returning funds from payments with status tracking.';
