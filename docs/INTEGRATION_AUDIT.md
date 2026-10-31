# Integration Audit Report: Subscription Management System (SMS)

**Document Version:** 1.0.0  
**Target Branch:** `integration/cleanup`  
**Auditor:** Senior Integration Engineer & Code Auditor  
**Date:** October 31, 2026  
**Reference Document:** `/features.md` (Version 1.0 - Brightloop Software)

---

## Executive Summary

A comprehensive multi-layer architectural and compatibility audit was conducted across the three merged subsystems of Brightloop Software's Subscription Management System (SMS):
1. **Frontend (F1–F10):** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query.
2. **Backend (B1–B15):** Python Flask REST API, SQLAlchemy ORM, Marshmallow, APScheduler, ReportLab.
3. **Database (D1–D9):** PostgreSQL 15+ relational schema, migrations, business triggers, and analytical views.

While each teammate delivered high-quality individual components, severe integration mismatches exist at the boundaries between Frontend $\leftrightarrow$ Backend and Backend $\leftrightarrow$ Database:
- **Critical URL Routing Gap:** Frontend API client and Vite development proxy route requests to `/api/*`, whereas the Backend blueprints are mounted exclusively under `/api/v1/*`. This causes $100\%$ of frontend calls to fail with HTTP 404.
- **Authentication Transport Desynchronization:** Backend issues JWT Bearer tokens in JSON response bodies and requires `Authorization: Bearer <token>` on all protected routes. Frontend client relies on HttpOnly cookies (`credentials: "include"`) and passes an unrecognized `X-Mock-Session-Token` header.
- **Monetary Unit Discrepancy:** The Frontend client and UI components expect monetary values represented as integer **paise** (`_paise`, e.g. ₹2,500.00 $\rightarrow$ `250000`), whereas the Backend and Database return fixed-point decimal **rupees** (e.g. `2500.00`). Without adapter normalization, monetary figures in the UI are off by a factor of 100.
- **Missing Backend Endpoints:** 18 distinct endpoints called by the Frontend or mandated by Section 13.1 of `features.md` are absent from the Backend (including `/auth/me`, `/me/*` customer portal routes, `/quotation-templates`, `/invoices/outstanding`, `/audit-logs`, `/dashboard/overdue`, and standalone `/refunds` CRUD).
- **Schema & Model Divergence:** Database migrations use PostgreSQL identity columns (`{table}_id`), `CITEXT` case-insensitivity, single `billing_period` string keys, and trigger-managed state. Backend models use generic `id` columns, duplicate fields, missing plan flags (`auto_close`, `price`), and divergent discount field names.

---

## Phase 1: Repository Architecture & Inventory

### 1.1 Architecture Summary

| Component | Technology / Library | Location / Notes |
|---|---|---|
| **Frontend Framework** | React 18.3.1, TypeScript 5.5, Vite 5.4 | `frontend/src/` |
| **Frontend Routing & State** | React Router DOM 6.26, TanStack Query 5.56 | `frontend/src/app/`, `frontend/src/api/` |
| **Frontend Styling & UI** | Tailwind CSS 3.4, Lucide React, Recharts | `frontend/src/components/`, `features/` |
| **Backend Framework** | Python 3.13, Flask 3.1.3 | `backend/app/` |
| **Authentication & Tokens** | Flask-JWT-Extended 4.7.4 | JWT Bearer tokens with TokenBlocklist |
| **ORM & Migrations** | Flask-SQLAlchemy 3.1.1, Flask-Migrate 4.1.0 | `backend/app/models/` |
| **Validation & Serialization** | Marshmallow 4.3.1 | `backend/app/schemas/` |
| **Scheduler & Jobs** | APScheduler 3.11.3 | `backend/app/jobs/billing_job.py` |
| **Email Service** | Custom `MailService` (Dev Outbox / SMTP TLS) | `backend/app/services/mail_service.py` |
| **PDF Generation** | ReportLab 5.1.0 | `backend/app/services/pdf_service.py` |
| **Database Engines** | SQLite (Embedded dev) / PostgreSQL 15+ (Production) | `subscription_system.db` / `database/migrations/` |
| **Database Migrations** | Plain ANSI/PostgreSQL SQL (001 to 008) | `database/migrations/` |
| **Environment Configs** | `.env`, `.env.example`, `frontend/.env` | Root & `frontend/` |

---

### 1.2 Backend API Routes Catalog

