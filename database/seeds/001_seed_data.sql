-- Seed: 001_seed_data.sql
-- Description: Complete seed data covering all roles, statuses, and domain entities
-- Scope: D7 - Seed Data (Brightloop SMS)

BEGIN;

-- Set current application context for audit logging
SET LOCAL app.current_user_id = '1';

-- ============================================================================
-- 1. AUTH ACCOUNTS (1 Admin, 2 Staff, 5 Customers)
-- Password for all accounts: Brightloop@2026!
-- Bcrypt hash ($2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u)
-- ============================================================================

INSERT INTO auth (id, email, password_hash, role, is_active, last_login)
OVERRIDING SYSTEM VALUE VALUES
(1, 'admin@brightloop.io', '$2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u', 'admin', true, CURRENT_TIMESTAMP - INTERVAL '1 hour'),
(2, 'sarah.ops@brightloop.io', '$2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u', 'staff', true, CURRENT_TIMESTAMP - INTERVAL '4 hours'),
(3, 'raj.finance@brightloop.io', '$2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u', 'staff', true, CURRENT_TIMESTAMP - INTERVAL '1 day'),
(4, 'contact@acmecorp.com', '$2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u', 'customer', true, CURRENT_TIMESTAMP - INTERVAL '2 days'),
(5, 'billing@nexatech.co', '$2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u', 'customer', true, CURRENT_TIMESTAMP - INTERVAL '3 days'),
(6, 'ops@bluehorizon.net', '$2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u', 'customer', true, CURRENT_TIMESTAMP - INTERVAL '5 days'),
(7, 'finance@quantedge.ai', '$2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u', 'customer', true, CURRENT_TIMESTAMP - INTERVAL '6 days'),
(8, 'accounts@solariahealth.org', '$2b$12$e0MYzXv9kL7rY1wYv6gGkO6i4hT5dC5wP8aU0nL6cZ8jU3sO2qF3u', 'customer', true, CURRENT_TIMESTAMP - INTERVAL '10 days');

-- Reset identity sequence
SELECT SETVAL(pg_get_serial_sequence('auth', 'id'), (SELECT MAX(id) FROM auth));


-- ============================================================================
-- 2. STAFF PROFILES (1 Admin, 2 Staff)
-- ============================================================================

INSERT INTO staff (staff_id, auth_id, name, department, created_by, is_active)
OVERRIDING SYSTEM VALUE VALUES
(1, 1, 'Chief Administrator', 'Executive Leadership', NULL, true),
(2, 2, 'Sarah Jenkins', 'Operations & Sales', 1, true),
(3, 3, 'Rajesh Patel', 'Finance & Billing', 1, true);

SELECT SETVAL(pg_get_serial_sequence('staff', 'staff_id'), (SELECT MAX(staff_id) FROM staff));


-- ============================================================================
-- 3. CUSTOMER PROFILES (5 Customers)
-- ============================================================================

INSERT INTO customer (customer_id, auth_id, name, phone, address, company, is_active)
OVERRIDING SYSTEM VALUE VALUES
(1, 4, 'John Acme', '+1-555-0100', '100 Industrial Parkway, Austin, TX', 'Acme Corporation', true),
(2, 5, 'Elena Rostova', '+1-555-0200', '450 Innovation Way, San Francisco, CA', 'NexaTech Solutions', true),
(3, 6, 'Marcus Brody', '+1-555-0300', '12 Harbour View, Seattle, WA', 'BlueHorizon Logistics', true),
(4, 7, 'Dr. Aris Thorne', '+1-555-0400', '77 Financial Plaza, New York, NY', 'QuantEdge Analytics', true),
(5, 8, 'Claire Vance', '+1-555-0500', '320 Medical Center Dr, Boston, MA', 'Solaria Health Systems', true);

SELECT SETVAL(pg_get_serial_sequence('customer', 'customer_id'), (SELECT MAX(customer_id) FROM customer));


-- ============================================================================
-- 4. PRODUCTS & VARIANTS (4 Products with Multiple Variants)
-- ============================================================================

INSERT INTO product (product_id, name, type, sales_price, cost_price, notes, is_active)
OVERRIDING SYSTEM VALUE VALUES
(1, 'BrightSuite ERP Platform', 'software', 499.00, 150.00, 'Cloud-based subscription ERP core', true),
(2, 'Dedicated Support Tier', 'service', 250.00, 80.00, 'Priority SLA technical support tier', true),
(3, 'Cloud Storage Volume', 'add-on', 100.00, 25.00, 'Scalable high-availability cloud storage expansion', true),
(4, 'Compliance & Security Audit', 'service', 1200.00, 400.00, 'Continuous automated SOC2 and regulatory checks', true);

