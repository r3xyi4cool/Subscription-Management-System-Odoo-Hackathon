-- Migration: 008_audit_log.sql
-- Description: Immutable audit log table and automated change capture triggers
-- Scope: D9 - Audit Log (Brightloop SMS)

-- ============================================================================
-- 1. AUDIT LOG TABLE
-- Structured immutable ledger for compliance, forensic, and security tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(20) NOT NULL,
    entity VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_values JSONB,
    new_values JSONB,

    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES auth(id) ON DELETE SET NULL,
    CONSTRAINT chk_audit_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'))
);

-- Index for chronological and entity-specific audit reviews
CREATE INDEX IF NOT EXISTS idx_audit_log_entity_id ON audit_log (entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log (user_id);


-- ============================================================================
-- 2. INSERT-ONLY ENFORCEMENT RULE (D9)
-- Strictly prohibits UPDATE and DELETE actions on the audit_log table
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_audit_log_prevent_tampering()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log security violation: % operations are strictly forbidden on audit_log. Records are append-only.', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_log_immutable
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION fn_audit_log_prevent_tampering();

-- Revoke modification privileges from public role
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM PUBLIC;


-- ============================================================================
-- 3. AUDIT CAPTURE TRIGGER FUNCTION
-- Captures state changes on financial and configuration tables:
-- Invoice, Invoice Line, Payment, Refund, Discount, Tax
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_audit_log_capture()
RETURNS TRIGGER AS $$
DECLARE
    v_user_id BIGINT;
    v_action VARCHAR(20);
    v_entity VARCHAR(50);
    v_entity_id VARCHAR(100);
    v_old_json JSONB := NULL;
    v_new_json JSONB := NULL;
BEGIN
    v_action := TG_OP;
    v_entity := TG_TABLE_NAME;

    -- Extract JSON representations
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        v_old_json := to_jsonb(OLD);
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        v_new_json := to_jsonb(NEW);
    END IF;

    -- Extract entity primary key dynamically
    v_entity_id := COALESCE(
        v_new_json->>'invoice_id',
        v_new_json->>'line_id',
        v_new_json->>'payment_id',
        v_new_json->>'refund_id',
        v_new_json->>'discount_id',
        v_new_json->>'tax_id',
        v_old_json->>'invoice_id',
        v_old_json->>'line_id',
        v_old_json->>'payment_id',
        v_old_json->>'refund_id',
        v_old_json->>'discount_id',
        v_old_json->>'tax_id',
        'unknown'
    );

    -- Retrieve current user from session variable if set by backend middleware
    BEGIN
        v_user_id := NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::BIGINT;
    EXCEPTION WHEN OTHERS THEN
        v_user_id := NULL;
    END;

    -- Fallback to inline audit user fields if present
    IF v_user_id IS NULL THEN
        IF v_new_json ? 'recorded_by' THEN
            v_user_id := (v_new_json->>'recorded_by')::BIGINT;
        ELSIF v_new_json ? 'approved_by' THEN
            v_user_id := (v_new_json->>'approved_by')::BIGINT;
        ELSIF v_new_json ? 'created_by' THEN
            v_user_id := (v_new_json->>'created_by')::BIGINT;
        END IF;
    END IF;

    -- Record the audit event
    INSERT INTO audit_log (
        user_id,
        action,
        entity,
        entity_id,
        timestamp,
        old_values,
        new_values
    ) VALUES (
        v_user_id,
        v_action,
        v_entity,
        v_entity_id,
        CURRENT_TIMESTAMP,
        v_old_json,
        v_new_json
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 4. ATTACH AUDIT TRIGGERS (D9)
-- Attaches change capture to Invoice, Invoice Line, Payment, Refund, Discount, Tax
-- ============================================================================

-- Invoice audit
CREATE TRIGGER trg_audit_invoice
AFTER INSERT OR UPDATE OR DELETE ON invoice
FOR EACH ROW EXECUTE FUNCTION fn_audit_log_capture();

-- Invoice Line audit
CREATE TRIGGER trg_audit_invoice_line
AFTER INSERT OR UPDATE OR DELETE ON invoice_line
FOR EACH ROW EXECUTE FUNCTION fn_audit_log_capture();

-- Payment audit
CREATE TRIGGER trg_audit_payment
AFTER INSERT OR UPDATE OR DELETE ON payment
FOR EACH ROW EXECUTE FUNCTION fn_audit_log_capture();

-- Refund audit
CREATE TRIGGER trg_audit_refund
AFTER INSERT OR UPDATE OR DELETE ON refund
FOR EACH ROW EXECUTE FUNCTION fn_audit_log_capture();

-- Discount audit
CREATE TRIGGER trg_audit_discount
AFTER INSERT OR UPDATE OR DELETE ON discount
FOR EACH ROW EXECUTE FUNCTION fn_audit_log_capture();

-- Tax audit
CREATE TRIGGER trg_audit_tax
AFTER INSERT OR UPDATE OR DELETE ON tax
FOR EACH ROW EXECUTE FUNCTION fn_audit_log_capture();

COMMENT ON TABLE audit_log IS 'Append-only audit trail logging all modifications to financial and sensitive configurations.';
COMMENT ON TRIGGER trg_audit_log_immutable ON audit_log IS 'Guarantees audit trail immutability by aborting UPDATE and DELETE attempts.';
