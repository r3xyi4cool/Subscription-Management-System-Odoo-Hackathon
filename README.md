# Brightloop Subscription Management System (SMS)

A complete, robust, enterprise-grade local Subscription Management and Billing platform designed for seamless setup and operation on any local developer workstation.

---

## 1. Project Overview

**Brightloop SMS** automates recurring billing lifecycles, self-service customer subscriptions, quotation-to-order conversions, invoicing with downloadable PDF generation, payment recording, refund thresholds, and real-time business telemetry.

Key Highlights:
* **Zero Cloud / Zero External Service Dependencies:** Runs 100% locally on your machine with host Python and Node.js.
* **In-App Customer Notifications:** No SMTP, SendGrid, or external mail server required. Communication flows directly into the customer portal feed with interactive unread counters and actionable deep-links.
* **Deterministic Decimal Arithmetic:** All financial transactions and pricing models utilize SQL `DECIMAL`/`NUMERIC(12,2)` precision with half-up rounding.
* **High-Throughput Analytics:** Live SQL aggregations respond under 100ms even across 5,000+ active subscriptions and 10,000+ invoices.

---

## 2. Architecture

Brightloop SMS is structured as an integrated three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React 18 + Vite)                │
│  - TypeScript & Tailwind CSS UI                             │
│  - TanStack Query (Server State Cache)                      │
│  - Code-split routes & vendor chunking (< 400kB chunks)     │
│  - Customer Portal (/portal/*) & Staff Console (/admin/*)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON REST (/api/v1)
                               │ JWT Bearer Authentication
┌──────────────────────────────▼──────────────────────────────┐
│                    Backend (Python Flask)                   │
│  - Modular Blueprints: Auth, Catalog, Sales, Billing, etc.  │
│  - PricingService: Round-half-up Decimal calculations       │
│  - NotificationService: In-app alerts & deduplication       │
│  - Worker: File-locked single-instance billing runner       │
└──────────────────────────────┬──────────────────────────────┘
                               │ SQLAlchemy ORM & Migrations
┌──────────────────────────────▼──────────────────────────────┐
│                    Database (SQLite / PostgreSQL)           │
│  - Dual engine support: Zero-setup SQLite or PostgreSQL 15+ │
│  - Strict unique constraints preventing double billing      │
│  - Composite indexes on status, due date, & billing dates   │
│  - Append-only immutable audit trail                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Prerequisites

To clone and run Brightloop SMS locally, you only need:
* **Python:** Version 3.10 or higher (`python --version`)
* **Node.js:** Version 18 or higher with npm (`node --version`)
* **Git:** For local version control

*Note: No Docker, Kubernetes, Nginx, or cloud accounts are required.*

---

## 4. Local Clone & Run in 3 Commands

### On Windows:
```cmd
git clone <repository_path>
setup.bat
start.bat
```

### On Linux / macOS:
```bash
git clone <repository_path>
chmod +x *.sh
./setup.sh
./start.sh
```

`setup` creates the Python virtual environment, installs backend dependencies, initializes migrations, seeds initial data, and builds the frontend.  
`start` launches the Backend API (port 5000), Background Worker, and Frontend (port 5173).

Open **http://localhost:5173** in your browser.

---

## 5. Features Matrix

| ID | Module / Feature | Status | Evidence |
| :--- | :--- | :--- | :--- |
| **F1** | Customer Sign Up & Login | Done | `frontend/src/features/auth/` |
| **F2** | Forgot & Reset Password | Done | `frontend/src/features/auth/ResetPasswordPage.tsx` |
| **F3** | Role-Based Route Guards | Done | `frontend/src/app/guards/RequireRole.tsx` |
| **F4** | Customer Dashboard | Done | `frontend/src/features/portal/CustomerDashboardPage.tsx` |
| **F5** | My Subscriptions View | Done | `frontend/src/features/portal/CustomerSubscriptionsPage.tsx` |
| **F6** | My Invoices & PDF Download | Done | `frontend/src/features/portal/CustomerInvoicesPage.tsx` |
| **F7** | Account Settings & Password Change | Done | `frontend/src/features/portal/CustomerAccountPage.tsx` |
| **F8** | Staff Operational Screens | Done | `frontend/src/features/subscriptions/`, `invoices/` |
| **F9** | Admin Configuration Screens | Done | `frontend/src/features/staff/`, `catalogue/`, `audit/` |
| **F10** | Executive Dashboard with Filters | Done | `frontend/src/features/dashboard/DashboardPage.tsx` |
| **B1** | Auth, Password Rules & Uniqueness | Done | `backend/app/routes/auth.py` |
| **B2** | Password Reset Token Workflow | Done | `backend/app/services/auth_service.py` |
| **B3** | Role-Based Access Control | Done | `backend/app/utils/decorators.py` |
| **B4** | Staff Management API | Done | `backend/app/routes/staff.py` |
| **B5** | Products & Variants Catalog | Done | `backend/app/routes/catalog.py` |
| **B6** | Plans & Lifecycle Policy Flags | Done | `backend/app/models/catalog.py` |
| **B7** | Discount Engine & Limits | Done | `backend/app/services/pricing_service.py` |
| **B8** | Tax Calculation Engine | Done | `backend/app/services/pricing_service.py` |
| **B9** | Quotations & Templates | Done | `backend/app/routes/quotations.py` |
| **B10**| Subscription Lifecycle State Machine| Done | `backend/app/routes/subscriptions.py` |
| **B11**| Idempotent Recurring Billing Worker | Done | `backend/app/worker.py` |
| **B12**| Invoices & ReportLab PDF Export | Done | `backend/app/services/pdf_service.py` |
| **B13**| Payments & Overdue Tracking | Done | `backend/app/routes/payments.py` |
| **B14**| Refunds & Cancellation Limits | Done | `backend/app/routes/refunds.py` |
| **B15**| Dashboard SQL Telemetry & Aggregations| Done| `backend/app/routes/dashboard.py` |
| **D1** | Auth, Customer & Staff Schema | Done | `backend/app/models/auth.py`, `customer.py` |
| **D2** | Catalog Schema & Foreign Keys | Done | `backend/app/models/catalog.py` |
| **D3** | Sales & Subscription Lines | Done | `backend/app/models/subscription.py` |
| **D4** | Billing Schema & Numeric Types | Done | `backend/app/models/billing.py` |
| **D5** | Integrity Rules & Double Billing Guard| Done| `backend/tests/test_concurrency.py` |
| **D6** | High-Performance Indexes | Done | Composite indexes on due dates & billing periods |
| **D7** | Comprehensive Lifecycle Seed | Done | `backend/seed.py`, `seed.py` |
| **D8** | Backup & Disaster Recovery Scripts | Done | `backup.bat`, `backup.sh`, `restore.bat`, `restore.sh` |
| **D9** | Immutable Audit Trail | Done | `backend/app/models/audit.py` |
| **M1–M9**| Operational Management Routines | Done | CLI commands, worker runners, backup tools |

---

## 6. Default Credentials

The initial seed populates the following accounts for immediate local testing:

| Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@brightloop.io` | `Admin@12345` | Global system control, staff management, audit log |
| **Staff** | `staff@brightloop.io` | `Staff@12345` | Sales operations, quotations, subscriptions, billing |
| **Customer** | `customer@demo.com` | `Demo@12345` | Demo customer portal with subscriptions & invoices |

---

## 7. In-App Notifications (Replaces Email)

In this local environment, there is **no external mail provider**. All customer-directed messages are routed to an in-app notification engine:

* **Invoice Generated:** An alert is created with an instant link to the statement.
* **Payment Due / Overdue:** Amber/Red alert banners appear on the customer dashboard, and automated reminders are placed in the notification inbox.
* **Payment Received:** A confirmation notification is dispatched with the settled amount.
* **Interactive UI:** The customer top navigation bar features a live unread bell counter with a preview dropdown and a dedicated management page (`/portal/notifications`) with "Mark all as read".

---

## 8. Local Background Worker

The billing and dunning worker runs locally via `backend/app/worker.py` and features a single-instance file lock (`.worker.lock`) to prevent concurrent execution conflicts:

```bash
# Run worker continuously (polls every 60 seconds)
python -m backend.app.worker --interval 60

# Run a single evaluation tick
python -m backend.app.worker --once

# Time-travel test (simulate billing on a future date)
python -m backend.app.worker --once --as-of 2026-12-01
```

The worker performs three key jobs on every tick:
1. **Billing Catch-Up:** Evaluates subscriptions where `next_billing_date <= today` and creates invoices idempotently.
2. **Payment Reminders:** Identifies unpaid invoices due within 3 days or overdue, generating deduplicated daily reminders.
3. **Auto-Close:** Automatically closes subscriptions where the plan has `auto_close = True` and period has expired.

---

## 9. Local Security & CORS

* **CORS Lockdown:** Local backend accepts requests strictly from `http://localhost:5173`, `http://127.0.0.1:5173`, and `http://localhost:3000`.
* **Security Headers:** Every response includes `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and strict script policies.
* **Password Policy:** Enforces $\ge 8$ characters, uppercase, lowercase, numbers, and symbols.
* **Staff Reset Helper:** Local staff can click **Generate Reset Link** on any customer page to copy a 30-minute password reset link to the clipboard without needing an outbox check.

---

## 10. Performance Benchmarks

Measured on a standard local workstation with **5,000 subscriptions**, **1,000 customers**, and **10,000 invoices**:

* `GET /dashboard/summary`: **83.72 ms** (Target: $< 2.0\text{ s}$)
* `GET /dashboard/overdue`: **37.78 ms** (Target: $< 2.0\text{ s}$)
* `GET /invoices/outstanding`: **31.58 ms** (Target: $< 2.0\text{ s}$)
* `GET /subscriptions` (paginated): **24.82 ms** (Target: $< 1.0\text{ s}$)
* **Billing Worker Cycle:** **3.57 ms** (Target: $< 5.0\text{ s}$)
* **Frontend Bundle:** Chunks cleanly split (`vendor-react`, `vendor-query`, `vendor-icons`), zero build warnings, dynamic route code splitting.

*For complete details, see [docs/PERFORMANCE.md](file:///a:/Coding/Oddo/docs/PERFORMANCE.md).*

---

## 11. Database & Migrations

* **Default Engine:** SQLite (stored in `instance/subscription_system.db`).
* **PostgreSQL Support:** Fully compatible by changing `DATABASE_URL` in `.env` to `postgresql://user:pass@localhost:5432/dbname`.
* **Alembic Migrations:** Run `flask db upgrade` to apply schema versions.
* **Double-Billing Safeguard:** Database constraint `uq_invoice_subscription_period UNIQUE(subscription_id, billing_period_start, billing_period_end)` guarantees no subscription is billed twice for the same period.

---

## 12. API Endpoints Reference

Base URL: `http://localhost:5000/api/v1`

* **Auth:** `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`, `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /auth/change-password`
* **Portal:** `GET /me/dashboard`, `GET /me/subscriptions`, `GET /me/invoices`, `GET /me/notifications`, `PATCH /me/notifications/{id}/read`
* **Catalog:** `GET|POST /products`, `POST /products/{id}/variants`, `GET|POST /plans`, `GET|POST /discounts`, `GET|POST /taxes`
* **Sales:** `GET|POST /quotation-templates`, `GET|POST /quotations`, `POST /quotations/{id}/confirm`, `GET /quotations/{id}/pdf`
* **Subscriptions:** `GET /subscriptions`, `POST /subscriptions/{id}/activate`, `POST /subscriptions/{id}/pause`, `POST /subscriptions/{id}/resume`, `POST /subscriptions/{id}/close`
* **Invoices:** `GET /invoices`, `GET /invoices/outstanding`, `POST /invoices/{id}/confirm`, `POST /invoices/{id}/send`, `GET /invoices/{id}/pdf`
* **Payments & Refunds:** `POST /payments`, `POST /refunds`, `PATCH /refunds/{id}`
* **Analytics:** `GET /dashboard/summary`, `GET /dashboard/overdue`, `GET /audit-logs`

*For complete documentation, see [docs/API.md](file:///a:/Coding/Oddo/docs/API.md).*

---

## 13. Customer Portal vs Staff Console

| Feature | Customer Portal (`/portal/*`) | Staff Console (`/admin/*`) |
| :--- | :--- | :--- |
| **Authentication** | Customer login & signup | Admin & Staff login |
| **Dashboard** | My spending, balance owed, alerts | Company MRR, ARR, churn, collections |
| **Subscriptions** | View owned active/closed services | Create, confirm, pause, activate, close |
| **Invoicing** | View personal invoices, download PDF | Create, confirm, mark sent, cancel |
| **Payments** | View payment receipts & balance due | Record payments, issue & approve refunds |
| **Communications**| Live in-app notifications & alerts | Send invoice notices, staff reset helper |
| **Audit Logs** | Not accessible | Full immutable audit event log (Admin) |

---

## 14. Troubleshooting & FAQ

**Q: Port 5000 or 5173 is already in use.**  
*A: Stop the process using that port or specify a different port in `.env` (`PORT=5001`) and update `frontend/vite.config.ts` proxy target.*

**Q: "Database locked" or SQLite concurrent write warnings.**  
*A: SQLite handles concurrent reads well; for production or parallel stress testing, switch to PostgreSQL via `DATABASE_URL` in `.env`.*

**Q: Where do password reset emails go?**  
*A: No external emails are sent. Reset links are logged directly to the backend terminal stdout. Additionally, staff can copy reset links from the customer detail page in the console.*

---

## 15. Backup & Restore

Quick backup:
```cmd
backup.bat    :: Creates backups/subscription_system_YYYYMMDD_HHMMSS.db
```
Quick restore:
```cmd
restore.bat backups\subscription_system_YYYYMMDD_HHMMSS.db
```
On Linux/macOS, use `./backup.sh` and `./restore.sh`.

---

## 16. Design Decisions

1. **Host-Native Execution:** Strictly host Python and Node.js without container or virtualization layers for zero-overhead local development.
2. **Deterministic Rounding:** `ROUND_HALF_UP` on 2 decimal places to ensure currency math matches real-world accounting rules.
3. **Audit Immutability:** Audit trail records user IDs, timestamps, and JSON snapshots of changes without update/delete capabilities.

---

## 17. Verification & Testing

Run all test suites locally:

```bash
# Backend pytest suite (35 tests, 100% pass)
python -m pytest backend/tests/

# Frontend component & guard suite (18 tests, 100% pass)
npm --prefix frontend test -- --run

# Security AST scanner (0 issues)
bandit -r backend/app

# Production bundle compilation
npm --prefix frontend run build
```

---

## 18. License & Authors

Brightloop Subscription Management System (SMS)  
Developed by the Brightloop Engineering Team.
Distributed for local development and integration evaluation.