SELECT SETVAL(pg_get_serial_sequence('product', 'product_id'), (SELECT MAX(product_id) FROM product));

-- Product Variants (Spec 4.2 example: Odoo brand adds 560 to base price)
INSERT INTO product_variant (variant_id, product_id, attribute, value, extra_price, is_active)
OVERRIDING SYSTEM VALUE VALUES
(1, 1, 'Edition', 'Standard Edition', 0.00, true),
(2, 1, 'Edition', 'Odoo Enterprise Suite', 560.00, true),
(3, 2, 'SLA', 'Business Hours (9x5)', 0.00, true),
(4, 2, 'SLA', '24x7 Mission Critical', 450.00, true),
(5, 3, 'Capacity', '100 GB Vault', 0.00, true),
(6, 3, 'Capacity', '1 TB High-Speed Tier', 300.00, true),
(7, 4, 'Compliance', 'SOC2 Baseline', 0.00, true),
(8, 4, 'Compliance', 'HIPAA & Financial Grade', 800.00, true);

SELECT SETVAL(pg_get_serial_sequence('product_variant', 'variant_id'), (SELECT MAX(variant_id) FROM product_variant));


-- ============================================================================
-- 5. PLANS (3 Plans: Monthly, Weekly, Yearly)
-- ============================================================================

INSERT INTO plan (plan_id, name, price, billing_period, min_quantity, start_date, end_date, auto_close, allow_early_close, allow_pause, allow_renewal, is_active)
OVERRIDING SYSTEM VALUE VALUES
(1, 'Starter Monthly', 499.00, 'monthly', 1, '2026-01-01', NULL, false, true, true, true, true),
(2, 'Agile Weekly', 150.00, 'weekly', 1, '2026-01-01', NULL, false, true, true, true, true),
(3, 'Enterprise Annual', 4990.00, 'yearly', 1, '2026-01-01', NULL, false, false, false, true, true);

SELECT SETVAL(pg_get_serial_sequence('plan', 'plan_id'), (SELECT MAX(plan_id) FROM plan));


-- ============================================================================
-- 6. TAXES (2 Taxes)
-- ============================================================================

INSERT INTO tax (tax_id, name, rate, applies_to, is_active)
OVERRIDING SYSTEM VALUE VALUES
(1, 'GST 18%', 18.00, 'all', true),
(2, 'Tech VAT 5%', 5.00, 'software', true);

SELECT SETVAL(pg_get_serial_sequence('tax', 'tax_id'), (SELECT MAX(tax_id) FROM tax));


-- ============================================================================
-- 7. DISCOUNTS (2 Discounts) & PRODUCT MAPPINGS
-- ============================================================================

INSERT INTO discount (discount_id, name, code, type, value, scope, product_id, min_amount, min_qty, start_date, end_date, usage_limit, times_used, is_active)
OVERRIDING SYSTEM VALUE VALUES
(1, 'Volume Team Discount', 'VOL10', 'percent', 10.00, 'subscription', NULL, 500.00, 2, '2026-01-01', '2026-12-31', 100, 4, true),
(2, 'New Customer Software Voucher', 'WELCOME500', 'fixed', 500.00, 'product', 1, 1000.00, 1, '2026-01-01', '2026-12-31', 50, 2, true);

SELECT SETVAL(pg_get_serial_sequence('discount', 'discount_id'), (SELECT MAX(discount_id) FROM discount));

-- Many-to-many relationship mapping
INSERT INTO discount_product (discount_id, product_id) VALUES
(2, 1);


-- ============================================================================
-- 8. QUOTATIONS (Templates & Customer Quotes)
-- ============================================================================

-- Quotation 1: Reusable Template
INSERT INTO quotation (quotation_id, number, is_template, customer_id, plan_id, validity_days, status, created_by, notes)
OVERRIDING SYSTEM VALUE VALUES
(1, 'QT-TMPL-ENTERPRISE', true, NULL, 3, 60, 'accepted', 2, 'Standard Enterprise Reusable Sales Template');

INSERT INTO quotation_line (line_id, quotation_id, product_id, variant_id, quantity, unit_price, tax_id, amount)
OVERRIDING SYSTEM VALUE VALUES
(1, 1, 1, 2, 1, 1059.00, 1, 1059.00),
(2, 1, 2, 4, 1, 700.00, 1, 700.00);

-- Quotation 2: Active quote for Customer 2
INSERT INTO quotation (quotation_id, number, is_template, customer_id, plan_id, validity_days, status, created_by, notes)
OVERRIDING SYSTEM VALUE VALUES
(2, 'QT-2026-000002', false, 2, 1, 30, 'accepted', 2, 'Direct quote accepted by NexaTech');

