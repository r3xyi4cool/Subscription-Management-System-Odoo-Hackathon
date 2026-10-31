# Brightloop SMS - REST API Contract & Specification

This specification defines the complete HTTP REST API contract for the Subscription Management System (SMS) at Brightloop Software.
Both the front-end client (`frontend/src/api/`) and the mock backend (`frontend/src/mock/`) strictly adhere to this contract. This document serves as the implementation blueprint for the Python + Flask + SQLite backend.

---

## 1. Global Architectural Conventions

### Base URL & Environment
- Development Proxy: `http://localhost:5173/api` proxies to `http://localhost:5000/api`
- Header / Content-Type: `application/json` (unless downloading PDF binary `application/pdf`)
- Request Credentials: `credentials: "include"` on all requests (for session cookie exchange)
- CSRF Protection: `X-CSRF-Token` header sent on `POST`, `PUT`, `PATCH`, `DELETE` matching `csrf_token` cookie

### Monetary Arithmetic
- **Never use floating-point types for currency.**
- All money is stored and transmitted as **integer paise** (₹1.00 = 100 paise).
  - e.g., ₹2,500.00 is represented as `250000`.
- Tax and discount percentages are plain numbers (e.g. `18`, `10.5`).

### Date and Time Standards
- Dates: ISO 8601 Date strings `YYYY-MM-DD` (e.g., `2026-10-31`)
- Timestamps: UTC with trailing `Z` (e.g., `2026-10-31T10:00:00Z`)

### Standard Pagination Envelope
All list queries support: `?page=1&per_page=20&sort=created_at&order=desc&q=search_text`
```json
{
  "items": [ /* array of records */ ],
  "page": 1,
  "per_page": 20,
  "total": 134,
  "pages": 7
}
```

### Standard Error Response Envelope
Every non-2xx status code returns:
```json
{
  "error": {
    "code": "validation_error",
    "message": "Human readable summary of the error",
    "fields": {
      "email": ["Email already registered"],
      "amount_paise": ["Payment exceeds balance due"]
    }
  }
}
```
HTTP Status Codes used:
- `400`: Bad Request / Malformed JSON / Expired token
- `401`: Unauthorized / Session Expired
- `403`: Forbidden (insufficient role authorization or plan restriction)
- `404`: Entity Not Found
- `409`: State Conflict (e.g. confirming an expired quotation or invalid transition)
- `422`: Unprocessable Entity / Form Validation Failure
- `429`: Too Many Requests (e.g. 5 failed login attempts lockout)

---

## 2. API Endpoints Catalog

### 2.1 Authentication & Profile

#### `POST /api/auth/login`
- **Roles**: Public
- **Request Body**:
```json
{
  "email": "admin@brightloop.test",
  "password": "Demo@1234"
}
```
- **Response** (`200 OK`):
```json
{
  "user": {
    "id": "usr_admin_1",
    "email": "admin@brightloop.test",
    "role": "admin",
    "name": "Aditi Sharma",
    "phone": "+91 98765 43210",
    "company_name": "Brightloop Technologies",
    "is_active": true,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  },
  "session_token": "mock-token-xyz"
}
```
- **Error Codes**: `401 invalid_credentials`, `403 account_inactive`, `429 rate_limit_exceeded`.

#### `POST /api/auth/signup`
- **Roles**: Public (registers customer user)
- **Request Body**:
```json
{
  "name": "Vikram Malhotra",
  "email": "customer@brightloop.test",
  "password": "Demo@1234",
  "company_name": "Acme Cloud Solutions",
  "phone": "+91 98111 22334"
}
```
- **Response** (`201 Created`): Returns user object & session cookie.
- **Error Codes**: `422 validation_error` (duplicate email or weak password).

#### `GET /api/auth/me`
- **Roles**: Authenticated
- **Response** (`200 OK`): Current authenticated `User` object.
- **Error Codes**: `401 unauthorized`.

#### `PATCH /api/auth/me`
- **Roles**: Authenticated
- **Request Body**: `{ "name": "...", "phone": "...", "company_name": "..." }`
- **Response** (`200 OK`): Updated `User` object.