| Blueprint | HTTP Method | Route Path | Enforced Roles | Description / Handler |
|---|---|---|---|---|
| `health` | GET | `/api/v1/health` | Public | System health check (`health.py:7`) |
| `auth` | POST | `/api/v1/auth/signup` | Public | Customer account registration (`auth.py:32`) |
| `auth` | POST | `/api/v1/auth/login` | Public | User authentication & JWT issuance (`auth.py:91`) |
| `auth` | POST | `/api/v1/auth/logout` | Authenticated | JWT token revocation (`auth.py:164`) |
| `auth` | POST | `/api/v1/auth/forgot-password` | Public | Password reset token generation (`auth.py:174`) |
| `auth` | POST | `/api/v1/auth/reset-password` | Public | Password reset execution (`auth.py:212`) |
| `staff` | POST | `/api/v1/staff` | Admin | Staff member creation (`staff.py:18`) |
| `staff` | GET | `/api/v1/staff` | Admin | Paginated staff listing (`staff.py:69`) |
| `staff` | PATCH | `/api/v1/staff/<int:staff_id>` | Admin | Staff update & deactivation (`staff.py:89`) |
| `catalog` | POST | `/api/v1/taxes` | Admin | Tax rule creation (`catalog.py:23`) |
| `catalog` | GET | `/api/v1/taxes` | Admin, Staff, Customer | List active tax rules (`catalog.py:63`) |
| `catalog` | POST | `/api/v1/discounts` | Admin | Discount rule creation (`catalog.py:79`) |
| `catalog` | GET | `/api/v1/discounts` | Admin, Staff | List discount rules (`catalog.py:139`) |
| `catalog` | POST | `/api/v1/products` | Admin | Product catalog creation (`catalog.py:159`) |
| `catalog` | GET | `/api/v1/products` | Admin, Staff, Customer | Paginated product listing (`catalog.py:201`) |
| `catalog` | POST | `/api/v1/products/<int:id>/variants` | Admin | Add variant to product (`catalog.py:221`) |
| `catalog` | POST | `/api/v1/plans` | Admin | Billing plan creation (`catalog.py:267`) |
| `catalog` | GET | `/api/v1/plans` | Admin, Staff, Customer | Paginated plan listing (`catalog.py:314`) |
| `quotations` | GET | `/api/v1/customers` | Admin, Staff | Paginated customer listing (`quotations.py:33`) |
| `quotations` | POST | `/api/v1/quotations` | Admin, Staff, Customer | Create quotation proposal (`quotations.py:51`) |
| `quotations` | GET | `/api/v1/quotations` | Admin, Staff, Customer | Paginated quotation listing (`quotations.py:175`) |
| `quotations` | GET | `/api/v1/quotations/<int:id>` | Admin, Staff, Customer | Retrieve quotation details (`quotations.py:198`) |
| `quotations` | POST | `/api/v1/quotations/<int:id>/confirm` | Admin, Staff, Customer | Confirm quote $\rightarrow$ create subscription (`quotations.py:209`) |
| `subscriptions` | GET | `/api/v1/subscriptions` | Admin, Staff, Customer | List subscriptions (`subscriptions.py:22`) |
| `subscriptions` | GET | `/api/v1/subscriptions/<int:id>` | Admin, Staff, Customer | Subscription details (`subscriptions.py:49`) |
| `subscriptions` | POST | `/api/v1/subscriptions/<int:id>/activate` | Admin, Staff, Customer | Transition confirmed/paused $\rightarrow$ active (`subscriptions.py:60`) |
| `subscriptions` | POST | `/api/v1/subscriptions/<int:id>/pause` | Admin, Staff, Customer | Suspend billing / pause (`subscriptions.py:86`) |
| `subscriptions` | POST | `/api/v1/subscriptions/<int:id>/close` | Admin, Staff, Customer | Early closure / cancel (`subscriptions.py:123`) |
| `subscriptions` | POST | `/api/v1/subscriptions/<int:id>/renew` | Admin, Staff, Customer | Extend period / renew (`subscriptions.py:158`) |
| `billing_trigger` | POST | `/api/v1/billing/run` | Admin | Execute billing run job (`billing_trigger.py:10`) |
| `invoices` | GET | `/api/v1/invoices` | Admin, Staff, Customer | Paginated invoices listing (`invoices.py:28`) |
| `invoices` | GET | `/api/v1/invoices/overdue` | Admin, Staff, Customer | List overdue invoices (`invoices.py:56`) |
| `invoices` | GET | `/api/v1/invoices/<int:id>` | Admin, Staff, Customer | Invoice details (`invoices.py:81`) |
| `invoices` | POST | `/api/v1/invoices/<int:id>/confirm` | Admin, Staff, Customer | Lock invoice amounts (`invoices.py:92`) |
| `invoices` | GET | `/api/v1/invoices/<int:id>/pdf` | Admin, Staff, Customer | Download binary PDF (`invoices.py:122`) |
| `invoices` | POST | `/api/v1/invoices/<int:id>/send` | Admin, Staff | Dispatch PDF invoice email (`invoices.py:141`) |
| `invoices` | POST | `/api/v1/invoices/<int:id>/cancel` | Admin, Staff | Cancel draft/confirmed invoice (`invoices.py:157`) |
| `invoices` | POST | `/api/v1/invoices/<int:id>/refund` | Admin | Process invoice refund (`invoices.py:183`) |
| `payments` | POST | `/api/v1/payments` | Admin, Staff, Customer | Record payment receipt (`payments.py:26`) |
| `payments` | GET | `/api/v1/payments` | Admin, Staff, Customer | Paginated payments listing (`payments.py:110`) |
| `payments` | GET | `/api/v1/payments/<int:id>` | Admin, Staff, Customer | Retrieve payment receipt (`payments.py:134`) |
| `dashboard` | GET | `/api/v1/dashboard/summary` | Admin, Staff | Operational metrics telemetry (`dashboard.py:15`) |

---

### 1.3 Frontend API Calls Catalog

