-- Migration: 007_performance_indexes_views.sql
-- Description: Performance indexes, summary views, and materialized dashboard view
-- Scope: D6 - Performance (<2 second targets) (Brightloop SMS)

-- ============================================================================
-- 1. PERFORMANCE INDEXES (D6 & Spec 12.3)
-- Targeted composite and foreign-key indexes for high-throughput queries
-- ============================================================================

-- Fast lookup for the billing-day cron job: finds active subscriptions due for invoicing
CREATE INDEX IF NOT EXISTS idx_subscription_status_next_billing 
ON subscription (status, next_billing_date);

-- Fast lookup for overdue invoice queries and dunning jobs
CREATE INDEX IF NOT EXISTS idx_invoice_status_due_date 
ON invoice (status, due_date);

-- Customer portal scoping: filters invoices by customer instantly
CREATE INDEX IF NOT EXISTS idx_invoice_customer_id 
ON invoice (customer_id);

-- Payment reconciliation and invoice balance calculation
CREATE INDEX IF NOT EXISTS idx_payment_invoice_id 
ON payment (invoice_id);

-- Customer portal scoping: filters subscriptions by customer
CREATE INDEX IF NOT EXISTS idx_subscription_customer_id 
ON subscription (customer_id);

-- Additional high-value foreign key and lookup indexes
CREATE INDEX IF NOT EXISTS idx_subscription_plan_id ON subscription (plan_id);
CREATE INDEX IF NOT EXISTS idx_subscription_line_subscription_id ON subscription_line (subscription_id);
CREATE INDEX IF NOT EXISTS idx_invoice_line_invoice_id ON invoice_line (invoice_id);
CREATE INDEX IF NOT EXISTS idx_refund_payment_id ON refund (payment_id);
CREATE INDEX IF NOT EXISTS idx_refund_invoice_id ON refund (invoice_id);
CREATE INDEX IF NOT EXISTS idx_quotation_customer_id ON quotation (customer_id);
CREATE INDEX IF NOT EXISTS idx_product_variant_product_id ON product_variant (product_id);
CREATE INDEX IF NOT EXISTS idx_auth_role_active ON auth (role, is_active);


-- ============================================================================
-- 2. DASHBOARD SUMMARY VIEWS (D6)
-- Provides instant metrics: Active Count, Revenue, Amount Owed, Overdue, MRR, ARR, Churn, Collection Rate
-- ============================================================================

-- Active Subscriptions with plan normalization for MRR
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
    -- Calculate normalized Monthly Recurring Revenue (MRR) based on Section 11.3
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

-- Overdue Invoices View
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

-- Live KPI Summary View (Instant computation)
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
    -- Churn rate: closed subscriptions / total ever created (or 0 if none)
    CASE 
        WHEN (sub_stats.active_subscriptions + sub_stats.closed_subscriptions) > 0 
        THEN ROUND((sub_stats.closed_subscriptions::NUMERIC / (sub_stats.active_subscriptions + sub_stats.closed_subscriptions)) * 100.0, 2)
        ELSE 0.00 
    END AS churn_rate_percent,
    -- Collection rate: net collected / total invoiced (or 0 if no invoices)
    CASE 
        WHEN inv_stats.total_invoiced > 0 
        THEN ROUND(((rev_stats.gross_collected - rev_stats.total_refunded) / inv_stats.total_invoiced) * 100.0, 2)
        ELSE 0.00 
    END AS collection_rate_percent,
    CURRENT_TIMESTAMP AS computed_at
FROM sub_stats, mrr_calc, rev_stats, inv_stats, overdue_stats;


-- ============================================================================
-- 3. PRE-AGGREGATED MATERIALIZED VIEW & REFRESH STRATEGY (D6)
-- Ensures O(1) instantaneous responses under heavy dashboard load
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_summary AS
SELECT 
    1 AS summary_id,
    active_subscriptions,
    net_revenue_collected,
    amount_owed,
    overdue_invoice_count,
    overdue_amount,
    mrr,
    arr,
    churn_rate_percent,
    collection_rate_percent,
    computed_at
FROM v_dashboard_kpis;

-- Unique index required for REFRESH MATERIALIZED VIEW CONCURRENTLY (non-blocking)
CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_dashboard_summary 
ON mv_dashboard_summary (summary_id);

-- Refresh procedure callable by cron, background worker, or triggers
CREATE OR REPLACE PROCEDURE sp_refresh_dashboard_summary()
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_summary;
END;
$$;

COMMENT ON VIEW v_active_subscriptions IS 'Active subscriptions with normalized monthly recurring revenue calculations.';
COMMENT ON VIEW v_overdue_invoices IS 'Confirmed invoices that have passed their due date with outstanding balances.';
COMMENT ON VIEW v_dashboard_kpis IS 'Real-time KPI aggregation view for the Brightloop executive dashboard.';
COMMENT ON MATERIALIZED VIEW mv_dashboard_summary IS 'Pre-aggregated snapshot view for sub-millisecond dashboard queries.';
COMMENT ON PROCEDURE sp_refresh_dashboard_summary IS 'Refreshes the materialized dashboard summary view concurrently without locking reads.';
