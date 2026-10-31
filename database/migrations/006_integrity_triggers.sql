-- Migration: 006_integrity_triggers.sql
-- Description: Business integrity triggers: Refund limits, Invoice auto-paid sync, Auto-numbering, Status history
-- Scope: D5 - Integrity Rules (Brightloop SMS)

-- ============================================================================
-- 1. AUTO-NUMBER GENERATION TRIGGERS
-- Ensures clean business document numbers (SUB-YYYY-NNNNNN, INV-YYYY-NNNNNN, QT-YYYY-NNNNNN)
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_trg_autogen_subscription_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.number IS NULL OR TRIM(NEW.number) = '' THEN
        NEW.number := fn_generate_subscription_number();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_subscription_autogen_number
BEFORE INSERT ON subscription
FOR EACH ROW EXECUTE FUNCTION fn_trg_autogen_subscription_number();

CREATE OR REPLACE FUNCTION fn_trg_autogen_invoice_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.number IS NULL OR TRIM(NEW.number) = '' THEN
        NEW.number := fn_generate_invoice_number();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_invoice_autogen_number
BEFORE INSERT ON invoice
FOR EACH ROW EXECUTE FUNCTION fn_trg_autogen_invoice_number();

CREATE OR REPLACE FUNCTION fn_trg_autogen_quotation_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.number IS NULL OR TRIM(NEW.number) = '' THEN
        NEW.number := fn_generate_quotation_number();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_quotation_autogen_number
BEFORE INSERT ON quotation
FOR EACH ROW EXECUTE FUNCTION fn_trg_autogen_quotation_number();


-- ============================================================================
-- 2. REFUND LIMIT ENFORCEMENT TRIGGER (D5)
-- Choice Explanation:
-- Enforced via a BEFORE INSERT OR UPDATE trigger because:
-- 1. PostgreSQL CHECK constraints cannot execute subqueries or aggregate functions (SUM).
-- 2. PostgreSQL does not implement CREATE ASSERTION.
-- 3. A PL/pgSQL trigger allows acquiring a row-level lock (FOR UPDATE) on the payment row,
--    guaranteeing atomic validation and eliminating race conditions in concurrent transactions.
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_check_refund_limit()
RETURNS TRIGGER AS $$
DECLARE
    v_payment_amount NUMERIC(12,2);
    v_existing_refunds NUMERIC(12,2);
    v_payment_invoice_id BIGINT;
BEGIN
    -- Only active refund requests (not rejected) count towards the limit
    IF NEW.status = 'rejected' THEN
        RETURN NEW;
    END IF;

    -- Lock the parent payment record to prevent concurrent over-refund race conditions
    SELECT amount, invoice_id 
    INTO v_payment_amount, v_payment_invoice_id
    FROM payment 
    WHERE payment_id = NEW.payment_id 
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Payment record with ID % not found.', NEW.payment_id;
    END IF;

    -- Ensure the refund invoice_id matches the payment invoice_id for relational consistency
    IF NEW.invoice_id != v_payment_invoice_id THEN
        RAISE EXCEPTION 'Invoice ID mismatch: refund invoice_id (%) does not match payment invoice_id (%).', 
            NEW.invoice_id, v_payment_invoice_id;
    END IF;

    -- Calculate total existing non-rejected refunds for this payment, excluding the current record
    SELECT COALESCE(SUM(amount), 0.00)
    INTO v_existing_refunds
    FROM refund
    WHERE payment_id = NEW.payment_id
      AND refund_id != COALESCE(NEW.refund_id, -1)
      AND status != 'rejected';

    -- Validate total limit
    IF (v_existing_refunds + NEW.amount) > v_payment_amount THEN
        RAISE EXCEPTION 'Refund limit exceeded: Total refunds (%) would exceed original payment amount (%) for payment_id %',
            (v_existing_refunds + NEW.amount), v_payment_amount, NEW.payment_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_refund_limit_check
BEFORE INSERT OR UPDATE ON refund
FOR EACH ROW EXECUTE FUNCTION fn_check_refund_limit();


-- ============================================================================
-- 3. INVOICE AUTO-PAID SYNCHRONIZATION TRIGGER (D5)
-- When recorded payments cover the invoice total, status automatically transitions to 'paid'.
-- If a refund is processed or a payment cancelled/reduced, it reverts to 'confirmed'.
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_recalculate_invoice_payment_status(p_invoice_id BIGINT)
RETURNS VARCHAR(20) AS $$
DECLARE
    v_invoice_total NUMERIC(12,2);
    v_current_status VARCHAR(20);
    v_total_paid NUMERIC(12,2);
    v_total_refunded NUMERIC(12,2);
    v_net_paid NUMERIC(12,2);
    v_new_status VARCHAR(20);
