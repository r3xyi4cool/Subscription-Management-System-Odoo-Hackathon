# Team Members

Subscription Management System

| Member   | Name        | Role                       | Responsibilities                                      |
| -------- | ----------- | -------------------------- | ----------------------------------------------------- |
| Member 1 | Harigovindh | Frontend                   | All screens for customers, staff and admin            |
| Member 2 | Devanandan  | Backend                    | APIs, business rules, billing job, authentication     |
| Member 3 | Gayathri    | Database                   | Tables, constraints, indexes, backups                 |
| Member 4 | Sanjay      | Management, Review and Fix | Planning, code review, testing, bug fixes, deployment |

---

## Harigovindh: Frontend

- Sign up, login, forgot and reset password pages
- Role-based navigation and routes
- Customer portal: dashboard, My Subscriptions, My Invoices, account settings
- Staff screens: customers, quotations, subscriptions, invoices, payments
- Admin screens: staff, products, plans, discounts, taxes
- Dashboard with filters

## Devanandan: Backend

- Authentication, password reset and role-based access
- Staff, product, variant, plan, discount and tax APIs
- Quotations and subscription lifecycle
- Invoice generation job (no duplicates, none skipped)
- Invoice actions, payments, refunds and cancellations
- Dashboard APIs

## Gayathri: Database

- All tables: Auth, Customer, Staff, Product, Variant, Plan, Discount, Tax, Quotation, Subscription, Invoice, Payment, Refund
- Constraints: unique email, one invoice per subscription per billing period
- Indexes and summary queries for speed
- Migrations and seed data
- Daily backups and tested restore

## Sanjay: Management, Review and Fix

- Task board and progress check
- Agree API format and naming across the team
- Review every pull request
- Test all three roles, billing and security
- Load test: pages under 2 seconds
- Fix bugs found during review and testing
- Documentation, deployment and go-live

---

## Who to Ask

| Question about               | Ask         |
| ---------------------------- | ----------- |
| Screens, forms, navigation   | Harigovindh |
| APIs, billing logic, login   | Devanandan  |
| Tables, queries, data issues | Gayathri    |
| Plan, review, bugs, release  | Sanjay      |
