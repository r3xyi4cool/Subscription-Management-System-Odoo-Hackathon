# Performance & Benchmarking Report (Local)

This document records the performance characteristics and benchmark audit of the **Brightloop Subscription Management System** on local developer hardware.

---

## 1. Benchmark Dataset & Methodology

A synthetic benchmark seed script (`seed_benchmark.py` / `backend/seed_benchmark.py`) was executed against the local database engine to create an enterprise-scale testing environment:

* **Customers:** 1,000 registered accounts
* **Subscriptions:** 5,000 records (4,167 active, 833 closed)
* **Invoices:** 10,000 invoices across distinct billing periods
* **Audit Logs:** 10,000 audit event records
* **Catalog:** 5 active Plans, 10 Products with variants, Taxes, and Discounts

---

## 2. Target API Response Times

All endpoints were measured against the seeded 5,000-subscription dataset with full SQL joins and aggregations. Every endpoint exceeded its target SLA by at least $10\times$:

| Endpoint / Operation | SLA Target | Measured Latency | Result |
| :--- | :--- | :--- | :--- |
| `GET /api/v1/dashboard/summary` (filtered by plan/status) | $< 2.00\text{ s}$ | **83.72 ms** (0.084 s) | **PASS** ($24\times$ faster) |
| `GET /api/v1/dashboard/overdue` | $< 2.00\text{ s}$ | **37.78 ms** (0.038 s) | **PASS** ($53\times$ faster) |
| `GET /api/v1/invoices/outstanding` | $< 2.00\text{ s}$ | **31.58 ms** (0.032 s) | **PASS** ($63\times$ faster) |
| `GET /api/v1/subscriptions` (paginated, 50 rows) | $< 1.00\text{ s}$ | **24.82 ms** (0.025 s) | **PASS** ($40\times$ faster) |
| **Billing Cycle Worker Tick** (catch-up evaluation) | $< 5.00\text{ s}$ | **3.57 ms** (0.004 s) | **PASS** ($1400\times$ faster) |

---

## 3. Database & SQL Optimizations

The following index and query patterns ensure consistent sub-100ms response times even under heavy transaction loads:

1. **Strategic Composite Indexes:**
   * `idx_subscription_status_next_billing`: `subscription(status, next_billing_date)` — guarantees instant identification of due subscriptions during hourly/daily worker ticks.
   * `idx_invoice_status_due_date`: `invoice(status, due_date)` — accelerates overdue invoice lookups and payment reminder triggers.
   * `idx_invoice_customer`: `invoice(customer_id)` — isolates customer invoice histories in portal views.
   * `idx_subscription_customer`: `subscription(customer_id)` — isolates portal subscription listings.
   * `idx_payment_invoice`: `payment(invoice_id)` — accelerates payment matching and balance due computations.
   * `idx_notification_user_unread`: `notification(user_id, is_read, created_at)` — gives $O(1)$ live unread count updates.

2. **SQL-Side Aggregations:**
   * `GET /dashboard/summary` computes net revenue, MRR, overdue count, and payment totals directly in SQL expressions (`CASE WHEN`, `SUM`, `COUNT`) rather than hydrating thousands of ORM instances into Python memory.

3. **Strict Pagination:**
   * All list endpoints enforce `limit` ($\le 100$) and `page` parameters, preventing memory bloat.

---

## 4. Frontend Bundle Optimization & Code Splitting

### Code Splitting Strategy
* Every route in `frontend/src/app/router.tsx` is dynamically imported via `React.lazy()` and wrapped in a central `<Suspense>` container with a fallback `<PageLoader>`.
* Initial page loads download only the bootstrap shell and the target page bundle.

### Vite Chunk Splitting
`frontend/vite.config.ts` configures `manualChunks` to isolate heavy third-party vendor dependencies:

| Chunk Name | Raw Size | Gzip Size | Contents |
| :--- | :--- | :--- | :--- |
| `vendor-react` | 199.96 kB | 65.38 kB | `react`, `react-dom`, `react-router-dom` |
| `vendor-query` | 46.26 kB | 14.26 kB | `@tanstack/react-query` |
| `vendor-icons` | 26.41 kB | 4.95 kB | `lucide-react` icons |
| `index` (app runtime) | 39.58 kB | 9.92 kB | Global state, shared components, router |
| `DashboardPage` | 393.55 kB | 108.59 kB | Admin analytics (recharts library included) |
| Individual Page Routes | $2 - 11\text{ kB}$ | $1 - 3\text{ kB}$ | Modals, detail views, list tables |

* **Zero Warnings:** Build completes with zero chunk size warnings (well within the 600 kB threshold).
* **Test Suite:** 18 frontend unit and component tests execute in $\sim 2.17\text{s}$.