INSERT INTO quotation_line (line_id, quotation_id, product_id, variant_id, quantity, unit_price, tax_id, amount)
OVERRIDING SYSTEM VALUE VALUES
(3, 2, 1, 1, 2, 499.00, 1, 998.00);

SELECT SETVAL(pg_get_serial_sequence('quotation', 'quotation_id'), (SELECT MAX(quotation_id) FROM quotation));
SELECT SETVAL(pg_get_serial_sequence('quotation_line', 'line_id'), (SELECT MAX(line_id) FROM quotation_line));


-- ============================================================================
-- 9. SUBSCRIPTIONS (Covering ALL 6 Statuses: draft, quotation, confirmed, active, paused, closed)
-- ============================================================================

INSERT INTO subscription (subscription_id, number, customer_id, plan_id, quotation_id, start_date, expiry_date, next_billing_date, payment_terms, status)
OVERRIDING SYSTEM VALUE VALUES
-- 1. Active subscription (Customer 1 - Acme Corp)
(1, 'SUB-2026-000001', 1, 1, NULL, '2026-01-01', '2026-12-31', '2026-11-01', 'Net 15', 'active'),
-- 2. Confirmed subscription (Customer 2 - NexaTech)
(2, 'SUB-2026-000002', 2, 1, 2, '2026-11-01', '2027-10-31', '2026-11-01', 'Immediate', 'confirmed'),
-- 3. Paused subscription (Customer 3 - BlueHorizon)
(3, 'SUB-2026-000003', 3, 2, NULL, '2026-02-01', '2026-12-31', '2026-11-15', 'Immediate', 'paused'),
-- 4. Closed subscription (Customer 4 - QuantEdge)
(4, 'SUB-2026-000004', 4, 1, NULL, '2026-01-01', '2026-06-30', '2026-07-01', 'Net 30', 'closed'),
-- 5. Draft subscription (Customer 5 - Solaria Health)
(5, 'SUB-2026-000005', 5, 3, NULL, '2026-11-15', '2027-11-14', '2026-11-15', 'Net 30', 'draft'),
-- 6. Quotation stage subscription (Customer 1 - Acme Corp)
(6, 'SUB-2026-000006', 1, 3, 1, '2026-12-01', '2027-11-30', '2026-12-01', 'Net 30', 'quotation');

SELECT SETVAL(pg_get_serial_sequence('subscription', 'subscription_id'), (SELECT MAX(subscription_id) FROM subscription));

-- Subscription Lines
INSERT INTO subscription_line (line_id, subscription_id, product_id, variant_id, quantity, unit_price, tax_id, amount)
OVERRIDING SYSTEM VALUE VALUES
(1, 1, 1, 2, 2, 1059.00, 1, 2118.00), -- SUB 1: 2x ERP Odoo Enterprise
(2, 1, 2, 4, 1, 700.00, 1, 700.00),   -- SUB 1: 1x 24/7 Support
(3, 2, 1, 1, 1, 499.00, 1, 499.00),   -- SUB 2: 1x ERP Standard
(4, 3, 3, 6, 2, 400.00, 1, 800.00),   -- SUB 3: 2x 1TB Storage
(5, 4, 1, 1, 1, 499.00, 1, 499.00),   -- SUB 4: 1x ERP Standard
(6, 5, 4, 8, 1, 2000.00, 1, 2000.00); -- SUB 5: 1x Compliance HIPAA

SELECT SETVAL(pg_get_serial_sequence('subscription_line', 'line_id'), (SELECT MAX(line_id) FROM subscription_line));


-- ============================================================================
-- 10. INVOICES (Covering ALL 4 Statuses: draft, confirmed, paid, cancelled)
-- ============================================================================

INSERT INTO invoice (invoice_id, number, subscription_id, customer_id, billing_period, subtotal, discount_total, tax_total, total, issue_date, due_date, status, notes)
OVERRIDING SYSTEM VALUE VALUES
-- Invoice 1: Paid (Sub 1, Period 2026-10)
(1, 'INV-2026-000001', 1, 1, '2026-10', 2818.00, 281.80, 456.52, 2992.72, '2026-10-01', '2026-10-15', 'paid', 'Monthly recurring charge for October 2026'),
-- Invoice 2: Confirmed / Overdue with partial payment (Sub 1, Period 2026-09)
(2, 'INV-2026-000002', 1, 1, '2026-09', 2818.00, 0.00, 507.24, 3325.24, '2026-09-01', '2026-09-15', 'confirmed', 'September billing - currently overdue with partial balance'),
-- Invoice 3: Draft (Sub 2, Period 2026-11)
(3, 'INV-2026-000003', 2, 2, '2026-11', 499.00, 0.00, 89.82, 588.82, '2026-10-31', '2026-11-15', 'draft', 'Draft invoice generated for upcoming cycle'),
-- Invoice 4: Cancelled (Sub 4, Period 2026-07)
(4, 'INV-2026-000004', 4, 4, '2026-07', 499.00, 0.00, 89.82, 588.82, '2026-07-01', '2026-07-15', 'cancelled', 'Voided due to early closure agreement');

