# Brightloop SMS - User Guide

## 1. Introduction

Brightloop SMS provides two distinct operational environments:
1. **Customer Self-Service Portal** (`/portal/*`): For subscribers to view active services, review billing statements, download PDF invoices, track payment receipts, and receive in-app notifications.
2. **Staff & Admin Management Console** (`/admin/*`): For company operators to manage catalogs, generate quotations, track subscriptions, monitor the billing engine, record payments, and audit business telemetry.

---

## 2. Customer Portal Walkthrough

### 2.1 Sign Up & Login
* Navigate to `http://localhost:5173/signup` to register a new account.
* Enter your Name, Company Name, Email, and a strong password (minimum 8 characters, with uppercase, lowercase, number, and special character).
* Upon login, you are automatically routed to `/portal/dashboard`.

### 2.2 Messages & In-App Notifications
* Because this system runs locally with zero external mail dependencies, all communications (invoice generation alerts, overdue notices, payment confirmations) appear in your **In-App Notification Feed**.
* Click the **Bell Icon** in the top navigation bar to preview recent messages or visit `/portal/notifications`.
* If you have an unpaid balance, an alert banner appears prominently on your dashboard.

### 2.3 Viewing Subscriptions & Invoices
* **My Subscriptions (`/portal/subscriptions`):** View your current plan, billing frequency (monthly, yearly, weekly), renewal dates, and status.
* **My Invoices (`/portal/invoices`):** View all issued statements. Click **Download PDF** on any invoice to obtain a formatted invoice PDF.

### 2.4 Account Settings
* Visit `/portal/account` to view your profile details and update your account password.

---

## 3. Staff & Admin Console Walkthrough

### 3.1 Role Privileges
* **Admin:** Full access to all modules, including Staff Management, Catalog editing, and the Immutable Audit Log.
* **Staff:** Operational access to Customers, Quotations, Subscriptions, Invoices, Payments, and Overdue Dashboards.

### 3.2 Product Catalog & Plans
* **Products:** Create software or service offerings, and attach variants with extra pricing (e.g. Dedicated Support +Rs 450).
* **Plans:** Define billing frequency (`daily`, `weekly`, `monthly`, `yearly`) and lifecycle flags:
  * `allow_pause`: Permits customer or staff to pause subscriptions.
  * `allow_early_close`: Permits termination before current period expiration.
  * `auto_close`: Automatically transitions expired subscriptions to Closed.
  * `allow_renewal`: Enables automatic renewal upon billing date.
* **Discounts:** Configure fixed or percentage discounts with optional usage limits and date windows.
* **Taxes:** Set tax rates applicable across catalog items.

### 3.3 Quotations to Subscriptions
1. Create a Quotation with selected customer, plan, and product lines.
2. Once the customer agrees, click **Confirm Quotation**.
3. The system automatically creates a `confirmed` Subscription with an auto-generated serial number (`SUB-YYYY-NNNNNN`).
4. Click **Activate** to shift the subscription to `active` and initialize the recurring billing cycle.

### 3.4 Billing Engine & Invoicing
* When a subscription's `next_billing_date` is reached, the system generates a draft invoice.
* Click **Confirm** to lock the invoice and generate an official invoice number (`INV-YYYY-NNNNNN`).
* Click **Send** to mark the invoice as Sent and emit an in-app notification to the customer.
* When payments are received via Wire, UPI, Card, or Cheque, record the payment under **Payments**.
* When total payments equal or exceed the invoice total, the invoice shifts automatically to `paid`.