| API Module | Frontend Function | HTTP Method & Target Path | Expected Payload / Response | Backend Status |
|---|---|---|---|---|
| `authApi` | `signup` | `POST auth/signup` | `{ email, password, name, phone?, company_name? }` | Exists (`/api/v1/auth/signup`) |
| `authApi` | `login` | `POST auth/login` | `{ email, password }` $\rightarrow$ `{ user, session_token }` | Mismatch (path & payload keys) |
| `authApi` | `logout` | `POST auth/logout` | No payload $\rightarrow$ `{ message }` | Exists (`/api/v1/auth/logout`) |
| `authApi` | `forgotPassword` | `POST auth/forgot-password` | `{ email }` $\rightarrow$ `{ message }` | Exists |
| `authApi` | `resetPassword` | `POST auth/reset-password` | `{ token, password }` $\rightarrow$ `{ message }` | Exists |
| `authApi` | `getMe` | `GET auth/me` | Authenticated session $\rightarrow$ `User` | **MISSING** |
| `authApi` | `updateProfile` | `PATCH auth/me` | `{ name?, phone?, company_name? }` | **MISSING** |
| `staffApi` | `list` | `GET staff?page=&per_page=` | Paginated `StaffMember` items | Exists |
| `staffApi` | `create` | `POST staff` | `{ name, email, role, phone?, department?, password? }` | Exists |
| `staffApi` | `update` | `PATCH staff/:id` | Partial `StaffMember` fields | Exists |
| `customerApi` | `list` | `GET customers?page=` | Paginated `Customer` items | Exists (`quotations.py:33`) |
| `customerApi` | `get` | `GET customers/:id` | Returns `CustomerDetail` with aggregates | **MISSING** |
| `customerApi` | `create` | `POST customers` | Create customer directly | **MISSING** |
| `customerApi` | `update` | `PATCH customers/:id` | Update customer metadata | **MISSING** |
| `customerApi` | `sendResetLink` | `POST customers/:id/send-reset-link` | Trigger admin/staff reset email | **MISSING** |
| `catalogueApi` | `listProducts` | `GET products` | Paginated `Product` items | Exists |
| `catalogueApi` | `getProduct` | `GET products/:id` | Product detail with variants | **MISSING** |
| `catalogueApi` | `createProduct` | `POST products` | Create product with variants | Exists |
| `catalogueApi` | `updateProduct` | `PATCH products/:id` | Modify product attributes | **MISSING** |
| `catalogueApi` | `deleteProduct` | `DELETE products/:id` | Deactivate/remove product | **MISSING** |
| `catalogueApi` | `createVariant` | `POST products/:id/variants` | `{ name, extra_price_paise }` | Exists |
| `catalogueApi` | `listPlans` | `GET plans` | Paginated `Plan` items | Exists |
| `catalogueApi` | `getPlan` | `GET plans/:id` | Plan detail | **MISSING** |
| `catalogueApi` | `createPlan` | `POST plans` | Create plan | Exists |
| `catalogueApi` | `updatePlan` | `PATCH plans/:id` | Update plan flags | **MISSING** |
| `catalogueApi` | `deletePlan` | `DELETE plans/:id` | Deactivate plan | **MISSING** |
| `catalogueApi` | `listTaxes` | `GET taxes` | Paginated `TaxRule` items | Exists |
| `catalogueApi` | `createTax` | `POST taxes` | Create tax rule | Exists |
| `catalogueApi` | `updateTax` | `PATCH taxes/:id` | Modify tax rate | **MISSING** |
| `catalogueApi` | `deleteTax` | `DELETE taxes/:id` | Deactivate tax rule | **MISSING** |
| `catalogueApi` | `listDiscounts` | `GET discounts` | Paginated `DiscountRule` items | Exists |
| `catalogueApi` | `createDiscount` | `POST discounts` | Create discount rule | Exists |
| `catalogueApi` | `updateDiscount` | `PATCH discounts/:id` | Modify discount rule | **MISSING** |
| `catalogueApi` | `deleteDiscount` | `DELETE discounts/:id` | Deactivate discount | **MISSING** |
| `quotationApi` | `listTemplates` | `GET quotation-templates` | Paginated templates list | **MISSING** |
| `quotationApi` | `createTemplate` | `POST quotation-templates` | Create template | **MISSING** |
| `quotationApi` | `list` | `GET quotations` | Paginated quotes | Exists |
| `quotationApi` | `get` | `GET quotations/:id` | Quote detail with lines | Exists |
| `quotationApi` | `create` | `POST quotations` | Create quotation proposal | Exists |
| `quotationApi` | `update` | `PATCH quotations/:id` | Modify quotation draft | **MISSING** |
| `subscriptionApi` | `list` | `GET subscriptions` | Paginated subscriptions | Exists |
| `subscriptionApi` | `get` | `GET subscriptions/:id` | Subscription detail | Exists |
| `subscriptionApi` | `create` | `POST subscriptions` | Direct subscription creation | **MISSING** |
| `subscriptionApi` | `update` | `PATCH subscriptions/:id` | Update subscription terms | **MISSING** |
| `subscriptionApi` | `confirm` | `POST subscriptions/:id/confirm` | Confirm subscription | **MISSING** (Backend only has quote confirm) |
| `subscriptionApi` | `activate` | `POST subscriptions/:id/activate` | Activate subscription | Exists |
| `subscriptionApi` | `pause` | `POST subscriptions/:id/pause` | Pause subscription | Exists |
| `subscriptionApi` | `resume` | `POST subscriptions/:id/resume` | Resume subscription | **MISSING** (Backend uses `/activate`) |
| `subscriptionApi` | `renew` | `POST subscriptions/:id/renew` | Renew subscription | Exists |
| `subscriptionApi` | `close` | `POST subscriptions/:id/close` | Early close subscription | Exists |
| `invoiceApi` | `list` | `GET invoices` | Paginated invoices | Exists |
| `invoiceApi` | `get` | `GET invoices/:id` | Invoice detail with lines | Exists |
| `invoiceApi` | `create` | `POST invoices` | Manual invoice creation | **MISSING** |
| `invoiceApi` | `confirm` | `POST invoices/:id/confirm` | Confirm invoice | Exists |
| `invoiceApi` | `send` | `POST invoices/:id/send` | Send invoice PDF email | Exists |
| `invoiceApi` | `cancel` | `POST invoices/:id/cancel` | Cancel invoice | Exists |
| `invoiceApi` | `getPdf` | `GET invoices/:id/pdf` | Download PDF stream | Exists |
| `invoiceApi` | `listOutstanding` | `GET invoices/outstanding` | Outstanding invoices ledger | **MISSING** |
| `invoiceApi` | `runBilling` | `POST billing/run` | Execute automated billing | Exists |
| `paymentApi` | `list` | `GET payments` | Paginated payments | Exists |
| `paymentApi` | `create` | `POST payments` | Inward payment receipt | Exists |
| `paymentApi` | `update` | `PATCH payments/:id` | Update payment details | **MISSING** |
| `refundApi` | `list` | `GET refunds` | Paginated refunds | **MISSING** |
| `refundApi` | `create` | `POST refunds` | Create refund request | **MISSING** (Backend has `/invoices/:id/refund`) |
| `refundApi` | `update` | `PATCH refunds/:id` | Approve/Reject refund | **MISSING** |
| `dashboardApi` | `getSummary` | `GET dashboard/summary` | Telemetry & KPI payload | Exists (Shape mismatch) |
| `dashboardApi` | `getOverdue` | `GET dashboard/overdue` | Overdue invoice list | **MISSING** (Backend has `/invoices/overdue`) |
| `portalApi` | `getMySubscriptions` | `GET me/subscriptions` | Customer portal subscriptions | **MISSING** |
| `portalApi` | `getMyInvoices` | `GET me/invoices` | Customer portal invoices | **MISSING** |
| `portalApi` | `getMyDashboard` | `GET me/dashboard` | Customer dashboard metrics | **MISSING** |
| `auditApi` | `list` | `GET audit-logs` | Admin audit log viewer | **MISSING** |

---

### 1.4 Database Migrations Schema Catalog

The PostgreSQL migration scripts define the following 14 tables and 4 views:

```
database/migrations/
├── 001_extensions_and_enums.sql   (citext, pgcrypto, sequences for SUB-, INV-, QT-)
├── 002_account_tables.sql         (auth, staff, customer)
├── 003_catalog_tables.sql         (product, product_variant, plan, tax, discount, discount_product)
├── 004_sales_tables.sql           (quotation, quotation_line, subscription, subscription_line, subscription_status_history)
├── 005_billing_tables.sql         (invoice, invoice_line, payment, refund)
├── 006_integrity_triggers.sql     (auto-numbering, refund cap check, invoice auto-paid sync, history capture)
├── 007_performance_indexes_views.sql (composite indexes, v_active_subscriptions, v_overdue_invoices, v_dashboard_kpis, mv_dashboard_summary)
└── 008_audit_log.sql              (audit_log table, append-only security trigger, automated change capture)
```

