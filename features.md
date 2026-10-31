# Subscription Management System: Product & Technical Documentation

*Prepared for Brightloop Software. Version 1.0*

## 1. Overview

The Subscription Management System (SMS) is one unified platform that runs the full life of a subscription business: setting up products and plans, turning quotes into subscriptions, generating invoices automatically, collecting payments, applying discounts and taxes, handling refunds and cancellations, and reporting revenue.

**Problems it replaces**

| Today at Brightloop | With the SMS |
| --- | --- |
| Subscriptions tracked in a spreadsheet | Central subscription register with lifecycle status |
| Renewals remembered by whoever notices | Automated renewal reminders and auto-renew rules |
| Invoices typed by hand | Invoices generated automatically from subscriptions |
| Payments matched by scrolling bank statements | Payments recorded against specific invoices |
| Revenue reports built quarterly by hand | Live dashboard with filters and summaries |

**Goals**

- No invoice is ever billed twice or skipped.
- Every role sees only what it is allowed to see.
- Every page responds in under two seconds, even with thousands of subscriptions.
- Finance can answer "how many active, how much collected, how much owed, what is overdue" in one place.

## 2. User Roles and Permissions

There are three roles. Role-based access control (RBAC) is enforced on the server for every request, not just hidden in the interface.

### 2.1 Admin

The admin controls the whole system.

- Customer details: view and manage all customers.
- Staff management: the only role that can add, edit, deactivate or remove staff.
- Products and plans: create products, variants and plans.
- Discount rules: create fixed-amount or percentage discounts (for example, 10% off for 10 items, or Rs 500 off a specific product).
- Tax rules: define tax rates and the conditions they apply to.
- Full visibility: payment amounts, invoices, subscriptions, refunds, reports and audit logs.
- Access to every feature available to staff and customers.

### 2.2 Staff

Internal team members with limited access to handle day-to-day work.

| Area | Capabilities |
| --- | --- |
| Customer management | View customer details, customer email, customer ID; trigger password reset links (staff never see or set raw passwords) |
| Subscription management | Create quotations, confirm subscriptions, activate, pause, renew and close subscriptions |
| Invoice management | Generate, view, confirm, send, print and cancel invoices |
| Payment management | Record payments, update payment details, check outstanding invoices |
| Dashboard | View active subscriptions, revenue, payments and overdue invoices |

Staff **cannot**: add staff, create products/plans, create discount or tax rules, or change system settings.

### 2.3 Customer

Customers use a self-service portal and see only their own data.

1. **Account management:** sign up with email and password, login and logout, unique email per account, forgot password, password reset through registered email, account settings.
2. **My subscriptions:** subscription number, plan details, products and quantities, start date, expiry date, current status, pricing and payment terms. Customers can **pause**, **close early** and **renew**, but only where the plan permits it.
3. **My invoices:** invoice number, product or service details, quantity and pricing, taxes, discounts, total amount, invoice status.
4. **Customer dashboard:** number of active subscriptions, upcoming or active plans, amount due, recent invoices, subscription status.
5. **Security and access:** customers can view only their own subscriptions and invoices and cannot reach admin or staff features.

### 2.4 Permission Matrix

| Feature | Admin | Staff | Customer |
| --- | --- | --- | --- |
| Sign up / login / reset password | Yes | Yes | Yes |
| Add staff member | Yes | No | No |
| View all customers | Yes | Yes | No |
| Create products, variants, plans | Yes | No | No |
| Create discount and tax rules | Yes | No | No |
| Create quotation templates | Yes | Yes | No |
| Create quotation / subscription | Yes | Yes | No |
| Confirm, activate, renew, close subscription | Yes | Yes | Own, if plan allows (pause, close, renew) |
| Generate / confirm / send / print / cancel invoice | Yes | Yes | View only (own) |
| Record payment | Yes | Yes | No (online pay optional, see add-ons) |
| Issue refund | Yes | Request / process within limit | Request only |
| Dashboard and reports | Full | Operational view | Personal dashboard |

## 3. Account and Authentication Rules