BEGIN
    SELECT total, status INTO v_invoice_total, v_current_status
    FROM invoice
    WHERE invoice_id = p_invoice_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    -- Cancelled invoices do not automatically change status
    IF v_current_status = 'cancelled' THEN
        RETURN v_current_status;
    END IF;

    -- Sum payments
    SELECT COALESCE(SUM(amount), 0.00) INTO v_total_paid
    FROM payment
    WHERE invoice_id = p_invoice_id;

    -- Sum processed refunds
    SELECT COALESCE(SUM(amount), 0.00) INTO v_total_refunded
    FROM refund
    WHERE invoice_id = p_invoice_id
      AND status = 'processed';

    v_net_paid := v_total_paid - v_total_refunded;

    IF v_net_paid >= v_invoice_total AND v_invoice_total > 0 THEN
        v_new_status := 'paid';
    ELSE
        -- If it was paid but net_paid fell below total due to refund, revert to confirmed
        IF v_current_status = 'paid' THEN
            v_new_status := 'confirmed';
        ELSE
            v_new_status := v_current_status;
        END IF;
    END IF;

    IF v_new_status != v_current_status THEN
        UPDATE invoice
        SET status = v_new_status,
            updated_at = CURRENT_TIMESTAMP
        WHERE invoice_id = p_invoice_id;
    END IF;

    RETURN v_new_status;
END;
$$ LANGUAGE plpgsql;

-- Trigger on payment table
CREATE OR REPLACE FUNCTION fn_trg_payment_sync_invoice()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM fn_recalculate_invoice_payment_status(OLD.invoice_id);
    ELSE
        PERFORM fn_recalculate_invoice_payment_status(NEW.invoice_id);
        IF TG_OP = 'UPDATE' AND OLD.invoice_id != NEW.invoice_id THEN
            PERFORM fn_recalculate_invoice_payment_status(OLD.invoice_id);
        END IF;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_payment_after_change
AFTER INSERT OR UPDATE OR DELETE ON payment
FOR EACH ROW EXECUTE FUNCTION fn_trg_payment_sync_invoice();

-- Trigger on refund table
CREATE OR REPLACE FUNCTION fn_trg_refund_sync_invoice()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM fn_recalculate_invoice_payment_status(OLD.invoice_id);
    ELSE
        PERFORM fn_recalculate_invoice_payment_status(NEW.invoice_id);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_refund_after_change
AFTER INSERT OR UPDATE OR DELETE ON refund
FOR EACH ROW EXECUTE FUNCTION fn_trg_refund_sync_invoice();


-- ============================================================================
-- 4. SUBSCRIPTION STATUS HISTORY TRIGGER (D3)
-- Automatically captures user, timestamp, and reason on every status transition
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_log_subscription_status_change()
RETURNS TRIGGER AS $$
DECLARE
    v_changed_by BIGINT;
    v_reason TEXT;
BEGIN
    -- Read session context if provided by API layer, otherwise fall back to NULL / default
    BEGIN
        v_changed_by := NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::BIGINT;
    EXCEPTION WHEN OTHERS THEN
        v_changed_by := NULL;
    END;

    BEGIN
        v_reason := NULLIF(CURRENT_SETTING('app.status_change_reason', true), '');
    EXCEPTION WHEN OTHERS THEN
        v_reason := NULL;
    END;

    IF v_reason IS NULL THEN
        v_reason := 'Lifecycle transition from ' || COALESCE(OLD.status, 'none') || ' to ' || NEW.status;
    END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO subscription_status_history (subscription_id, from_status, to_status, changed_by, reason)
        VALUES (NEW.subscription_id, NULL, NEW.status, v_changed_by, 'Initial creation');
    ELSIF TG_OP = 'UPDATE' AND (OLD.status IS DISTINCT FROM NEW.status) THEN
        INSERT INTO subscription_status_history (subscription_id, from_status, to_status, changed_by, reason)
        VALUES (NEW.subscription_id, OLD.status, NEW.status, v_changed_by, v_reason);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_subscription_status_history
AFTER INSERT OR UPDATE OF status ON subscription
FOR EACH ROW EXECUTE FUNCTION fn_log_subscription_status_change();


-- ============================================================================
-- 5. ATOMIC DISCOUNT USAGE HELPER (D5)
-- Concurrency-safe decrement pattern using row locking and WHERE bounds
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_apply_discount_atomically(p_discount_id BIGINT)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated_count INT;
BEGIN
    UPDATE discount
    SET times_used = times_used + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE discount_id = p_discount_id
      AND is_active = TRUE
      AND (usage_limit IS NULL OR times_used < usage_limit)
      AND (start_date <= CURRENT_DATE AND (end_date IS NULL OR end_date >= CURRENT_DATE));

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RETURN (v_updated_count > 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_check_refund_limit() IS 'Enforces that total active refunds do not exceed the payment amount.';
COMMENT ON FUNCTION fn_recalculate_invoice_payment_status(BIGINT) IS 'Recalculates net paid amount and automatically sets invoice status to paid or confirmed.';
COMMENT ON FUNCTION fn_apply_discount_atomically(BIGINT) IS 'Atomically increments discount usage counter ensuring usage_limit is never exceeded.';
