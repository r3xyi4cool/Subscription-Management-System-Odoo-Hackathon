# Work Split: Subscription Management System

Who is doing what. Update the checkboxes as work is finished.

## Team

| Member   | Name        | Area                  | Focus                                             |
| -------- | ----------- | --------------------- | ------------------------------------------------- |
| Member 1 | Harigovindh | Frontend              | All screens for customers, staff and admin        |
| Member 2 | Devannn     | Backend               | APIs, business rules, billing job, authentication |
| Member 3 | Gayathri    | Database              | Tables, constraints, indexes, backups             |
| Member 4 | Sanjay      | Management and Review | Planning, code review, testing, docs, deployment  |

---

## Member 1: Frontend

- [ ] App layout, navigation, role-based routes
- [ ] Form validation (including password rules)
- [ ] Sign up, login, forgot password, reset password pages
- [ ] Account settings
- [ ] Customer dashboard (active subscriptions, amount due, recent invoices)
- [ ] My Subscriptions (pause, close early, renew)
- [ ] My Invoices and PDF download
- [ ] Staff pages: customers, quotations, subscriptions, invoices, payments
- [ ] Admin pages: staff, products, plans, discounts, taxes
- [ ] Staff and admin dashboard with filters

## Member 2: Backend

- [ ] Sign up, login, logout
- [ ] Forgot and reset password (email link)
- [ ] Role-based access (admin, staff, customer)
- [ ] Admin adds staff
- [ ] Product and variant APIs
- [ ] Plan APIs (pause, close, renew permissions)
- [ ] Discount and tax APIs
- [ ] Quotation templates and quotations
- [ ] Subscription lifecycle (Draft, Quotation, Confirmed, Active, Closed)
- [ ] Auto invoice generation (no duplicates, none skipped)
- [ ] Tax and discount calculation on invoices
- [ ] Invoice confirm, send, print, cancel
- [ ] Payments, refunds, cancellations
- [ ] Dashboard APIs (active subscriptions, revenue, overdue)

## Member 3: Database

- [x] Tables: Auth, Customer, Staff
- [x] Tables: Product, Variant, Plan
- [x] Tables: Discount, Tax
- [x] Tables: Quotation, Subscription
- [x] Tables: Invoice, Payment, Refund
- [x] Constraints: unique email, one invoice per subscription per billing period
- [x] Indexes for fast dashboard and list queries
- [x] Migrations and seed data
- [x] Daily backups and tested restore

## Member 4: Management and Review

- [ ] Task board and weekly progress check
- [ ] Agree API format and naming
- [ ] Review every pull request
- [ ] Test cases for admin, staff and customer roles
- [ ] Security check: customers see only their own data
- [ ] Load test: pages under 2 seconds
- [ ] Documentation and user guides
- [ ] Deployment and go-live

---

## Dependencies

| Needs                 | From            | Why                                      |
| --------------------- | --------------- | ---------------------------------------- |
| Schema and seed data  | Member 3        | Backend cannot start without tables      |
| API format, then APIs | Member 2        | Frontend builds against agreed endpoints |
| Finished features     | Members 1, 2, 3 | Member 4 reviews and tests them          |

## Timeline

| Week | Focus                                                              |
| ---- | ------------------------------------------------------------------ |
| 1    | Schema and seed data; API format agreed; layout and account pages  |
| 2    | Auth, products, plans, discounts, taxes; admin pages               |
| 3    | Quotations and subscriptions; subscription pages; first review     |
| 4    | Invoice job, payments, refunds; indexes; invoice and payment pages |
| 5    | Dashboards; full testing and security check                        |
| 6    | Load test, fixes, docs, deployment                                 |

## Working Agreements

- One Git branch per feature, named `area/feature` (for example `backend/invoice-job`).
- Every pull request is reviewed by Member 4 before merge.
- Weekly integration check where each member demos their part.