#### Migration Tables & Columns Summary:
- `auth`: `id`, `email (CITEXT UNIQUE)`, `password_hash`, `role (admin, staff, customer)`, `is_active`, `last_login`, `reset_token`, `reset_expiry`, `created_at`, `updated_at`.
- `staff`: `staff_id`, `auth_id (FK, UNIQUE)`, `name`, `department`, `created_by (FK)`, `is_active`, `created_at`, `updated_at`.
- `customer`: `customer_id`, `auth_id (FK, UNIQUE)`, `name`, `phone`, `address`, `company`, `is_active`, `created_at`, `updated_at`.
- `product`: `product_id`, `name`, `type (service, software, add-on, physical)`, `sales_price (NUMERIC)`, `cost_price (NUMERIC)`, `notes`, `is_active`, `created_at`, `updated_at`.
- `product_variant`: `variant_id`, `product_id (FK)`, `attribute`, `value`, `extra_price (NUMERIC)`, `is_active`, `created_at`, `updated_at`.
- `plan`: `plan_id`, `name`, `price (NUMERIC)`, `billing_period (daily, weekly, monthly, yearly)`, `min_quantity`, `start_date`, `end_date`, `auto_close`, `allow_early_close`, `allow_pause`, `allow_renewal`, `is_active`, `created_at`, `updated_at`.
- `tax`: `tax_id`, `name`, `rate (NUMERIC)`, `applies_to`, `is_active`, `created_at`, `updated_at`.
- `discount`: `discount_id`, `name`, `code (UNIQUE)`, `type (fixed, percent)`, `value (NUMERIC)`, `scope (product, subscription)`, `product_id (FK)`, `min_amount`, `min_qty`, `start_date`, `end_date`, `usage_limit`, `times_used`, `is_active`, `created_at`, `updated_at`.
- `discount_product`: `discount_id (PK, FK)`, `product_id (PK, FK)`, `created_at`.
- `quotation`: `quotation_id`, `number (UNIQUE)`, `is_template`, `customer_id (FK)`, `plan_id (FK)`, `validity_days`, `status (draft, sent, accepted, expired, cancelled)`, `created_by (FK)`, `notes`, `created_at`, `updated_at`.
- `quotation_line`: `line_id`, `quotation_id (FK)`, `product_id (FK)`, `variant_id (FK)`, `quantity`, `unit_price`, `tax_id (FK)`, `amount`, `created_at`.
- `subscription`: `subscription_id`, `number (UNIQUE)`, `customer_id (FK)`, `plan_id (FK)`, `quotation_id (FK)`, `start_date`, `expiry_date`, `next_billing_date`, `payment_terms (Immediate, Net 15, Net 30)`, `status (draft, quotation, confirmed, active, paused, closed)`, `created_at`, `updated_at`.
- `subscription_line`: `line_id`, `subscription_id (FK)`, `product_id (FK)`, `variant_id (FK)`, `quantity`, `unit_price`, `tax_id (FK)`, `amount`, `created_at`.
- `subscription_status_history`: `history_id`, `subscription_id (FK)`, `from_status`, `to_status`, `changed_by (FK)`, `reason`, `created_at`.
- `invoice`: `invoice_id`, `number (UNIQUE)`, `subscription_id (FK)`, `customer_id (FK)`, `billing_period (UNIQUE with subscription_id)`, `subtotal`, `discount_total`, `tax_total`, `total`, `issue_date`, `due_date`, `status (draft, confirmed, paid, cancelled)`, `notes`, `created_at`, `updated_at`.
- `invoice_line`: `line_id`, `invoice_id (FK)`, `product_id (FK)`, `variant_id (FK)`, `description`, `quantity`, `unit_price`, `discount_amount`, `tax_id (FK)`, `tax_amount`, `amount`, `created_at`.
- `payment`: `payment_id`, `invoice_id (FK)`, `method (card, bank_transfer, upi, cash, cheque, other)`, `amount`, `payment_date`, `note`, `recorded_by (FK)`, `created_at`, `updated_at`.
- `refund`: `refund_id`, `payment_id (FK)`, `invoice_id (FK)`, `amount`, `reason`, `status (requested, approved, processed, rejected)`, `processed_date`, `approved_by (FK)`, `created_at`, `updated_at`.
- `audit_log`: `log_id`, `user_id (FK)`, `action (INSERT, UPDATE, DELETE)`, `entity`, `entity_id`, `timestamp`, `old_values (JSONB)`, `new_values (JSONB)`.

---

## Phase 2: Compatibility Matrix

### 2.1 Feature Compatibility Matrix (F1–F10, B1–B15, D1–D9)