- **Unique email:** each email can belong to only one account (database unique constraint, case-insensitive).
- **Password policy:** more than eight characters, at least one uppercase letter, one lowercase letter and one special character. Validated on both client and server.
- **Password storage:** hashed with bcrypt or Argon2; never stored or displayed in plain text.
- **Forgot password:** the user enters their registered email; the system sends a single-use, time-limited reset link (for example, valid 30 minutes). The response is the same whether or not the email exists, to prevent account discovery.
- **Sessions:** JWT or secure session cookie with expiry; logout invalidates the session.
- **Staff creation:** only the admin can create staff accounts; there is no public staff sign-up.
- **Brute-force protection:** rate limiting and temporary lockout after repeated failed logins.

## 4. Products, Variants and Plans

### 4.1 Product

Fields: name, type (for example service, software, add-on), sales price, cost price, notes, active/inactive flag.

### 4.2 Variants

A product can be offered in variants by attribute such as brand. Each variant value carries an **extra price**. Example: choosing the *Odoo* brand adds 560 to the base price.

`Final unit price = product sales price + variant extra price`

### 4.3 Plan

Fields:

- Name and price
- Billing period: daily, weekly, monthly or yearly
- Minimum quantity
- Availability dates (start date, end date)
- Admin-controlled options, set plan by plan:
  - Auto-close when the plan ends
  - Allow early close
  - Allow pause
  - Allow renewal

These options directly drive what a customer sees in the portal. If "pause" is off for a plan, the Pause button never appears and the API rejects the request.

## 5. Quotations and Subscriptions

### 5.1 Quotation Templates

A sales rep starts from a template instead of building from scratch. A template contains the plan, product lines and a **validity period in days**. Expired quotations can no longer be confirmed.

### 5.2 Subscription Record

| Field | Description |
| --- | --- |
| Subscription number | Unique, auto-generated (for example SUB-2026-000123) |
| Customer | Linked customer |
| Plan | Linked plan |
| Start date / expiry date | Term of the subscription |
| Payment terms | For example Immediate, Net 15, Net 30 |
| Order lines | Product, quantity, unit price, taxes, amount |
| Status | Draft, Quotation, Confirmed, Active, Closed |

### 5.3 Subscription Lifecycle

`Draft → Quotation → Confirmed → Active → Closed`

| Transition | Who | Notes |
| --- | --- | --- |
| Draft → Quotation | Staff, Admin | Quote sent to customer, valid for N days |
| Quotation → Confirmed | Staff, Admin | Customer accepts; quote must not be expired |
| Confirmed → Active | Staff, Admin | On start date or manual activation; first invoice is scheduled |
| Active → Paused → Active | Staff, Admin, Customer (if allowed) | Billing is suspended while paused |
| Active → Closed | Staff, Admin, Customer (if allowed) or automatic at plan end | Final invoice and optional refund calculation |
| Active → Renewed | Staff, Admin, Customer (if allowed) | Expiry extended; new billing cycle continues |

Every status change is logged with user, timestamp and reason, and anyone on the team can see where a subscription stands.

## 6. Invoicing

### 6.1 Automated Invoice Generation

On billing day a scheduled job finds all Active subscriptions whose next billing date is due and creates one invoice per subscription, prefilled with customer details, product lines, taxes, discounts and totals. Nobody types invoices by hand.

**Guarantee: nothing is billed twice or skipped**

- A unique constraint on (subscription ID, billing period) prevents duplicate invoices.
- The job is idempotent: re-running it for the same day produces no duplicates.
- Each subscription stores a *next billing date* that only advances after the invoice is created, in the same database transaction.
- Missed runs are caught up on the next run (any subscription whose next billing date is in the past is processed).
- A job report lists created, skipped and failed invoices so failures are visible and retryable.

### 6.2 Invoice Lifecycle

`Draft → Confirmed → Paid` (with **Cancelled** as a side state)

- **Confirm:** locks the amounts and assigns the final invoice number.
- **Send:** emails the invoice (PDF) to the customer.
- **Print:** generates a printable PDF.
- **Cancel:** allowed on Draft or Confirmed invoices that have no payments; paid invoices need a refund or credit note instead.
- **Paid:** set automatically when recorded payments cover the total.

