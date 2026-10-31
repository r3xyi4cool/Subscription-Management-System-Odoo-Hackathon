-- Script: verify_tests.sql
-- Description: Automated verification test suite validating constraints and triggers (D1-D9)
-- Scope: Quality Assurance & Acceptance Testing (Brightloop SMS)

\set ON_ERROR_STOP off
\echo '========================================================================='
\echo '  Brightloop SMS: Database Integrity & Constraint Verification Test Suite'
\echo '========================================================================='

DO $$
DECLARE
    v_passed INT := 0;
    v_failed INT := 0;
    v_test_name TEXT;
BEGIN
    RAISE NOTICE 'Starting automated verification tests...';

    -- ========================================================================
    -- TEST 1: D1 - Duplicate email rejection (Case-Insensitive)
    -- ========================================================================
    v_test_name := 'TEST 1 (D1): Duplicate email rejection (case-insensitive)';
    BEGIN
        INSERT INTO auth (email, password_hash, role) 
        VALUES ('ADMIN@BRIGHTLOOP.IO', 'dummy_hash', 'admin');
        
        RAISE WARNING 'FAIL: % - Duplicate email was allowed!', v_test_name;
        v_failed := v_failed + 1;
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'PASS: % - Correctly rejected duplicate case-insensitive email.', v_test_name;
        v_passed := v_passed + 1;
    END;

    -- ========================================================================
    -- TEST 2: D1 - Invalid Auth role rejection
    -- ========================================================================
    v_test_name := 'TEST 2 (D1): Invalid Auth role rejection';
    BEGIN
        INSERT INTO auth (email, password_hash, role) 
        VALUES ('hacker@test.com', 'dummy_hash', 'superuser');
        
        RAISE WARNING 'FAIL: % - Invalid role was accepted!', v_test_name;
        v_failed := v_failed + 1;
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: % - Correctly rejected invalid role.', v_test_name;
        v_passed := v_passed + 1;
    END;

    -- ========================================================================
    -- TEST 3: D2 - Negative price rejection on Product
    -- ========================================================================
    v_test_name := 'TEST 3 (D2): Negative product price rejection';
    BEGIN
        INSERT INTO product (name, sales_price) VALUES ('Invalid Negative Item', -50.00);
        
        RAISE WARNING 'FAIL: % - Negative price was accepted!', v_test_name;
        v_failed := v_failed + 1;
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: % - Correctly rejected negative sales price.', v_test_name;
        v_passed := v_passed + 1;
    END;

    -- ========================================================================
    -- TEST 4: D3 - Auto-generation of Subscription Number
    -- ========================================================================
    v_test_name := 'TEST 4 (D3): Auto-generated Subscription Number format';
    DECLARE
        v_new_sub_num VARCHAR(50);
        v_new_sub_id BIGINT;
    BEGIN
        INSERT INTO subscription (customer_id, plan_id, next_billing_date, status)
        VALUES (1, 1, CURRENT_DATE + 30, 'draft')
        RETURNING subscription_id, number INTO v_new_sub_id, v_new_sub_num;

        IF v_new_sub_num LIKE 'SUB-%-%' THEN
            RAISE NOTICE 'PASS: % - Successfully generated: %', v_test_name, v_new_sub_num;
            v_passed := v_passed + 1;
        ELSE
            RAISE WARNING 'FAIL: % - Unexpected number format: %', v_test_name, v_new_sub_num;
            v_failed := v_failed + 1;
        END IF;

        -- Clean up test subscription
        DELETE FROM subscription WHERE subscription_id = v_new_sub_id;
    END;

    -- ========================================================================
    -- TEST 5: D3 - Subscription status change history tracking
    -- ========================================================================
    v_test_name := 'TEST 5 (D3): Subscription status change history tracking';
    DECLARE
        v_hist_count INT;
    BEGIN
        -- Update subscription 5 status
        UPDATE subscription SET status = 'quotation' WHERE subscription_id = 5;

        SELECT COUNT(*) INTO v_hist_count 
        FROM subscription_status_history 
        WHERE subscription_id = 5 AND to_status = 'quotation';

        IF v_hist_count > 0 THEN
            RAISE NOTICE 'PASS: % - Status transition was logged in history.', v_test_name;
            v_passed := v_passed + 1;
        ELSE
            RAISE WARNING 'FAIL: % - Status transition was NOT recorded!', v_test_name;
            v_failed := v_failed + 1;
        END IF;

        -- Revert status
        UPDATE subscription SET status = 'draft' WHERE subscription_id = 5;
    END;

    -- ========================================================================
    -- TEST 6: D5 - Duplicate Invoice for same subscription & billing period
    -- ========================================================================
    v_test_name := 'TEST 6 (D5): Duplicate Invoice prevention (same subscription & period)';
    BEGIN
        INSERT INTO invoice (number, subscription_id, customer_id, billing_period, total, due_date, status)
        VALUES ('INV-TEST-DUP-01', 1, 1, '2026-10', 100.00, CURRENT_DATE + 15, 'draft');

        RAISE WARNING 'FAIL: % - Duplicate invoice period was allowed!', v_test_name;
        v_failed := v_failed + 1;
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'PASS: % - Duplicate billing period rejected by unique constraint.', v_test_name;
        v_passed := v_passed + 1;
    END;

    -- ========================================================================
    -- TEST 7: D5 - Refund limit enforcement (Refund > Payment amount)
    -- ========================================================================
    v_test_name := 'TEST 7 (D5): Refund limit enforcement trigger';
    BEGIN
        -- Payment 1 has amount 2000.00. Attempting to refund 5000.00 must fail.
        INSERT INTO refund (payment_id, invoice_id, amount, reason, status)
        VALUES (1, 1, 5000.00, 'Exorbitant over-refund attempt', 'requested');

        RAISE WARNING 'FAIL: % - Refund exceeding payment was allowed!', v_test_name;
        v_failed := v_failed + 1;
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%Refund limit exceeded%' THEN
            RAISE NOTICE 'PASS: % - Correctly blocked refund exceeding payment amount: %', v_test_name, SQLERRM;
            v_passed := v_passed + 1;
        ELSE
            RAISE WARNING 'FAIL: % - Unexpected error: %', v_test_name, SQLERRM;
            v_failed := v_failed + 1;
        END IF;
    END;

    -- ========================================================================
    -- TEST 8: D5 - Invoice auto-paid status trigger
    -- ========================================================================
    v_test_name := 'TEST 8 (D5): Invoice status transitions to paid when fully settled';
    DECLARE
        v_test_inv_id BIGINT;
        v_status_after VARCHAR(20);
    BEGIN
        -- Create a confirmed test invoice for Rs 500.00
        INSERT INTO invoice (number, subscription_id, customer_id, billing_period, total, due_date, status)
        VALUES ('INV-TEST-AUTO-PAID', NULL, 1, '2026-TEST-01', 500.00, CURRENT_DATE + 15, 'confirmed')
        RETURNING invoice_id INTO v_test_inv_id;

        -- Record payment of 500.00
        INSERT INTO payment (invoice_id, method, amount, note)
        VALUES (v_test_inv_id, 'card', 500.00, 'Full test settlement');

        -- Check if invoice status switched to 'paid'
        SELECT status INTO v_status_after FROM invoice WHERE invoice_id = v_test_inv_id;

        IF v_status_after = 'paid' THEN
            RAISE NOTICE 'PASS: % - Invoice successfully transitioned to paid automatically.', v_test_name;
            v_passed := v_passed + 1;
        ELSE
            RAISE WARNING 'FAIL: % - Invoice status is % instead of paid!', v_test_name, v_status_after;
            v_failed := v_failed + 1;
        END IF;

        -- Clean up test records
        DELETE FROM payment WHERE invoice_id = v_test_inv_id;
        DELETE FROM invoice WHERE invoice_id = v_test_inv_id;
    END;

    -- ========================================================================
    -- TEST 9: D5 - Atomic Discount counter function
    -- ========================================================================
    v_test_name := 'TEST 9 (D5): Atomic discount increment function';
    DECLARE
        v_atomic_ok BOOLEAN;
        v_used_before INT;
        v_used_after INT;
    BEGIN
        SELECT times_used INTO v_used_before FROM discount WHERE discount_id = 1;
        v_atomic_ok := fn_apply_discount_atomically(1);
        SELECT times_used INTO v_used_after FROM discount WHERE discount_id = 1;

        IF v_atomic_ok AND v_used_after = (v_used_before + 1) THEN
            RAISE NOTICE 'PASS: % - Atomic update succeeded (counter: % -> %)', v_test_name, v_used_before, v_used_after;
            v_passed := v_passed + 1;
        ELSE
            RAISE WARNING 'FAIL: % - Atomic discount counter update failed!', v_test_name;
            v_failed := v_failed + 1;
        END IF;

        -- Revert counter
        UPDATE discount SET times_used = v_used_before WHERE discount_id = 1;
    END;

    -- ========================================================================
    -- TEST 10: D9 - Audit log entry generation on payment update
    -- ========================================================================
    v_test_name := 'TEST 10 (D9): Audit log entry created on Payment update';
    DECLARE
        v_log_count INT;
    BEGIN
        UPDATE payment 
        SET note = 'Updated payment note for audit verification test' 
        WHERE payment_id = 3;

        SELECT COUNT(*) INTO v_log_count 
        FROM audit_log 
        WHERE entity = 'payment' AND entity_id = '3' AND action = 'UPDATE';

        IF v_log_count > 0 THEN
            RAISE NOTICE 'PASS: % - Audit log entry created successfully.', v_test_name;
            v_passed := v_passed + 1;
        ELSE
            RAISE WARNING 'FAIL: % - Audit log entry NOT created on payment update!', v_test_name;
            v_failed := v_failed + 1;
        END IF;
    END;

    -- ========================================================================
    -- TEST 11: D9 - Immutability of audit_log table (Block UPDATE/DELETE)
    -- ========================================================================
    v_test_name := 'TEST 11 (D9): Audit log immutability check (prevent DELETE)';
    BEGIN
        DELETE FROM audit_log WHERE log_id = 1;

        RAISE WARNING 'FAIL: % - Delete on audit_log was allowed!', v_test_name;
        v_failed := v_failed + 1;
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%audit_log is append-only%' THEN
            RAISE NOTICE 'PASS: % - Correctly blocked audit log tampering: %', v_test_name, SQLERRM;
            v_passed := v_passed + 1;
        ELSE
            RAISE WARNING 'FAIL: % - Unexpected error: %', v_test_name, SQLERRM;
            v_failed := v_failed + 1;
        END IF;
    END;

    -- ========================================================================
    -- SUMMARY REPORT
    -- ========================================================================
    RAISE NOTICE '---------------------------------------------------------';
    RAISE NOTICE ' TEST SUMMARY: % PASSED, % FAILED', v_passed, v_failed;
    RAISE NOTICE '---------------------------------------------------------';

    IF v_failed > 0 THEN
        RAISE EXCEPTION 'Verification test suite failed with % errors.', v_failed;
    END IF;
END $$;