| Feature Code | Area & Description | Status | Evidence (File : Line) | Issue Summary |
|---|---|---|---|---|
| **F1** | App layout, navigation, role routes | **Compatible** | `frontend/src/app/Router.tsx:32-150` | Role guards and route trees properly configured. |
| **F2** | Form validation & password rules | **Compatible** | `frontend/src/lib/permissions.ts:80-110` | Client enforces $>8$ chars, upper, lower, special. |
| **F3** | Signup, login, forgot, reset pages | **Mismatch** | `frontend/src/features/auth/LoginPage.tsx:132-160` | Login demo fills `@brightloop.test` not in seed; token response unhandled. |
| **F4** | Account settings & profile | **Missing** | `frontend/src/app/AuthContext.tsx:30` | Calls `GET /auth/me`; route does not exist in backend. |
| **F5** | Customer portal dashboard | **Missing** | `frontend/src/features/portal/CustomerDashboardPage.tsx:28` | Calls `GET /me/dashboard`; endpoint absent in backend. |
| **F6** | Customer My Subscriptions | **Missing** | `frontend/src/features/portal/CustomerSubscriptionsPage.tsx:35` | Calls `GET /me/subscriptions`; endpoint absent in backend. |
| **F7** | Customer My Invoices & PDF | **Missing** | `frontend/src/features/portal/CustomerInvoicesPage.tsx:32` | Calls `GET /me/invoices`; endpoint absent in backend. |
| **F8** | Staff operational pages | **Mismatch** | `frontend/src/features/quotations/QuotationTemplatesListPage.tsx:30` | Calls `GET /quotation-templates`; absent in backend. |
| **F9** | Admin management pages | **Mismatch** | `frontend/src/features/catalogue/ProductsListPage.tsx:85` | Product mutations (`PATCH/DELETE /products/:id`) absent in backend. |
| **F10** | Staff & admin analytics dashboard | **Mismatch** | `frontend/src/features/dashboard/DashboardPage.tsx:43-88` | Metric names (`mrr_paise`, `arr_paise`, trends) missing from response. |
| **B1** | Customer signup, login, logout | **Mismatch** | `backend/app/routes/auth.py:91-162` | Returns `access_token` instead of session/token expected by frontend. |
| **B2** | Password reset flow | **Mismatch** | `backend/app/routes/auth.py:206` | Forgot-password leaks `reset_token` in response body. |
| **B3** | Role-based access control (RBAC) | **Mismatch** | `backend/app/routes/payments.py:27` | Customer permitted to call `POST /payments` (violates Section 2.4). |
| **B4** | Staff management | **Compatible** | `backend/app/routes/staff.py:18-122` | Admin-only create, list, and patch deactivation. |
| **B5** | Products & Variants with delta | **Mismatch** | `backend/app/routes/catalog.py:159-264` | Missing `GET /products/:id`, `PATCH`, `DELETE`. |
| **B6** | Plans & lifecycle flags | **Mismatch** | `backend/app/models/catalog.py:91-94` | Model uses `allow_close`, `allow_renew`; missing `price`, `auto_close`. |
| **B7** | Discount rule engine | **Mismatch** | `backend/app/routes/catalog.py:79-156` | Uses `discount_type='percentage'`; DB uses `'percent'`. Missing `PATCH/DELETE`. |
| **B8** | Tax calculation per invoice line | **Compatible** | `backend/app/services/pricing_service.py:89-105` | Auto-calculated per line; staff cannot override. |
| **B9** | Quotations & Templates | **Mismatch** | `backend/app/routes/quotations.py:1-286` | Model `QuotationTemplate` exists, but no `/quotation-templates` route. |
| **B10** | Subscription lifecycle | **Mismatch** | `backend/app/routes/subscriptions.py:60-192` | Missing `POST /subscriptions` and `POST /subscriptions/:id/confirm`. |
| **B11** | Idempotent billing job | **Mismatch** | `backend/app/services/billing_service.py:155-159` | Response returns `invoices` instead of `created`, `skipped`, `failed`. |
| **B12** | Invoice actions (confirm, send, pdf) | **Mismatch** | `backend/app/routes/invoices.py:164` | `cancel_invoice` allows cancelling confirmed invoices with partial payments. |
| **B13** | Payment recording & ledger | **Mismatch** | `backend/app/routes/invoices.py:56` | Missing `/invoices/outstanding` route (only `/invoices/overdue` exists). |
| **B14** | Refunds & Cancellations | **Mismatch** | `backend/app/routes/invoices.py:183-259` | Only `POST /invoices/:id/refund` exists; `/refunds` CRUD absent. |
| **B15** | Dashboard summary & filters | **Mismatch** | `backend/app/routes/dashboard.py:144-154` | Excludes MRR, ARR, churn rate, collection rate, trends. |
| **D1** | Account tables (Auth, Customer, Staff) | **Mismatch** | `database/migrations/002_account_tables.sql:8-66` | PK is `customer_id`/`staff_id`; Backend models use generic `id`. |
| **D2** | Catalog tables (Product, Variant, Plan) | **Mismatch** | `database/migrations/003_catalog_tables.sql:48-70` | Plan requires `price NUMERIC(12,2)`; backend model lacks `price`. |
| **D3** | Sales tables (Quotation, Subscription) | **Mismatch** | `database/migrations/004_sales_tables.sql:56-76` | Unique document number is `number`; backend uses `subscription_number`. |
| **D4** | Billing tables (Invoice, Payment, Refund) | **Mismatch** | `database/migrations/005_billing_tables.sql:8-35` | Invoice unique period is `billing_period`; backend has `billing_period_start`. |
| **D5** | Integrity triggers | **Compatible** | `database/migrations/006_integrity_triggers.sql:63-100` | Refund limit lock trigger and auto-paid invoice status sync. |
| **D6** | Indexes & analytical views | **Compatible** | `database/migrations/007_performance_indexes_views.sql:1-193` | Composite indexes and real-time KPI views verified. |
| **D7** | Seed data coverage | **Mismatch** | `database/seeds/001_seed_data.sql:18-25` | Seed credentials (`admin@brightloop.io`) differ from backend (`admin@example.com`). |
| **D8** | Automated backups & restore | **Compatible** | `database/scripts/backup.ps1:1-60` | Full `pg_dump` and `pg_restore` disaster recovery scripts provided. |
| **D9** | Immutable audit log | **Compatible** | `database/migrations/008_audit_log.sql:35-48` | Trigger aborts any `UPDATE` or `DELETE` on `audit_log`. |

---

### 2.2 Cross-Reference A: Frontend $\leftrightarrow$ Backend (API Contract)

| Frontend Call (`src/api/endpoints.ts`) | Backend Route (`backend/app/routes/`) | Status | Discrepancies & Required Fix |
|---|---|---|---|
| `POST auth/signup` | `POST /api/v1/auth/signup` | **Mismatch** | Base URL path missing `/v1`. Field `company_name` vs `company`. |
| `POST auth/login` | `POST /api/v1/auth/login` | **Mismatch** | Backend returns `access_token`; Frontend expects `session_token`. |
| `POST auth/logout` | `POST /api/v1/auth/logout` | **Mismatch** | Base URL path missing `/v1`. Frontend sends no Bearer header. |
| `GET auth/me` | *None* | **Missing** | Implement `GET /api/v1/auth/me` returning authenticated user profile. |
| `PATCH auth/me` | *None* | **Missing** | Implement `PATCH /api/v1/auth/me` updating customer/staff profile. |
| `POST auth/forgot-password` | `POST /api/v1/auth/forgot-password` | **Mismatch** | Backend leaks `reset_token` in response body. |
| `GET staff` | `GET /api/v1/staff` | **Compatible** | Response pagination envelopes match. |
| `POST staff` | `POST /api/v1/staff` | **Compatible** | Admin role check matches. |
| `PATCH staff/:id` | `PATCH /api/v1/staff/<int:id>` | **Compatible** | Deactivation and name updates match. |
| `GET customers` | `GET /api/v1/customers` | **Compatible** | Paginated customer directory matches. |
| `GET customers/:id` | *None* | **Missing** | Implement `GET /api/v1/customers/<id>` with active sub counts. |
| `POST customers/:id/send-reset-link` | *None* | **Missing** | Implement staff-triggered reset link dispatch. |
| `GET products/:id` | *None* | **Missing** | Implement product detail view. |
| `PATCH products/:id` | *None* | **Missing** | Implement product modification endpoint. |
| `DELETE products/:id` | *None* | **Missing** | Implement product deactivation endpoint. |
| `GET plans/:id` | *None* | **Missing** | Implement plan detail view. |
| `PATCH plans/:id` | *None* | **Missing** | Implement plan modification endpoint. |
| `DELETE plans/:id` | *None* | **Missing** | Implement plan deactivation endpoint. |
| `PATCH taxes/:id`, `DELETE taxes/:id` | *None* | **Missing** | Implement tax rule update/delete. |
| `PATCH discounts/:id`, `DELETE discounts/:id` | *None* | **Missing** | Implement discount rule update/delete. |
| `GET quotation-templates` | *None* | **Missing** | Implement quotation templates listing and creation. |
| `POST subscriptions/:id/confirm` | *None* | **Missing** | Implement direct subscription confirmation. |
| `POST subscriptions/:id/resume` | *None* | **Missing** | Alias to `/activate` or implement `/resume`. |
| `GET invoices/outstanding` | *None* | **Missing** | Implement outstanding invoices query (`balance_due > 0`). |
| `POST billing/run` | `POST /api/v1/billing/run` | **Mismatch** | Response envelope keys (`created`, `skipped`, `failed`). |
| `GET refunds`, `POST refunds`, `PATCH refunds/:id` | *None* | **Missing** | Implement standalone `/refunds` resource routes. |
| `GET dashboard/overdue` | *None* | **Missing** | Mount overdue invoices under `/dashboard/overdue`. |
| `GET me/subscriptions` | *None* | **Missing** | Implement customer-scoped subscriptions list. |
| `GET me/invoices` | *None* | **Missing** | Implement customer-scoped invoices list. |
| `GET me/dashboard` | *None* | **Missing** | Implement customer-scoped dashboard summary. |
| `GET audit-logs` | *None* | **Missing** | Implement admin-only audit log query endpoint. |