#### `POST /api/auth/forgot-password`
- **Roles**: Public
- **Request Body**: `{ "email": "customer@brightloop.test" }`
- **Response** (`200 OK`):
```json
{
  "message": "If an account exists with this email, a password reset link has been dispatched."
}
```

#### `POST /api/auth/reset-password`
- **Roles**: Public
- **Request Body**: `{ "token": "reset_xyz...", "password": "NewDemo@1234" }`
- **Response** (`200 OK`): `{ "message": "Your password has been successfully reset. You may now log in." }`
- **Error Codes**: `400 invalid_or_expired_token`, `422 validation_error`.

#### `POST /api/auth/logout`
- **Roles**: Authenticated
- **Response** (`200 OK`): `{ "message": "Successfully logged out" }`

---

### 2.2 Staff Management (Admin Only)

#### `GET /api/staff`
- **Roles**: `admin`
- **Query Params**: `page`, `per_page`, `sort`, `order`, `q`
- **Response** (`200 OK`): Paginated envelope of `StaffMember` items.

#### `POST /api/staff`
- **Roles**: `admin`
- **Request Body**:
```json
{
  "name": "Rohan Mehta",
  "email": "rohan@brightloop.test",
  "role": "staff",
  "department": "Billing Operations",
  "phone": "+91 98765 43211"
}
```
- **Response** (`201 Created`): `StaffMember` object.

#### `PATCH /api/staff/:id`
- **Roles**: `admin`
- **Request Body**: `{ "name": "...", "role": "...", "department": "...", "is_active": false }`
- **Response** (`200 OK`): Updated `StaffMember` object.

---

### 2.3 Customers

#### `GET /api/customers`
- **Roles**: `admin`, `staff`
- **Response** (`200 OK`): Paginated envelope of `Customer` items.

#### `GET /api/customers/:id`
- **Roles**: `admin`, `staff`, `customer` (customer can only access their own id)
- **Response** (`200 OK`): `CustomerDetail` object including `active_subscriptions_count`, `total_invoiced_paise`, and `outstanding_balance_paise`.

#### `POST /api/customers`
- **Roles**: `admin`, `staff`
- **Request Body**: Customer fields (`name`, `email`, `company_name`, `billing_address`, `gstin`, etc.)

#### `PATCH /api/customers/:id`
- **Roles**: `admin`, `staff`
- **Request Body**: Partial customer fields.

#### `POST /api/customers/:id/send-reset-link`
- **Roles**: `admin`, `staff`
- **Response** (`200 OK`): `{ "message": "Password reset link sent to ...", "reset_link": "..." }`

---

### 2.4 Catalogue: Products, Plans, Taxes, Discounts

#### `GET /api/products` & `GET /api/products/:id`
- **Roles**: Public/Authenticated
- **Response** (`200 OK`): Paginated `Product` items with `variants: [{ id, name, sku, extra_price_paise }]`.

#### `POST /api/products` & `PATCH /api/products/:id` & `DELETE /api/products/:id`
- **Roles**: `admin`
- **Request Body**:
```json
{
  "name": "Cloud Core Platform",
  "sku": "PRD-CORE-001",
  "type": "software",
  "sales_price_paise": 250000,
  "tax_rule_id": "tax_18",
  "variants": [
    { "name": "Standard Edition", "sku": "PRD-CORE-001-STD", "extra_price_paise": 0 },
    { "name": "Odoo Integrated", "sku": "PRD-CORE-001-ODOO", "extra_price_paise": 56000 }
  ]
}
```

#### `GET /api/plans` & `POST /api/plans` & `PATCH /api/plans/:id`
- **Roles**: Read (`all`), Write (`admin`)
- **Request Body**:
```json
{
  "name": "Professional Monthly",
  "code": "PRO_MONTHLY",
  "billing_period": "monthly",
  "min_quantity": 1,
  "auto_close": false,
  "allow_early_close": true,
  "allow_pause": true,
  "allow_renewal": true
}
```

