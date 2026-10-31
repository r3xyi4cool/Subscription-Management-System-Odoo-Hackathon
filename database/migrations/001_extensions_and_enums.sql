-- Migration: 001_extensions_and_enums.sql
-- Description: Core extensions, helper functions, and numbering sequences
-- Scope: Brightloop Subscription Management System (SMS) - Member 3 (Database)

-- Enable citext for case-insensitive email handling
CREATE EXTENSION IF NOT EXISTS citext;

-- Enable pgcrypto for password hashing and cryptographic helpers if needed
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Set consistent timezone
SET timezone = 'UTC';

-- Sequences for generating business document numbers
-- Format: SUB-YYYY-000001, INV-YYYY-000001, QT-YYYY-000001
CREATE SEQUENCE IF NOT EXISTS subscription_number_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS invoice_number_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS quotation_number_seq START WITH 1 INCREMENT BY 1;

-- Generator function for Subscription Number
CREATE OR REPLACE FUNCTION fn_generate_subscription_number()
RETURNS VARCHAR(50) AS $$
DECLARE
    v_year TEXT;
    v_seq_val BIGINT;
BEGIN
    v_year := TO_CHAR(CURRENT_DATE, 'YYYY');
    v_seq_val := NEXTVAL('subscription_number_seq');
    RETURN 'SUB-' || v_year || '-' || LPAD(v_seq_val::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

-- Generator function for Invoice Number
CREATE OR REPLACE FUNCTION fn_generate_invoice_number()
RETURNS VARCHAR(50) AS $$
DECLARE
    v_year TEXT;
    v_seq_val BIGINT;
BEGIN
    v_year := TO_CHAR(CURRENT_DATE, 'YYYY');
    v_seq_val := NEXTVAL('invoice_number_seq');
    RETURN 'INV-' || v_year || '-' || LPAD(v_seq_val::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

-- Generator function for Quotation Number
CREATE OR REPLACE FUNCTION fn_generate_quotation_number()
RETURNS VARCHAR(50) AS $$
DECLARE
    v_year TEXT;
    v_seq_val BIGINT;
BEGIN
    v_year := TO_CHAR(CURRENT_DATE, 'YYYY');
    v_seq_val := NEXTVAL('quotation_number_seq');
    RETURN 'QT-' || v_year || '-' || LPAD(v_seq_val::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

-- Helper trigger function to update updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