---

### 2.3 Cross-Reference B: Backend $\leftrightarrow$ Database

| SQLAlchemy Model (`backend/app/models/`) | PostgreSQL Migration Table (`database/migrations/`) | Column & Type Mismatches | Required Action |
|---|---|---|---|
| `Auth` | `auth` | `reset_token_expires_at` vs `reset_expiry`; missing `last_login`. | Harmonize column aliases in model/migration. |
| `Customer` | `customer` | PK `id` vs `customer_id`; `billing_address` vs `address`; duplicate `email` in customer table; missing `is_active`. | Map model properties to DB column names. |
| `Staff` | `staff` | PK `id` vs `staff_id`; duplicate `email` and `role`; missing `created_by`. | Map model properties to DB column names. |
| `Product` | `product` | PK `id` vs `product_id`; missing `type` (service/software/add-on/physical) and `notes`. | Add `type` and `notes` to model. |
| `Variant` | `product_variant` | PK `id` vs `variant_id`; model has `name`, DB has `attribute` + `value`. | Add attribute/value mapping. |
| `Plan` | `plan` | PK `id` vs `plan_id`; missing `price` and `auto_close`; `allow_close` vs `allow_early_close`; `allow_renew` vs `allow_renewal`. | Add `price`, `auto_close`, and canonical flag names. |
| `Discount` | `discount` | PK `id` vs `discount_id`; `discount_type` ('percentage') vs `type` ('percent'); `used_count` vs `times_used`; `min_purchase` vs `min_amount`; `applies_to` vs `scope`. | Support both enum/column aliases. |
| `Tax` | `tax` | PK `id` vs `tax_id`; missing `applies_to` in model. | Add `applies_to` column in model. |
| `Quotation` | `quotation` | Separate `quotation_template` table vs `is_template` boolean in DB; `quotation_number` vs `number`. | Align document number naming and template flag. |
| `Subscription` | `subscription` | PK `id` vs `subscription_id`; `subscription_number` vs `number`; missing `expiry_date` and `payment_terms`. | Add `expiry_date` and `payment_terms` to model. |
| `Invoice` | `invoice` | PK `id` vs `invoice_id`; `invoice_number` vs `number`; `billing_period_start/end` vs single `billing_period`; `tax_amount` vs `tax_total`; `discount_amount` vs `discount_total`. | Align period representation and column names. |
| `Payment` | `payment` | PK `id` vs `payment_id`; `date` vs `payment_date`; missing `recorded_by`. | Add `recorded_by` FK to model. |
| `Refund` | `refund` | PK `id` vs `refund_id`; missing `status` ('requested', 'approved', 'processed', 'rejected'), `processed_date`, `approved_by`. | Add status workflow fields to model. |
| `AuditLog` | `audit_log` | PK `id` vs `log_id`; `auth_id` vs `user_id`. | Map model properties to DB column names. |

---

### 2.4 Cross-Reference C: Frontend $\leftrightarrow$ Database (via Backend)

| Frontend UI Screen | Displayed / Submitted Fields | Traced Backend Model Field | Underlying DB Column | Gap / Risk |
|---|---|---|---|---|
| **Login Page** | `email`, `password` | `Auth.email`, `Auth.password_hash` | `auth.email (CITEXT)`, `auth.password_hash` | No case-insensitivity on SQLite. |
| **Signup Page** | `name`, `email`, `company_name`, `phone` | `Customer.name`, `Auth.email`, `Customer.company`, `Customer.phone` | `customer.name`, `auth.email`, `customer.company`, `customer.phone` | Working, but email stored redundantly. |
| **Products List** | `sales_price_paise`, `variants[].extra_price_paise` | `Product.sales_price`, `Variant.extra_price` | `product.sales_price`, `product_variant.extra_price` | **Scale Mismatch:** Rupees returned, Paise expected. |
| **Plans List** | `auto_close`, `allow_early_close`, `allow_pause`, `allow_renewal` | `Plan.allow_pause`, `Plan.allow_close`, `Plan.allow_renew` | `plan.auto_close`, `plan.allow_early_close`, `plan.allow_pause`, `plan.allow_renewal` | `auto_close` omitted; flag names mismatched. |
| **Subscription Detail** | Actions: Pause, Close Early, Renew | Checked against `plan.allow_*` | `plan.allow_pause`, `plan.allow_early_close`, `plan.allow_renewal` | UI correctly hides actions, but API checks wrong model flags. |
| **Invoice Detail** | Subtotal, discounts, taxes, total, balance due | `Invoice.subtotal`, `Invoice.discount_amount`, `Invoice.tax_amount`, `Invoice.total` | `invoice.subtotal`, `invoice.discount_total`, `invoice.tax_total`, `invoice.total` | Working, but paise/rupees scaling discrepancy. |
| **Customer Dashboard** | `active_subscriptions_count`, `balance_due_paise`, `recent_invoices` | *None* | `v_dashboard_kpis` or aggregate queries | Endpoint `/api/me/dashboard` missing in backend. |
| **Audit Log Viewer** | `timestamp`, `user_id`, `action`, `entity`, `old_values`, `new_values` | `AuditLog.*` | `audit_log.*` | Endpoint `/api/audit-logs` missing in backend. |

---

## Phase 3: Business-Rule Verification

