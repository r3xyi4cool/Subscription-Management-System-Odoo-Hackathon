-- Script: dashboard_views.sql
-- Description: Standalone reference for all dashboard views, MRR/ARR logic, and KPI queries
-- Scope: D6 - Performance and Reporting (Brightloop SMS)

-- 1. Active Subscriptions & MRR Normalization View
-- Converts all billing periods to a unified monthly metric according to Spec Section 11.3:
-- Daily: price * 30
-- Weekly: (price * 52) / 12
-- Monthly: price * 1
-- Yearly: price / 12
CREATE OR REPLACE VIEW v_active_subscriptions AS
SELECT 
    s.subscription_id,
    s.number,
    s.customer_id,
    c.name AS customer_name,
    s.plan_id,
    p.name AS plan_name,
    p.billing_period,
    p.price AS plan_price,
    s.start_date,
    s.expiry_date,
    s.next_billing_date,
    s.payment_terms,
    CASE p.billing_period
        WHEN 'daily'   THEN ROUND(p.price * 30.0, 2)
        WHEN 'weekly'  THEN ROUND((p.price * 52.0) / 12.0, 2)
        WHEN 'monthly' THEN ROUND(p.price, 2)
        WHEN 'yearly'  THEN ROUND(p.price / 12.0, 2)
        ELSE 0.00
    END AS normalized_mrr
FROM subscription s
JOIN plan p ON s.plan_id = p.plan_id
JOIN customer c ON s.customer_id = c.customer_id
WHERE s.status = 'active';

-- 2. Overdue Invoices View
-- Invoices in 'confirmed' status past due_date with unpaid balances
CREATE OR REPLACE VIEW v_overdue_invoices AS
SELECT 
    i.invoice_id,
    i.number AS invoice_number,
    i.customer_id,
    c.name AS customer_name,
    c.company AS customer_company,
    i.subscription_id,
    i.total,
    COALESCE(p_agg.total_paid, 0.00) AS total_paid,
    (i.total - COALESCE(p_agg.total_paid, 0.00)) AS balance_due,
    i.issue_date,
    i.due_date,
    (CURRENT_DATE - i.due_date) AS days_overdue
FROM invoice i
JOIN customer c ON i.customer_id = c.customer_id
LEFT JOIN (
    SELECT invoice_id, SUM(amount) AS total_paid
    FROM payment
    GROUP BY invoice_id
) p_agg ON i.invoice_id = p_agg.invoice_id
WHERE i.status = 'confirmed' 
  AND i.due_date < CURRENT_DATE
  AND (i.total - COALESCE(p_agg.total_paid, 0.00)) > 0;

-- 3. Live Dashboard KPI Summary View
CREATE OR REPLACE VIEW v_dashboard_kpis AS
WITH sub_stats AS (
    SELECT 
        COUNT(*) FILTER (WHERE status = 'active') AS active_subscriptions,
        COUNT(*) FILTER (WHERE status = 'closed') AS closed_subscriptions,
        COUNT(*) AS total_subscriptions
    FROM subscription
),
mrr_calc AS (
    SELECT COALESCE(SUM(normalized_mrr), 0.00) AS total_mrr
    FROM v_active_subscriptions
),
rev_stats AS (
    SELECT 
        COALESCE(SUM(p.amount), 0.00) AS gross_collected,
        COALESCE(SUM(r.amount) FILTER (WHERE r.status = 'processed'), 0.00) AS total_refunded
    FROM payment p
    LEFT JOIN refund r ON p.payment_id = r.payment_id
),
inv_stats AS (
    SELECT 
        COALESCE(SUM(total) FILTER (WHERE status != 'cancelled'), 0.00) AS total_invoiced,
        COALESCE(SUM(total) FILTER (WHERE status = 'confirmed'), 0.00) AS open_invoiced
    FROM invoice
),
overdue_stats AS (
    SELECT 
        COUNT(*) AS overdue_count,
        COALESCE(SUM(balance_due), 0.00) AS overdue_balance
    FROM v_overdue_invoices
)
SELECT 
    sub_stats.active_subscriptions,
    (rev_stats.gross_collected - rev_stats.total_refunded) AS net_revenue_collected,
    GREATEST(0.00, inv_stats.open_invoiced - (rev_stats.gross_collected - rev_stats.total_refunded)) AS amount_owed,
    overdue_stats.overdue_count AS overdue_invoice_count,
    overdue_stats.overdue_balance AS overdue_amount,
    mrr_calc.total_mrr AS mrr,
    ROUND(mrr_calc.total_mrr * 12.0, 2) AS arr,
    CASE 
        WHEN (sub_stats.active_subscriptions + sub_stats.closed_subscriptions) > 0 
        THEN ROUND((sub_stats.closed_subscriptions::NUMERIC / (sub_stats.active_subscriptions + sub_stats.closed_subscriptions)) * 100.0, 2)
        ELSE 0.00 
    END AS churn_rate_percent,
    CASE 
        WHEN inv_stats.total_invoiced > 0 
        THEN ROUND(((rev_stats.gross_collected - rev_stats.total_refunded) / inv_stats.total_invoiced) * 100.0, 2)
        ELSE 0.00 
    END AS collection_rate_percent,
    CURRENT_TIMESTAMP AS computed_at
FROM sub_stats, mrr_calc, rev_stats, inv_stats, overdue_stats;
