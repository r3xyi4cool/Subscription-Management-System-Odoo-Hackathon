# Brightloop SMS - REST API Reference

The Brightloop Subscription Management System (SMS) exposes a RESTful JSON API rooted at `/api/v1`.

All authenticated requests require an HTTP header:
```http
Authorization: Bearer <jwt_access_token>
```

---

## 1. Authentication Endpoints

### `POST /api/v1/auth/signup`
Creates a new customer account.
* **Public**
* **Request Body:**
  ```json
  {
    "email": "customer@example.com",
    "password": "StrongPassword@123",
    "name": "Jane Doe",
    "company_name": "Acme Corp",
    "phone": "+1-555-0100"
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "success": true,
    "data": {
      "user": { "id": 1, "email": "customer@example.com", "role": "customer" },
      "customer": { "id": 1, "name": "Jane Doe", "company_name": "Acme Corp" },
      "access_token": "eyJhbGciOi...",
      "refresh_token": "eyJhbGciOi..."
    }
  }
  ```

### `POST /api/v1/auth/login`
Authenticates an existing user (Admin, Staff, or Customer).
* **Public**
* **Request Body:** `{"email": "admin@brightloop.io", "password": "Admin@12345"}`
* **Response (200 OK):** User metadata and JWT tokens.

### `POST /api/v1/auth/logout`
Revokes the session.
* **Requires Authentication**

### `POST /api/v1/auth/forgot-password`
Initiates password reset; emits reset link to console log.
* **Public**
* **Request Body:** `{"email": "user@example.com"}`

### `POST /api/v1/auth/reset-password`
Resets password using a single-use 30-minute token.
* **Public**
* **Request Body:** `{"token": "token_string", "new_password": "NewStrongPassword@123"}`

### `POST /api/v1/auth/change-password`
Changes password for an authenticated session.
* **Requires Authentication**
* **Request Body:** `{"current_password": "OldPassword@123", "new_password": "NewPassword@123"}`

---

## 2. Customer Portal Endpoints (`/me/*`)

These endpoints are strictly isolated to the authenticated customer's own records.

### `GET /api/v1/me/dashboard`
Returns portal summary: active subscriptions, balance owed, unread notifications, upcoming invoices.

### `GET /api/v1/me/subscriptions`
Returns paginated list of subscriptions owned by the customer.

### `GET /api/v1/me/invoices`
Returns paginated list of invoices billed to the customer.

### `GET /api/v1/me/notifications`
Returns paginated in-app notifications (newest first).

### `GET /api/v1/me/notifications/unread-count`
Returns `{"data": {"unread_count": N}}`.

### `PATCH /api/v1/me/notifications/{id}/read`
Marks a specific notification as read.

### `POST /api/v1/me/notifications/read-all`
Marks all customer notifications as read.

---

## 3. Staff & Admin Management

### `GET /api/v1/staff`
List staff members (Admin only).

### `POST /api/v1/staff`
Create staff profile (Admin only).

### `PATCH /api/v1/staff/{id}`
Update/deactivate staff (Admin only).

### `GET /api/v1/customers`
List customers (Staff & Admin).

### `GET /api/v1/customers/{id}`
Customer details with full subscription and invoice histories.

### `POST /api/v1/customers/{id}/send-reset-link`
Generates a 30-minute reset link directly for local support assistance.

---

## 4. Product Catalog & Rules

* `GET /api/v1/products` / `POST /api/v1/products`
* `POST /api/v1/products/{id}/variants`
* `GET /api/v1/plans` / `POST /api/v1/plans`
* `GET /api/v1/discounts` / `POST /api/v1/discounts`
* `GET /api/v1/taxes` / `POST /api/v1/taxes`

---

## 5. Quotations & Subscriptions

* `GET /api/v1/quotation-templates` / `POST /api/v1/quotation-templates`
* `GET /api/v1/quotations` / `POST /api/v1/quotations`
* `POST /api/v1/quotations/{id}/confirm` (Converts quotation to confirmed subscription)
* `GET /api/v1/quotations/{id}/pdf` (Downloads quotation PDF)
* `GET /api/v1/subscriptions`
* `POST /api/v1/subscriptions/{id}/activate`
* `POST /api/v1/subscriptions/{id}/pause`
* `POST /api/v1/subscriptions/{id}/resume`
* `POST /api/v1/subscriptions/{id}/close`

---

## 6. Billing, Invoices & Payments

* `POST /api/v1/billing/run` (or `/api/v1/billing/trigger`) — Executes idempotent billing evaluation
* `GET /api/v1/invoices`
* `GET /api/v1/invoices/outstanding`
* `POST /api/v1/invoices/{id}/confirm`
* `POST /api/v1/invoices/{id}/send` (Marks as Sent, emits in-app notification)
* `POST /api/v1/invoices/{id}/cancel`
* `GET /api/v1/invoices/{id}/pdf` (Downloads PDF invoice)
* `POST /api/v1/payments` (Records payment against invoice)
* `POST /api/v1/refunds` (Issues payment refund within threshold)
* `PATCH /api/v1/refunds/{id}` (Approves/processes refund)

---

## 7. Executive Telemetry & Analytics

* `GET /api/v1/dashboard/summary` (Supports `start_date`, `end_date`, `customer_id`, `plan_id`, `product_id`, `status` filters)
* `GET /api/v1/dashboard/overdue` (Lists overdue invoice ledger)
* `GET /api/v1/audit-logs` (Paginated immutable change log, Admin only)

