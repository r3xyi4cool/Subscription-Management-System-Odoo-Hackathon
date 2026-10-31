-- Migration: 002_account_tables.sql
-- Description: Core account tables: Auth, Customer, and Staff
-- Scope: D1 - Account Tables (Brightloop SMS)

-- 1. Auth table
-- Stores authentication credentials and role assignments.
-- Password hash must use strong algorithm (bcrypt/argon2). Plain text is forbidden.
CREATE TABLE IF NOT EXISTS auth (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email CITEXT NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    reset_token VARCHAR(255),
    reset_expiry TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_auth_email UNIQUE (email),
    CONSTRAINT chk_auth_role CHECK (role IN ('admin', 'staff', 'customer')),
    CONSTRAINT chk_reset_expiry CHECK (reset_expiry IS NULL OR reset_expiry > created_at)
);

CREATE TRIGGER trg_auth_updated_at
BEFORE UPDATE ON auth
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 2. Staff table
-- 1:1 relationship with Auth for internal operators (Admin and Staff).
CREATE TABLE IF NOT EXISTS staff (
    staff_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    auth_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    created_by BIGINT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_staff_auth UNIQUE (auth_id),
    CONSTRAINT fk_staff_auth FOREIGN KEY (auth_id) REFERENCES auth(id) ON DELETE CASCADE,
    CONSTRAINT fk_staff_created_by FOREIGN KEY (created_by) REFERENCES staff(staff_id) ON DELETE SET NULL
);

CREATE TRIGGER trg_staff_updated_at
BEFORE UPDATE ON staff
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- 3. Customer table
-- 1:1 relationship with Auth for external portal subscribers.
CREATE TABLE IF NOT EXISTS customer (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    auth_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    company VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_customer_auth UNIQUE (auth_id),
    CONSTRAINT fk_customer_auth FOREIGN KEY (auth_id) REFERENCES auth(id) ON DELETE CASCADE
);

CREATE TRIGGER trg_customer_updated_at
BEFORE UPDATE ON customer
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Comments for documentation integrity
COMMENT ON TABLE auth IS 'Central authentication table storing email, credentials, and RBAC roles.';
COMMENT ON COLUMN auth.email IS 'Case-insensitive unique email address.';
COMMENT ON COLUMN auth.password_hash IS 'Cryptographic hash of password (bcrypt or argon2).';
COMMENT ON TABLE staff IS 'Internal company personnel linked 1:1 with Auth.';
COMMENT ON TABLE customer IS 'External subscription customers linked 1:1 with Auth.';
