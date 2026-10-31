# Subscription Management System - Backend API

A clean, modular, production-ready Python **Flask** REST API for subscription billing and lifecycle management. Designed to easily decouple from SQLite dummy development storage and integrate with team-managed PostgreSQL / MySQL databases without application code changes.

---

## 1. Quick Start & Setup

### Prerequisites
- Python 3.11+
- Git

### Installation & Environment Setup

#### On Mac / Linux:
```bash
# Clone and enter workspace
git clone <repo_url>
cd <repo_directory>

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Seed database with initial data
python seed.py
# (Alternative: flask --app run:app seed)

# Start API server
python run.py
```

#### On Windows (PowerShell / Command Prompt):
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env

# Seed database
python seed.py

# Start API server
python run.py
```

The API will be live at `http://127.0.0.1:5000/api/v1`.
Interactive Swagger UI documentation is available at `http://127.0.0.1:5000/api/docs`.

---

## 2. Seeded Credentials

When running `python seed.py` or `flask seed`, the following default test accounts are seeded:

| Role | Email | Password | Details |
|---|---|---|---|
| **Admin** | `admin@example.com` | `Admin@12345` | Global admin access (overridden via `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`) |
| **Staff** | `staff1@example.com` | `Staff@12345` | Alice Smith (Sales Department) |
| **Staff** | `staff2@example.com` | `Staff@12345` | Bob Jones (Support Department) |
| **Customer** | `customer1@example.com` | `Cust@12345` | Acme Corp (Has active subscription, paid invoice, overdue invoice) |
| **Customer** | `customer2@example.com` | `Cust@12345` | Beta LLC |
| **Customer** | `customer3@example.com` | `Cust@12345` | Gamma Tech |

---

## 3. Running Tests & Smoke Verification

### 3.1 In-Process Mock Test (`mock_test.py`)
Run the mock test suite without spinning up a live server or binding ports. Uses Flask's in-memory client and SQLite:

```bash
python mock_test.py
```
*40 end-to-end steps covering all 8 modules (Auth, Staff, Catalog, Quotations, Subscriptions, Billing, Invoices & PDF, Payments & Refunds, Dashboards, Audit Logs).*

### 3.2 Pytest Suite with Code Coverage
The automated pytest test suite uses a fresh in-memory SQLite database per test run, validating all core features:

```bash
# Run pytest with full coverage report
PYTHONPATH=. pytest backend/tests/ --cov=backend/app --cov-report=term-missing
```

### 3.2 Standalone Smoke Test (`test_backend.py`)
`test_backend.py` is an independent script depending solely on `requests` and the Python standard library. It executes an end-to-end 28-step test against the live HTTP server.

```bash
# 1. In one terminal, start the server:
python run.py

# 2. In a second terminal, execute the smoke test:
python test_backend.py
```

Expected output:
```
=== Starting Smoke Test against http://127.0.0.1:5000/api/v1 ===
[PASS]   1. health check
[PASS]   2. signup valid
...
[PASS]   27. dashboard responds in under 2 seconds - Took 0.005s
[PASS]   28. logout
=============================================
Test Summary: 28 passed, 0 failed, 0 skipped
=============================================
```

### 3.3 Dashboard Performance Benchmark (5,000+ Subscriptions)
Verifies that aggregate dashboard calculations run under 2 seconds on 5,000 subscriptions:

```bash
python seed_benchmark.py
```
*Benchmark result: typically responds in ~0.02 seconds using optimized SQL aggregate queries and indexes.*

---

## 4. Swapping Dummy SQLite for Real Database (PostgreSQL / MySQL)

The backend uses SQLAlchemy ORM with standard ANSI SQL constructs and no SQLite-specific constraints or types.

### Steps to Switch to PostgreSQL / MySQL:
1. **Update `.env`**:
   Change `DATABASE_URL`:
   ```env
   # PostgreSQL
   DATABASE_URL=postgresql://user:password@localhost:5432/subscription_db

   # MySQL
   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/subscription_db
   ```
2. **Install DB Driver** in your venv:
   - For PostgreSQL: `pip install psycopg2-binary`
   - For MySQL: `pip install pymysql`
3. **Run Migrations or Seed**:
   ```bash
   flask db init
   flask db migrate -m "Initial schema"
   flask db upgrade
   python seed.py
   ```
4. **Run Pytest**:
   ```bash
   pytest backend/tests/
   ```

All database models reside cleanly in `backend/app/models/`, structured by domain (`auth.py`, `customer.py`, `staff.py`, `catalog.py`, `quotation.py`, `subscription.py`, `billing.py`, `audit.py`).

---

## 5. Pricing Calculation Engine (Order of Operations)

All pricing calculations are centralized in `PricingService.calculate_line(...)` (`backend/app/services/pricing_service.py`) and use `Decimal` with `ROUND_HALF_UP` to 2 decimal places:

$$\text{Line Subtotal} = (\text{Product Sales Price} + \text{Variant Extra Price}) \times \text{Quantity}$$

1. **Base Line Subtotal**:
   - `unit_price = Decimal(product.sales_price)`
   - `variant_price = Decimal(variant.extra_price if variant else 0.00)`
   - `subtotal_raw = (unit_price + variant_price) * quantity`