### 6.3 Invoice Contents

Invoice number, customer details, subscription reference, product lines (quantity, unit price), taxes, discounts, total, due date, status.

### 6.4 Taxes

The admin defines tax rules (name, percentage, applicable products or categories, optional region). Taxes are calculated automatically per line and totalled on the invoice; staff cannot override them.

## 7. Discounts

Only the admin can create discount rules.

| Field | Description |
| --- | --- |
| Type | Fixed amount (for example Rs 500) or percentage (for example 10%) |
| Scope | Specific products, or whole subscriptions |
| Conditions | Minimum purchase amount or minimum quantity (for example 10 items) |
| Validity | Start date and end date |
| Usage limit | Maximum number of times the discount can be used |

**Examples**

- 10% off when a customer buys 10 or more seats.
- Rs 500 off a specific product.

**Behaviour**

- Once a subscription qualifies, the discount appears on the **next invoice automatically**.
- It stops when it expires or its usage limit is reached; the usage counter is updated atomically to avoid over-use.
- Invoices show the discount as its own line so the customer can see the saving.

**Calculation order:** line amount → discount → tax → total.

## 8. Payments

Each payment records:

- Method (card, bank transfer, UPI, cash, cheque, and so on)
- Amount
- Payment date
- Note / reference number
- The invoice it applies to

**Rules**

- A payment must be linked to an invoice.
- Partial payments are supported; the invoice stays Confirmed with a balance due until fully paid.
- Overpayments are blocked or held as customer credit.
- Staff can update payment details; every edit is audit-logged.
- Outstanding and paid invoices are visible at any moment, and overdue invoices (due date passed, balance greater than zero) are flagged for follow-up.

## 9. Refunds and Cancellations

**Cancellation**

- *Invoice cancellation:* an unpaid Draft or Confirmed invoice can be cancelled by staff or admin with a reason.
- *Subscription cancellation:* closing a subscription early (by staff, admin or an entitled customer) stops future billing.

**Refunds**

- A refund is created against a paid invoice or payment with amount, reason, method and date.
- Refund status flow: Requested → Approved → Processed (or Rejected).
- Refund amount cannot exceed the amount paid minus any earlier refunds.
- Optional pro-rata refund when a subscription is closed early (see add-ons).
- Refunds appear in revenue reports as negative revenue.

## 10. Active and Inactive Subscriptions

The system tracks an **active/inactive** flag for subscriptions, customers and products:

- **Active subscription:** status Active and not paused or expired; counted in dashboards and billed.
- **Inactive subscription:** Paused, Closed or Expired; not billed and excluded from active counts.
- Inactive customers and products are hidden from new selections but kept for historical records.

## 11. Dashboards and Reporting

### 11.1 Finance / Staff Dashboard

- Number of active subscriptions
- Revenue collected, and amount still owed
- Payments received
- Overdue invoices
- Filters: date range, customer, plan, product, status
- Summary view with totals and charts

### 11.2 Customer Dashboard

Active subscription count, upcoming or active plans, amount due, recent invoices, subscription status.

### 11.3 Key Metrics

- **MRR** (monthly recurring revenue): sum of normalised monthly value of active subscriptions (yearly price ÷ 12, weekly price × 52 ÷ 12, and so on).
- **ARR:** MRR × 12.
- **Churn rate:** subscriptions closed in the period ÷ active at the start of the period.
- **Collection rate:** paid ÷ invoiced.

### 11.4 Performance Target

Every page responds in **under two seconds** with thousands of subscriptions. Approach: database indexing, server-side pagination, pre-aggregated summary tables for the dashboard, caching of heavy queries, and background jobs for bulk work.

## 12. Database Design

### 12.1 Core Tables