| # | Business Rule | Verification Method | Status | Findings & Exact Code Locations |
|---|---|---|---|---|
| **1** | **Authentication & Password Policy** | Inspect `auth_schemas.py`, `auth.py`, `LoginPage.tsx` | **FAIL** | 1. Weak password rejected properly.<br/>2. Forgot-password leaks `reset_token` in response body (`auth.py:206`).<br/>3. No rate limiting / lockout decorator on login (`auth.py:91`).<br/>4. Email uniqueness check is case-sensitive on SQLite (`auth.py:51`). |
| **2** | **Server-side RBAC & IDOR Isolation** | Test role decorators in `routes/` | **FAIL** | 1. Customers can call `POST /payments` (`payments.py:27`) and `POST /invoices/:id/confirm` (`invoices.py:93`), violating Section 2.4.<br/>2. Staff blocked properly from creating catalog items.<br/>3. `enforce_customer_isolation` properly blocks cross-customer access on existing routes. |
| **3** | **Plan Permission Flags** | Inspect `subscriptions.py:95, 132, 167` | **PARTIAL** | Backend checks `allow_pause`, `allow_close`, `allow_renew`, but returns HTTP 409 instead of 403. Model lacks `allow_early_close` and `allow_renewal` canonical names. |
| **4** | **Pricing Calculation Order** | Inspect `pricing_service.py:16-113` | **PASS** | Calculation order: $(Unit + Variant) \times Qty \rightarrow - Discount \rightarrow + Tax = Total$. Rounding uses `Decimal` with `ROUND_HALF_UP`. Unit price formula verified. |
| **5** | **Discount Application & Limits** | Inspect `pricing_service.py:47-86` & `billing_service.py:130` | **FAIL** | 1. Min quantity and date validity checked.<br/>2. Usage counter updated in Python memory (`used_count += 1`), not via atomic SQL row-lock.<br/>3. Discount is not added as its own line on invoices (Section 7). |
| **6** | **Idempotent Billing Job** | Run `billing_job.py` twice | **PASS** | `UniqueConstraint('subscription_id', 'billing_period_start')` prevents duplicate invoices. Advances `next_billing_date` in same transaction. Catches up missed periods. |
| **7** | **Invoice Lifecycle & PDF** | Inspect `invoices.py:92-181` | **FAIL** | 1. `confirm_invoice` locks lines.<br/>2. `cancel_invoice` allows cancelling confirmed invoices that have partial payments (`invoices.py:164` only checks `invoice.status == 'paid'`).<br/>3. Auto-paid transition works.<br/>4. ReportLab PDF download verified. |
| **8** | **Payment Reconciliation** | Inspect `payments.py:26-107` | **PASS** | Payments link to invoices. Overpayments rejected (`payments.py:56`). Status shifts to `'paid'` when balance reaches 0. |
| **9** | **Refund Limits & Calculations** | Inspect `invoices.py:183-259` | **PASS** | Refund amount capped at `amount_paid - total_refunded`. Reduces `amount_paid` and reverts invoice to `'confirmed'`. |
| **10** | **Dashboard Telemetry (<2s)** | Inspect `dashboard.py:15-157` | **FAIL** | Sub-millisecond execution verified, but response payload omits MRR, ARR, churn rate, collection rate, and trend series. |
| **11** | **Audit Logging** | Inspect `audit_service.py:7` | **PARTIAL** | Money-related mutations logged with old and new values. However, no endpoint exists to retrieve or view audit records. |

---

## Phase 4: Mock & Dead Code Audit

### 4.1 Mock / Placeholder Code Inventory

| # | File Path | Line No. | Pattern / Match | Purpose in Code | Action Required |
|---|---|---|---|---|---|
| 1 | `frontend/src/api/client.ts` | 41–45 | `brightloop_mock_token`, `X-Mock-Session-Token` | Canned token transport for MSW mock mode | **DELETE / REPLACE:** Use standard `Authorization: Bearer <token>`. |
| 2 | `frontend/src/api/client.ts` | 71 | `localStorage.removeItem('brightloop_mock_token')` | Mock session clearance | **REPLACE:** Clear canonical auth token. |
| 3 | `frontend/src/app/AuthContext.tsx` | 57, 71, 86 | `brightloop_mock_token` | Saves `res.session_token` to mock storage | **REPLACE:** Save canonical `access_token` and handle bearer auth. |
| 4 | `frontend/src/features/auth/LoginPage.tsx` | 132–160 | Demo Quick-Fill Credentials (`@brightloop.test`) | Autofills non-existent demo accounts | **REPLACE:** Update quick-fill buttons to match seeded accounts (`admin@example.com`, etc.). |
| 5 | `frontend/.env` | 1 | `VITE_USE_MOCK=false` | Unused environment variable | **DELETE:** Remove unreferenced variable. |
| 6 | `backend/app/routes/auth.py` | 206 | `"reset_token": reset_token` | Leaks raw reset token in production response | **DELETE:** Remove from response to prevent user enumeration. |
| 7 | `mock_test.py` | 1–400 | In-process SQLite test suite | Test harness for development | **KEEP:** Belongs in root test harness; not imported by app code. |

*Total production files containing mock references:* **4 files** (Well below the 20-file stop threshold).

---

## Phase 5: Blocking Gaps & Questions for Owner

### 5.1 Blocking Gaps
1. **Frontend $\leftrightarrow$ Backend Base URL Prefix Mismatch:**
   - Frontend Vite proxy targets `/api`, sending requests to `http://localhost:5000/api/*`.
   - Backend routes are registered with blueprint prefix `/api/v1/*`.
   - *Fix:* Configure Vite proxy / Frontend `VITE_API_BASE_URL` to `/api/v1` and ensure backend blueprints match.
2. **Missing Customer Self-Service Endpoints:**
   - Frontend customer portal crashes on initial load because `/api/v1/auth/me`, `/api/v1/me/dashboard`, `/api/v1/me/subscriptions`, and `/api/v1/me/invoices` do not exist.
   - *Fix:* Implement these routes scoped strictly to `current_user.customer_id`.
3. **Monetary Unit Representation (Paise vs Rupees):**
   - Frontend types expect integer paise (`*_paise`). Backend models return float/decimal rupees.
   - *Fix:* Standardize backend serializers or frontend client adapters so both layers communicate without scaling distortions.

### 5.2 Questions for Owner
1. **Currency Representation:** Does Brightloop mandate integer paise across all JSON payloads (as specified in Member 1's `API_CONTRACT.md`), or fixed-point decimal rupees (as specified in Member 2's `README.md` and Section 12.3 of `features.md`)?
   - *Recommendation:* Support both by exposing canonical decimal values alongside integer `_paise` fields in backend serializers.
2. **Session Persistence Strategy:** Should authentication rely on HTTP-only session cookies or JWT Bearer headers in `Authorization`?
   - *Recommendation:* Configure Flask-JWT-Extended to accept both headers and cookies (`JWT_TOKEN_LOCATION = ["headers", "cookies"]`), and update `frontend/src/api/client.ts` to attach `Authorization: Bearer <token>` when a token is stored.
3. **Production Database Engine:** SQLite is functioning for development, while PostgreSQL scripts are written for deployment. Is the integrated test suite expected to run against SQLite or live PostgreSQL?
   - *Recommendation:* Maintain SQLAlchemy database agnosticism: models run seamlessly on SQLite for local smoke testing and on PostgreSQL for deployment.

---

## Phase 6: Baseline Test Execution Log

The following verification tests were executed against the codebase:

### 1. In-Process Mock Test (`mock_test.py`)
```text
=== Subscription Management System: In-Process Mock Test Suite ===
Target: Flask In-Memory SQLite | Mock Outbox Mailer | Mock Scheduled Jobs
[PASS] Step 01 - 40: All steps passed (Auth, Staff, Catalog, Quotations, Subscriptions, Billing, Invoices, Payments, Dashboard, Audit).
Mock Test Summary: 40 passed, 0 failed out of 40 steps (100.0%)
```