2. **Discount Evaluation**:
   Discount applies only if:
   - `discount.is_active is True`
   - `start_date <= today <= end_date` (if dates are specified)
   - `used_count < usage_limit` (if limit is specified)
   - `quantity >= min_quantity` and `subtotal_raw >= min_purchase`
   - `discount.applies_to` matches context (`product`, `subscription`, or `all`).
   
   If eligible:
   - Percentage: $\text{Discount} = \text{round}(\text{subtotal\_raw} \times (\text{value} / 100), 2)$
   - Fixed: $\text{Discount} = \min(\text{subtotal\_raw}, \text{round}(\text{value}, 2))$
3. **Discounted Subtotal**:
   - $\text{Discounted Subtotal} = \max(0.00, \text{subtotal\_raw} - \text{Discount})$
4. **Tax Calculation**:
   - $\text{Tax Amount} = \text{round}(\text{Discounted Subtotal} \times (\text{tax.rate} / 100), 2)$
5. **Total**:
   - $\text{Line Total} = \text{Discounted Subtotal} + \text{Tax Amount}$

---

## 6. Feature Mapping Matrix (B1 - B15)

| Code | Feature Description | API Endpoints | Test Files |
|---|---|---|---|
| **B1** | Customer signup, login, logout, password rules, email uniqueness | `POST /auth/signup`<br/>`POST /auth/login`<br/>`POST /auth/logout` | `test_auth.py` |
| **B2** | Password reset: single-use, 30-min token, dev outbox email | `POST /auth/forgot-password`<br/>`POST /auth/reset-password` | `test_password_reset.py` |
| **B3** | Role-based access control (Admin, Staff, Customer) and data isolation | Global decorator `@role_required` | `test_roles.py` |
| **B4** | Staff management (Admin-only create, list, deactivate) | `POST /staff`<br/>`GET /staff`<br/>`PATCH /staff/{id}` | `test_roles.py`<br/>`test_backend.py` |
| **B5** | Products & Variants with price delta | `POST /products`, `GET /products`<br/>`POST /products/{id}/variants` | `test_catalog.py` |
| **B6** | Plans (daily, weekly, monthly, yearly, pause/close/renew flags) | `POST /plans`<br/>`GET /plans` | `test_catalog.py`<br/>`test_lifecycle.py` |
| **B7** | Discount rules (fixed/percentage, min quantity, expiry, limits) | `POST /discounts`<br/>`GET /discounts` | `test_pricing.py`<br/>`test_catalog.py` |
| **B8** | Tax calculation per invoice line | `POST /taxes`<br/>`GET /taxes` | `test_pricing.py` |
| **B9** | Quotations & Templates; expiry check | `POST /quotations`<br/>`POST /quotations/{id}/confirm` | `test_quotations.py` |
| **B10** | Subscription lifecycle (Draft -> Confirmed -> Active -> Paused -> Closed) | `GET /subscriptions`<br/>`POST /subscriptions/{id}/activate`<br/>`POST /subscriptions/{id}/pause` | `test_lifecycle.py` |
| **B11** | Idempotent billing job, APScheduler, missed period catch-up | `POST /billing/run`<br/>`flask run-billing` | `test_billing_job.py` |
| **B12** | Invoice actions (confirm, send email, PDF export, cancel) | `GET /invoices`<br/>`POST /invoices/{id}/confirm`<br/>`GET /invoices/{id}/pdf` | `test_pdf.py`<br/>`test_backend.py` |
| **B13** | Payment recording, full/partial payment, overdue listing | `POST /payments`<br/>`GET /invoices/overdue` | `test_payments.py` |
| **B14** | Refunds & Cancellations (refund limit validation) | `POST /invoices/{id}/refund`<br/>`POST /subscriptions/{id}/close` | `test_payments.py` |
| **B15** | Dashboard summary metrics & SQL aggregation filters | `GET /dashboard/summary` | `test_dashboard.py`<br/>`seed_benchmark.py` |

---

## 7. Architectural Decisions & Assumptions

1. **Pluggable Mail Service**:
   - `MAIL_BACKEND=dev` (default) writes emails to the local console and serializes JSON records to `backend/outbox/` for zero-setup local testing.
   - Setting `MAIL_BACKEND=smtp` in `.env` utilizes standard SMTP with TLS.
2. **Single-Use Reset Tokens**:
   - Generated using `secrets.token_urlsafe(32)`.
   - Expire in 30 minutes, stored with `reset_token_used` flag to ensure they cannot be reused.
3. **Double-Billing Safeguard**:
   - Enforced by database constraint: `UniqueConstraint('subscription_id', 'billing_period_start', name='uq_invoice_sub_period')`.
   - The billing engine advances subscription periods safely and catches up missed periods without skipping or duplicating.
4. **Decimal Arithmetic**:
   - All monetary fields use `db.Numeric(12, 2)` mapped to Python `decimal.Decimal` to eliminate binary floating-point rounding inaccuracies.
5. **Dashboard Optimization**:
   - Dashboard queries run SQL `func.count()`, `func.sum()`, and `func.coalesce()` directly in the database engine, with indexed foreign keys and status columns. Seeding 5,000 subscriptions proves response latency remains under 0.03 seconds.