#### `GET /api/taxes` & `POST /api/taxes` & `PATCH /api/taxes/:id`
- **Roles**: Read (`admin`, `staff`), Write (`admin`)
- **Request Body**: `{ "name": "GST 18%", "code": "GST_18", "rate_percent": 18 }`

#### `GET /api/discounts` & `POST /api/discounts` & `PATCH /api/discounts/:id`
- **Roles**: Read (`admin`, `staff`), Write (`admin`)
- **Request Body**:
```json
{
  "code": "VOLUME10",
  "name": "10% Volume Discount",
  "discount_type": "percent",
  "discount_value": 10,
  "scope": "subscription",
  "min_quantity": 10,
  "min_amount_paise": 500000,
  "usage_limit": 100
}
```

---

### 2.5 Quotations & Templates

#### `GET /api/quotation-templates` & `POST /api/quotation-templates`
- **Roles**: `admin`, `staff`
- **Request Body**: Template with default validity and line bundles.

#### `GET /api/quotations` & `POST /api/quotations`
- **Roles**: `admin`, `staff`
- **Request Body**:
```json
{
  "customer_id": "cust_1",
  "plan_id": "plan_monthly_pro",
  "validity_days": 15,
  "items": [
    {
      "product_id": "prod_1",
      "quantity": 5,
      "unit_price_paise": 250000,
      "tax_rate_percent": 18
    }
  ]
}
```

---

### 2.6 Subscriptions

#### `GET /api/subscriptions` & `GET /api/subscriptions/:id`
- **Roles**: `admin`, `staff`, `customer` (customer scoped)
- **Response** (`200 OK`): Paginated `Subscription` items with lines, status history, and plan rules.

#### `POST /api/subscriptions`
- **Roles**: `admin`, `staff`
- **Request Body**: Subscription setup with customer, plan, and lines.

#### State Transitions:
- `POST /api/subscriptions/:id/confirm` (staff/admin)
- `POST /api/subscriptions/:id/activate` (staff/admin)
- `POST /api/subscriptions/:id/pause` (staff/admin, or customer if `plan.allow_pause === true`)
- `POST /api/subscriptions/:id/resume` (staff/admin, customer)
- `POST /api/subscriptions/:id/renew` (staff/admin, or customer if `plan.allow_renewal === true`)
- `POST /api/subscriptions/:id/close` (staff/admin, or customer if `plan.allow_early_close === true`)
- **Body**: `{ "reason": "Optional feedback" }`
- **Error Codes**: `403 forbidden / early_close_not_permitted / pause_not_permitted`, `409 conflict` (e.g. expired quotation cannot be confirmed).

---

### 2.7 Invoices & Billing Scheduler

#### `GET /api/invoices` & `GET /api/invoices/:id`
- **Roles**: `admin`, `staff`, `customer` (customer scoped)

#### `POST /api/invoices/:id/confirm`
- **Roles**: `admin`, `staff`
- Locks lines, discounts, and taxes. Assigns official invoice number.

#### `POST /api/invoices/:id/send`
- **Roles**: `admin`, `staff`
- Dispatches statement to customer.

#### `POST /api/invoices/:id/cancel`
- **Roles**: `admin`, `staff`
- Allowed ONLY on draft or confirmed invoices with zero recorded payments.
- **Error Codes**: `422 cannot_cancel_paid`.

#### `GET /api/invoices/:id/pdf`
- **Roles**: `admin`, `staff`, `customer`
- Returns binary stream `Content-Type: application/pdf`.

#### `GET /api/invoices/outstanding`
- **Roles**: `admin`, `staff`
- Returns confirmed invoices where `balance_due_paise > 0`.

#### `POST /api/billing/run`
- **Roles**: `admin`, `staff`
- **Response** (`200 OK`):
```json
{
  "run_at": "2026-10-31T11:00:00Z",
  "created_count": 8,
  "skipped_count": 17,
  "failed_count": 0,
  "created": [
    {
      "subscription_id": "sub_1",
      "subscription_number": "SUB-2026-000001",
      "invoice_id": "inv_123",
      "invoice_number": "INV-2026-000061",
      "amount_paise": 590000
    }
  ],
  "skipped": [],
  "failed": []
}
```