SELECT SETVAL(pg_get_serial_sequence('invoice', 'invoice_id'), (SELECT MAX(invoice_id) FROM invoice));

-- Invoice Lines
INSERT INTO invoice_line (line_id, invoice_id, product_id, variant_id, description, quantity, unit_price, discount_amount, tax_id, tax_amount, amount)
OVERRIDING SYSTEM VALUE VALUES
(1, 1, 1, 2, 'BrightSuite ERP Platform (Odoo Enterprise Suite)', 2, 1059.00, 211.80, 1, 343.30, 2248.90),
(2, 1, 2, 4, 'Dedicated Support Tier (24x7 Mission Critical)', 1, 700.00, 70.00, 1, 113.22, 743.82),
(3, 2, 1, 2, 'BrightSuite ERP Platform (Odoo Enterprise Suite)', 2, 1059.00, 0.00, 1, 381.24, 2499.24),
(4, 2, 2, 4, 'Dedicated Support Tier (24x7 Mission Critical)', 1, 700.00, 0.00, 1, 126.00, 826.00),
(5, 3, 1, 1, 'BrightSuite ERP Platform (Standard Edition)', 1, 499.00, 0.00, 1, 89.82, 588.82),
(6, 4, 1, 1, 'BrightSuite ERP Platform (Standard Edition)', 1, 499.00, 0.00, 1, 89.82, 588.82);

SELECT SETVAL(pg_get_serial_sequence('invoice_line', 'line_id'), (SELECT MAX(line_id) FROM invoice_line));


-- ============================================================================
-- 11. PAYMENTS (Full, Multiple, Partial)
-- ============================================================================

INSERT INTO payment (payment_id, invoice_id, method, amount, payment_date, note, recorded_by)
OVERRIDING SYSTEM VALUE VALUES
-- Invoice 1: Full settlement (2992.72 paid across two transactions)
(1, 1, 'bank_transfer', 2000.00, '2026-10-05 10:30:00+00', 'Wire transfer tranche 1 - Ref WT-99382', 3),
(2, 1, 'card', 992.72, '2026-10-06 14:15:00+00', 'Corporate Amex final balance payment', 3),
-- Invoice 2: Partial payment (1500.00 paid towards 3325.24, leaving open balance)
(3, 2, 'upi', 1500.00, '2026-09-10 11:00:00+00', 'UPI payment ref UPI/99281/TXN', 2);

SELECT SETVAL(pg_get_serial_sequence('payment', 'payment_id'), (SELECT MAX(payment_id) FROM payment));


-- ============================================================================
-- 12. REFUNDS (Covering ALL 4 Statuses: requested, approved, processed, rejected)
-- Payment 1 has amount 2000.00; refund of 250.00 is processed.
-- ============================================================================

INSERT INTO refund (refund_id, payment_id, invoice_id, amount, reason, status, processed_date, approved_by)
OVERRIDING SYSTEM VALUE VALUES
-- Processed refund (at least 1 processed per D7 spec)
(1, 1, 1, 250.00, 'Pro-rata credit for 2-hour scheduled maintenance outage', 'processed', '2026-10-08 16:00:00+00', 1),
-- Requested refund pending review
(2, 3, 2, 150.00, 'Billing adjustment requested on tax calculation', 'requested', NULL, NULL),
-- Approved refund ready for gateway payout
(3, 1, 1, 100.00, 'Goodwill credit for onboarding delay', 'approved', NULL, 1),
-- Rejected refund
(4, 3, 2, 500.00, 'Refund claim outside policy limits', 'rejected', NULL, 1);

SELECT SETVAL(pg_get_serial_sequence('refund', 'refund_id'), (SELECT MAX(refund_id) FROM refund));

-- Recalculate invoice statuses to guarantee synchronization
SELECT fn_recalculate_invoice_payment_status(1);
SELECT fn_recalculate_invoice_payment_status(2);
SELECT fn_recalculate_invoice_payment_status(3);
SELECT fn_recalculate_invoice_payment_status(4);

-- Refresh the materialized summary view with the fresh seed data
CALL sp_refresh_dashboard_summary();

COMMIT;