| Table | Key fields |
| --- | --- |
| **Auth** | id, email (unique), password\_hash, role (admin / staff / customer), is\_active, last\_login, reset\_token, reset\_expiry |
| **Customer** | customer\_id, auth\_id (FK), name, phone, address, company, is\_active, created\_at |
| **Staff** | staff\_id, auth\_id (FK), name, department, created\_by (admin), is\_active |
| **Product** | product\_id, name, type, sales\_price, cost\_price, notes, is\_active |
| **Product Variant** | variant\_id, product\_id (FK), attribute (for example brand), value, extra\_price |
| **Plan** | plan\_id, name, price, billing\_period, min\_quantity, start\_date, end\_date, auto\_close, allow\_early\_close, allow\_pause, allow\_renewal |
| **Quotation** | quotation\_id, template flag, customer\_id, plan\_id, validity\_days, status, created\_by |
| **Subscription** | subscription\_id, number (unique), customer\_id, plan\_id, quotation\_id, start\_date, expiry\_date, next\_billing\_date, payment\_terms, status |
| **Subscription Line** | line\_id, subscription\_id, product\_id, variant\_id, quantity, unit\_price, tax\_id, amount |
| **Tax** | tax\_id, name, rate, applies\_to, is\_active |
| **Discount** | discount\_id, type (fixed / percent), value, scope, product\_id, min\_amount, min\_qty, start\_date, end\_date, usage\_limit, times\_used |
| **Invoice** | invoice\_id, number (unique), subscription\_id, customer\_id, billing\_period, subtotal, discount\_total, tax\_total, total, due\_date, status |
| **Invoice Line** | line\_id, invoice\_id, product, quantity, unit\_price, discount, tax, amount |
| **Payment** | payment\_id, invoice\_id (FK), method, amount, payment\_date, note, recorded\_by |
| **Refund** | refund\_id, payment\_id / invoice\_id, amount, reason, status, processed\_date, approved\_by |
| **Audit Log** | log\_id, user\_id, action, entity, entity\_id, timestamp, old/new values |

*(The source brief lists "Quatition Table"; it is spelled Quotation here.)*

### 12.2 Relationships

- Auth 1 → 1 Customer or Staff
- Customer 1 → many Subscriptions → many Subscription Lines
- Subscription 1 → many Invoices (one per billing period)
- Invoice 1 → many Payments; Payment 1 → many Refunds
- Discount many ↔ many Products / Subscriptions

### 12.3 Key Constraints and Indexes

- Unique: Auth.email, Subscription.number, Invoice.number, (subscription\_id, billing\_period) on Invoice.
- Indexes: Subscription(status, next\_billing\_date), Invoice(status, due\_date), Invoice(customer\_id), Payment(invoice\_id), Subscription(customer\_id).
- Money stored as fixed-point decimals, never floats.

## 13. Suggested Architecture

- **Frontend:** web app with three experiences (admin console, staff workspace, customer portal), for example React.
- **Backend:** REST API (Node.js/Express, Django, Spring Boot or similar) with role-checking middleware.
- **Database:** relational (PostgreSQL or MySQL) for transactional integrity.
- **Scheduler / workers:** billing-day job, renewal reminders, overdue checks and email sending run as background jobs.
- **Email service:** password resets, invoices, reminders.
- **PDF generation:** invoices and quotations.
- **Cache:** Redis for dashboard aggregates.

### 13.1 Indicative API Endpoints

| Area | Endpoints |
| --- | --- |
| Auth | POST /auth/signup, /auth/login, /auth/logout, /auth/forgot-password, /auth/reset-password |
| Staff (admin) | POST/GET/PATCH /staff |
| Products and plans (admin) | /products, /products/{id}/variants, /plans |
| Discounts and taxes (admin) | /discounts, /taxes |
| Quotations | /quotation-templates, /quotations |
| Subscriptions | /subscriptions, POST /subscriptions/{id}/confirm, /activate, /pause, /renew, /close |
| Invoices | /invoices, POST /invoices/{id}/confirm, /send, /cancel, GET /invoices/{id}/pdf |
| Payments | POST /payments, GET /invoices/outstanding |
| Refunds | POST /refunds, PATCH /refunds/{id} |
| Dashboard | GET /dashboard/summary, /dashboard/overdue |
| Customer portal | GET /me/subscriptions, /me/invoices, /me/dashboard |

## 14. Security