---

### 2.8 Payments & Refunds

#### `GET /api/payments` & `POST /api/payments`
- **Roles**: `admin`, `staff`
- **POST Body**:
```json
{
  "invoice_id": "inv_1",
  "amount_paise": 250000,
  "payment_method": "bank_transfer",
  "payment_date": "2026-10-31",
  "reference": "UTR998877"
}
```
- **Error Codes**: `422 overpayment_rejected` (if `amount_paise > balance_due_paise`).

#### `GET /api/refunds` & `POST /api/refunds` & `PATCH /api/refunds/:id`
- **Flow**: `requested -> approved -> processed` (or `rejected`)
- **Limit Rule**: Staff can process refunds only up to ₹5,000.00 (`500000` paise). Higher amounts require Admin approval (`403 approval_limit_exceeded`).

---

### 2.9 Dashboard & Analytics

#### `GET /api/dashboard/summary`
- **Roles**: `admin`, `staff`
- **Query Params**: `plan_id`, `customer_id`
- **Response** (`200 OK`):
```json
{
  "active_subscriptions": 15,
  "revenue_collected_paise": 24500000,
  "amount_owed_paise": 3200000,
  "payments_received_count": 45,
  "overdue_invoices_count": 4,
  "overdue_amount_paise": 850000,
  "mrr_paise": 3150000,
  "arr_paise": 37800000,
  "churn_rate_percent": 8,
  "collection_rate_percent": 88,
  "revenue_trend": [
    { "date": "2026-05", "revenue_paise": 3800000, "invoiced_paise": 4200000 }
  ],
  "subscription_distribution": [
    { "name": "active", "count": 15 },
    { "name": "paused", "count": 2 }
  ]
}
```

#### `GET /api/dashboard/overdue`
- **Roles**: `admin`, `staff`
- Paginated confirmed invoices where `due_date < today && balance_due_paise > 0`.

#### `GET /api/me/dashboard`
- **Roles**: `customer`
- Summary for logged-in customer: `active_subscriptions_count`, `total_spent_paise`, `pending_invoices_count`, `balance_due_paise`, `next_renewal_date`.

---

### 2.10 Audit Logs (Admin Only)

#### `GET /api/audit-logs`
- **Roles**: `admin`
- Paginated log trail with action, entity_id, user, IP, and structured JSON `details`.

---

## 3. Notes for the Flask + SQLite Backend

When implementing the real Python + Flask + SQLite backend, follow these requirements:

1. **Session & Security**:
   - Store user sessions in Flask sessions backed by secure HttpOnly cookies (`session=...; HttpOnly; SameSite=Lax`).
   - Enable CSRF protection via `flask-wtf` or a custom decorator that sets a readable `csrf_token` cookie and verifies the `X-CSRF-Token` request header on mutating calls.
   - Configure CORS for `http://localhost:5173` with `supports_credentials=True`.

2. **Database Representation (SQLite)**:
   - SQLite does not have a decimal type. **Always use integer columns for money** (`INTEGER` column named with `_paise`, e.g. `amount_paise`, `sales_price_paise`, `balance_due_paise`).
   - Store dates as ISO strings `YYYY-MM-DD` and timestamps as `YYYY-MM-DDTHH:MM:SSZ`.
   - Store booleans as `INTEGER` (`0` or `1`) and serialize them to real JSON booleans `true` / `false`.
   - Field names must strictly match the `snake_case` definitions in `src/api/types.ts`.

3. **Calculation Order (Invoicing)**:
   - Strictly adhere to:
     1. Line item subtotal: `quantity * unit_price_paise`
     2. Line discount / Invoice discount: calculated on eligible lines/subtotal
     3. Taxable net: `subtotal - discount`
     4. Tax: GST calculated on the net taxable amount
     5. Total: `taxable_net + tax`

4. **Billing Job Idempotency**:
   - Create a unique constraint on `(subscription_id, billing_period_start)` in the `invoices` table.
   - When running the periodic billing job, catch up any overdue cycles and advance `next_billing_date` in the same SQLite transaction.