### 2. Automated Pytest Suite (`backend/tests/`)
```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.2.0, pluggy-1.7.0
rootdir: A:\Coding\Oddo\backend, configfile: pytest.ini
collected 20 items

backend\tests\test_auth.py::test_signup_success PASSED                   [  5%]
backend\tests\test_auth.py::test_signup_duplicate_email PASSED           [ 10%]
backend\tests\test_auth.py::test_signup_weak_passwords PASSED            [ 15%]
backend\tests\test_auth.py::test_login_and_logout PASSED                 [ 20%]
backend\tests\test_billing_job.py::test_billing_job_idempotence_and_no_duplicates PASSED [ 25%]
backend\tests\test_billing_job.py::test_billing_time_travel_and_paused_closed_skipped PASSED [ 30%]
backend\tests\test_catalog.py::test_catalog_crud_and_validation PASSED   [ 35%]
backend\tests\test_dashboard.py::test_dashboard_metrics_and_filters PASSED [ 40%]
backend\tests\test_lifecycle.py::test_subscription_lifecycle_and_plan_flags PASSED [ 45%]
backend\tests\test_password_reset.py::test_password_reset_flow PASSED    [ 50%]
backend\tests\test_password_reset.py::test_expired_token_rejected PASSED [ 55%]
backend\tests\test_payments.py::test_payments_partial_full_overpayment_and_refunds PASSED [ 60%]
backend\tests\test_pdf.py::test_invoice_pdf_endpoint_returns_valid_pdf PASSED [ 65%]
backend\tests\test_pricing.py::test_pricing_percentage_and_tax PASSED    [ 70%]
backend\tests\test_pricing.py::test_pricing_fixed_discount PASSED        [ 75%]
backend\tests\test_pricing.py::test_pricing_min_quantity_restriction PASSED [ 80%]
backend\tests\test_pricing.py::test_pricing_expired_and_usage_limit PASSED [ 85%]
backend\tests\test_quotations.py::test_quotation_creation_and_confirm PASSED [ 90%]
backend\tests\test_roles.py::test_role_restrictions_on_admin_routes PASSED [ 95%]
backend\tests\test_roles.py::test_customer_isolation PASSED              [100%]
============================= 20 passed in 9.97s ==============================
```

### 3. Frontend Vitest Suite (`npm run test`)
```text
 ✓ src/test/passwordPolicy.test.ts (5 tests)
 ✓ src/test/planFlags.test.ts (4 tests)
 ✓ src/test/invoiceActionRules.test.ts (3 tests)
 ✓ src/test/money.test.ts (3 tests)
 ✓ src/test/routeGuards.test.tsx (3 tests)
Test Files: 5 passed (5) | Tests: 18 passed (18)
```

### 4. Frontend Production Build (`npm run build`)
```text
✓ 2466 modules transformed.
dist/index.html                   0.57 kB
dist/assets/index-BsAWSB3F.css   26.98 kB
dist/assets/index-im21kNFL.js   863.47 kB
✓ built in 9.16s
```

### 5. Database Seed Execution (`seed.py`)
```text
Database seeding completed.
Admin account: admin@example.com (Admin@12345)
Staff accounts: staff1@example.com, staff2@example.com
Customer accounts: customer1@example.com, customer2@example.com, customer3@example.com
```

---

## Phase 7: Add-On Features Assessment (Spec Section 15)

| Add-On Feature (Section 15) | Implementation Status | Technical Observation |
|---|---|---|
| 1. Online payment gateway | **Absent** | Not implemented (out of scope). |
| 2. Automatic payment reminders (dunning) | **Absent** | No automated email reminder cron job. |
| 3. Pro-rata billing | **Absent** | Mid-cycle proration not implemented. |
| 4. Plan upgrade / downgrade | **Absent** | Plan switching logic not implemented. |
| 5. Credit notes & customer wallet | **Absent** | Overpayments blocked rather than banked. |
| 6. Free trials & setup fees | **Absent** | Trial periods not modeled. |
| 7. Usage-based billing | **Absent** | Pure subscription billing model. |
| 8. Coupon codes | **Partial** | Admin discount rules exist; customer-entered coupons absent. |
| 9. Multi-currency and multi-tax (GST) | **Partial** | Single INR currency; tax rules engine implemented. |
| 10. Renewal reminders | **Absent** | Background reminder notifications absent. |
| 11. Auto-renew toggle | **Absent** | Manual renew transition supported. |
| 12. Email and SMS notifications | **Implemented** | Password reset & PDF invoice dispatch via `MailService`. |
| 13. Downloadable invoice PDFs | **Implemented** | ReportLab dynamic PDF generation via `/invoices/:id/pdf`. |
| 14. Support tickets linked to subscription | **Absent** | Not implemented. |
| 15. Two-factor authentication (2FA) | **Absent** | Single-factor password auth. |
| 16. Advanced analytics (MRR, ARR, churn) | **Implemented** | Computed in SQL views (`v_dashboard_kpis`). |
| 17. Export to CSV / PDF | **Implemented** | Frontend CSV export utility (`csv.ts`) and PDF stream. |
| 18. Bulk actions | **Absent** | Bulk batch confirm/send not implemented. |
| 19. Notification centre for staff | **Absent** | Not implemented. |
| 20. Accounting integration | **Absent** | Not implemented. |
| 21. Webhooks & public API | **Absent** | Not implemented. |
| 22. Full audit trail viewer | **Partial** | Append-only DB table exists; UI viewer needs API endpoint. |
| 23. Dark-mode UI | **Implemented** | Frontend theme toggle supported. |

---

## Conclusion & Next Steps

The subsystems contain all foundational domain logic, but the system cannot function end-to-end without resolving the contractual mismatches identified above.

Since only **4 files** contain mock-related code (well below the 20-file deletion threshold), we will proceed in controlled batches on branch `integration/cleanup`:
1. **Batch 1 (API Contract & Routing Alignment):** Align base URL `/api/v1`, wire JWT Bearer headers, support `_paise` monetary serializers, and add missing profile/customer routes.
2. **Batch 2 (Business Rules & RBAC Hardening):** Restrict payment and invoice confirm routes from unauthorized customer mutation; enforce partial payment cancellation safeguards; eliminate reset token leakage.
3. **Batch 3 (Missing Endpoints Implementation):** Expose `/quotation-templates`, `/me/*`, `/invoices/outstanding`, `/audit-logs`, and standalone `/refunds` CRUD.
4. **Batch 4 (Mock Removal & Cleanup):** Remove `brightloop_mock_token` references, remove `VITE_USE_MOCK`, and align login quick-fill credentials with seeded database accounts.
5. **Batch 5 (End-to-End Smoke Verification):** Execute end-to-end user lifecycle test and verify duplicate-billing idempotence.