- RBAC enforced server-side on every endpoint; customer queries are always scoped by the authenticated customer ID.
- HTTPS everywhere; secure, HttpOnly cookies or short-lived tokens.
- Hashed passwords; single-use expiring reset tokens.
- Input validation and parameterised queries to prevent injection; CSRF and XSS protection.
- Audit log of admin and staff actions on money-related records.
- Personal data protection and a data-retention policy.

## 15. Add-on Features (Recommended Extensions)

**Billing and revenue**

1. **Online payment gateway:** let customers pay invoices from the portal (Razorpay, Stripe, UPI) with automatic reconciliation.
2. **Automatic payment reminders and dunning:** emails before due date, on due date and after overdue; optional auto-suspend after repeated failures.
3. **Pro-rata billing:** correct charges for mid-cycle upgrades, downgrades and early closures.
4. **Plan upgrade / downgrade:** switch plans with automatic proration.
5. **Credit notes and customer wallet:** hold overpayments and refunds as credit.
6. **Free trials and setup fees:** trial periods before the first charge.
7. **Usage-based billing:** meter seats or API usage and bill on consumption.
8. **Coupon codes:** customer-entered promo codes, in addition to admin discount rules.
9. **Multi-currency and multi-tax (GST) support** with GST-compliant invoice formats.

**Customer experience**

10. **Renewal reminders:** notifications 30, 7 and 1 day before expiry.
11. **Auto-renew toggle** in the customer portal.
12. **Email and SMS notifications** for invoices, payments, status changes.
13. **Downloadable invoice PDFs** and payment receipts.
14. **Support tickets or contact form** linked to a subscription.
15. **Two-factor authentication (2FA)** and social login.

**Operations and insight**

16. **Advanced analytics:** MRR, ARR, churn, LTV, revenue by plan, cohort charts.
17. **Export to CSV / Excel / PDF** for any report.
18. **Bulk actions:** bulk send, bulk confirm, bulk reminders.
19. **Notification centre** for staff (overdue invoices, expiring subscriptions, failed jobs).
20. **Accounting integration:** Tally, QuickBooks or Zoho Books sync.
21. **Webhooks and public API** for integrations.
22. **Full audit trail viewer** for admins.
23. **Multi-language and dark-mode UI.**

## 16. Non-Functional Requirements

| Requirement | Target |
| --- | --- |
| Performance | Every page under 2 seconds with thousands of subscriptions |
| Billing job | Process hundreds of due subscriptions in a single run without duplicates |
| Availability | 99.5% or higher |
| Scalability | Horizontal scaling of API and workers |
| Data integrity | ACID transactions for billing and payments |
| Backups | Daily automated backups with tested restore |
| Usability | Responsive design for desktop and mobile |
| Accessibility | WCAG 2.1 AA where practical |

## 17. Suggested Delivery Plan

| Phase | Scope |
| --- | --- |
| 1. Foundation | Auth, roles, staff management, customer accounts, password reset |
| 2. Catalogue | Products, variants, plans, tax rules, discount rules |
| 3. Sales | Quotation templates, quotations, subscription lifecycle |
| 4. Billing | Invoice generation job, invoice lifecycle, send and print |
| 5. Money | Payments, outstanding tracking, refunds and cancellations |
| 6. Insight | Staff dashboard, customer dashboard, reports and filters |
| 7. Hardening | Performance tuning, security review, add-ons, UAT |

## 18. Acceptance Criteria Summary

- Duplicate emails are rejected; weak passwords are rejected; reset links arrive by email.
- Only the admin can add staff, products, plans, discounts and taxes.
- A customer can never view another customer's subscription or invoice.
- Plan permissions control which actions (pause, close, renew) a customer sees.
- Invoices are generated automatically, with taxes and discounts, and never duplicated.
- Discounts apply automatically to the next invoice and stop at expiry or usage limit.
- Payments are recorded per invoice; outstanding and overdue invoices are visible at any time.
- Dashboards show active subscriptions, revenue, payments and overdue invoices, and load in under two seconds.

## 19. Glossary

- **MRR / ARR:** monthly / annual recurring revenue.
- **Dunning:** the process of chasing overdue payments.
- **Pro-rata:** charging or refunding in proportion to the time used.
- **Idempotent:** safe to run multiple times with the same result.
- **RBAC:** role-based access control.
