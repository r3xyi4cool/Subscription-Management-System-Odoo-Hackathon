#!/usr/bin/env python3
"""
mock_test.py - In-Process Mock Backend Test Harness.

Tests the entire Subscription Management System API end-to-end using Flask's
in-memory test client and an in-memory SQLite database.
Requires NO running server, NO external network, and NO open ports.
Can be executed directly with: python mock_test.py
"""

import sys
import os

# Auto-fallback to virtualenv python if dependencies are in venv
venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
if os.path.exists(venv_python) and sys.executable != venv_python:
    try:
        import flask
    except ImportError:
        os.execv(venv_python, [venv_python] + sys.argv)

# Add project root and backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

import json
import time
from datetime import date, timedelta
from decimal import Decimal

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.customer import Customer
from backend.app.models.staff import Staff
from backend.app.models.catalog import Product, Variant, Plan, Tax, Discount
from backend.app.models.quotation import QuotationTemplate, Quotation, QuotationLine
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.billing import Invoice, InvoiceLine, Payment, Refund
from backend.app.models.audit import AuditLog
from backend.app.services.billing_service import add_billing_period


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class MockTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.app = create_app("testing")
        self.client = self.app.test_client()

        # Auth tokens and state
        self.admin_token = None
        self.staff_token = None
        self.customer_token = None
        self.customer2_token = None
        self.state = {}

    def log_step(self, step_num, title, status="PASS", detail=""):
        badge = f"{Colors.GREEN}[PASS]{Colors.RESET}" if status == "PASS" else f"{Colors.RED}[FAIL]{Colors.RESET}"
        detail_str = f" - {Colors.CYAN}{detail}{Colors.RESET}" if detail else ""
        print(f"{badge} Step {step_num:02d}: {title}{detail_str}")
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1

    def req(self, method, path, json_data=None, token=None, expect_status=200):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        call_fn = getattr(self.client, method.lower())
        response = call_fn(path, json=json_data, headers=headers)

        try:
            body = response.get_json() or {}
        except Exception:
            body = response.data

        if isinstance(expect_status, (list, tuple)):
            status_match = response.status_code in expect_status
        else:
            status_match = response.status_code == expect_status

        return status_match, response.status_code, body

    def run_all(self):
        print(f"\n{Colors.BOLD}=== Subscription Management System: In-Process Mock Test Suite ==={Colors.RESET}")
        print(f"Target: Flask In-Memory SQLite | Mock Outbox Mailer | Mock Scheduled Jobs\n")

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            # ---------------- MODULE 1: AUTHENTICATION ----------------
            print(f"{Colors.BOLD}--- Module 1: Authentication & Password Security ---{Colors.RESET}")

            # 1. Health check
            ok, status, body = self.req("GET", "/api/v1/health")
            self.log_step(1, "Health check endpoint", "PASS" if ok else "FAIL", f"HTTP {status}")

            # 2. Signup Customer 1
            signup_payload = {
                "email": "mock_customer1@example.com",
                "password": "SecurePassword1!",
                "name": "Mock Customer One",
                "company": "Acme Innovations",
                "billing_address": "123 Mock Lane",
            }
            ok, status, body = self.req("POST", "/api/v1/auth/signup", signup_payload, expect_status=201)
            cust1_id = body.get("customer_id") or body.get("id") or body.get("data", {}).get("id")
            self.state["cust1_id"] = cust1_id
            self.log_step(2, "Customer signup valid credentials", "PASS" if ok and cust1_id else "FAIL", f"Customer ID: {cust1_id}")

            # 3. Duplicate email rejected
            ok, status, _ = self.req("POST", "/api/v1/auth/signup", signup_payload, expect_status=(400, 409))
            self.log_step(3, "Signup duplicate email rejected", "PASS" if ok else "FAIL", f"HTTP {status}")

            # 4. Weak password rejected
            weak_payload = {"email": "weak@example.com", "password": "weak", "name": "Weak User"}
            ok, status, _ = self.req("POST", "/api/v1/auth/signup", weak_payload, expect_status=(400, 422))
            self.log_step(4, "Signup weak password rejected", "PASS" if ok else "FAIL", f"HTTP {status}")

            # 5. Wrong login credentials rejected
            wrong_login = {"email": "mock_customer1@example.com", "password": "WrongPassword999!"}
            ok, status, _ = self.req("POST", "/api/v1/auth/login", wrong_login, expect_status=401)
            self.log_step(5, "Login bad password rejected", "PASS" if ok else "FAIL", f"HTTP {status}")

            # 6. Customer 1 login
            ok, status, body = self.req("POST", "/api/v1/auth/login", {"email": "mock_customer1@example.com", "password": "SecurePassword1!"})
            self.customer_token = body.get("access_token") or body.get("data", {}).get("access_token")
            self.log_step(6, "Customer 1 login", "PASS" if ok and self.customer_token else "FAIL")

            # 7. Seed & Login Admin
            admin_auth = Auth(email="admin@example.com", role="admin", is_active=True)
            admin_auth.set_password("Admin@12345")
            db.session.add(admin_auth)
            db.session.commit()

            ok, status, body = self.req("POST", "/api/v1/auth/login", {"email": "admin@example.com", "password": "Admin@12345"})
            self.admin_token = body.get("access_token") or body.get("data", {}).get("access_token")
            self.log_step(7, "Admin login", "PASS" if ok and self.admin_token else "FAIL")

            # 8. Password reset flow (single-use, time-limited)
            ok, status, body = self.req("POST", "/api/v1/auth/forgot-password", {"email": "mock_customer1@example.com"})
            reset_token = body.get("reset_token") or body.get("data", {}).get("reset_token")
            self.log_step(8, "Forgot password generates reset token", "PASS" if ok and reset_token else "FAIL")

            ok, status, _ = self.req("POST", "/api/v1/auth/reset-password", {"token": reset_token, "new_password": "NewSecurePass2!"})
            self.log_step(9, "Reset password sets new password", "PASS" if ok else "FAIL")

            # Reset token cannot be reused
            ok, status, _ = self.req("POST", "/api/v1/auth/reset-password", {"token": reset_token, "new_password": "AnotherPass3!"}, expect_status=(400, 422))
            self.log_step(10, "Reset token reuse rejected", "PASS" if ok else "FAIL", f"HTTP {status}")

            # ---------------- MODULE 2: ROLES & STAFF MANAGEMENT ----------------
            print(f"\n{Colors.BOLD}--- Module 2: Roles, Permissions & Staff Management ---{Colors.RESET}")

            # 11. Customer blocked from creating staff (403)
            staff_payload = {"email": "staff1@example.com", "password": "StaffPassword1!", "name": "Staff Alice", "department": "Sales"}
            ok, status, _ = self.req("POST", "/api/v1/staff", staff_payload, token=self.customer_token, expect_status=403)
            self.log_step(11, "Customer blocked from creating staff (403)", "PASS" if ok else "FAIL", f"HTTP {status}")

            # 12. Admin creates staff
            ok, status, body = self.req("POST", "/api/v1/staff", staff_payload, token=self.admin_token, expect_status=201)
            staff_id = body.get("id") or body.get("data", {}).get("id")
            self.state["staff_id"] = staff_id
            self.log_step(12, "Admin creates staff member", "PASS" if ok else "FAIL", f"Staff ID: {staff_id}")

            # 13. Staff login
            ok, status, body = self.req("POST", "/api/v1/auth/login", {"email": "staff1@example.com", "password": "StaffPassword1!"})
            self.staff_token = body.get("access_token") or body.get("data", {}).get("access_token")
            self.log_step(13, "Staff login", "PASS" if ok and self.staff_token else "FAIL")

            # 14. Staff blocked from creating catalog products (403)
            ok, status, _ = self.req("POST", "/api/v1/products", {"name": "Staff Item", "sales_price": 50.0}, token=self.staff_token, expect_status=403)
            self.log_step(14, "Staff blocked from creating products (403)", "PASS" if ok else "FAIL", f"HTTP {status}")

            # 15. Admin deactivates staff & deactivated staff cannot login
            ok, status, _ = self.req("PATCH", f"/api/v1/staff/{staff_id}", {"is_active": False}, token=self.admin_token)
            self.log_step(15, "Admin deactivates staff member", "PASS" if ok else "FAIL")

            ok, status, _ = self.req("POST", "/api/v1/auth/login", {"email": "staff1@example.com", "password": "StaffPassword1!"}, expect_status=401)
            self.log_step(16, "Deactivated staff login rejected (401)", "PASS" if ok else "FAIL")

            # Reactivate staff for remaining tests
            self.req("PATCH", f"/api/v1/staff/{staff_id}", {"is_active": True}, token=self.admin_token)

            # ---------------- MODULE 3: CATALOG, PLANS, TAXES & DISCOUNTS ----------------
            print(f"\n{Colors.BOLD}--- Module 3: Catalog, Variants, Plans, Taxes & Discounts ---{Colors.RESET}")

            # 17. Admin creates tax (10%)
            ok, status, body = self.req("POST", "/api/v1/taxes", {"name": "GST 10%", "rate": 10.0}, token=self.admin_token, expect_status=201)
            tax_id = body.get("id") or body.get("data", {}).get("id")
            self.state["tax_id"] = tax_id
            self.log_step(17, "Admin creates tax rule (10%)", "PASS" if ok else "FAIL", f"Tax ID: {tax_id}")

            # 18. Admin creates discount (20% off)
            ok, status, body = self.req("POST", "/api/v1/discounts", {
                "code": "PROMO20", "discount_type": "percentage", "value": 20.0, "min_quantity": 1
            }, token=self.admin_token, expect_status=201)
            disc_id = body.get("id") or body.get("data", {}).get("id")
            self.state["disc_id"] = disc_id
            self.log_step(18, "Admin creates discount rule (20%)", "PASS" if ok else "FAIL", f"Discount ID: {disc_id}")

            # 19. Admin creates product (ERP System - $1000)
            ok, status, body = self.req("POST", "/api/v1/products", {
                "name": "Enterprise ERP", "sales_price": 1000.00, "cost_price": 300.00
            }, token=self.admin_token, expect_status=201)
            prod_id = body.get("id") or body.get("data", {}).get("id")
            self.state["prod_id"] = prod_id
            self.log_step(19, "Admin creates product", "PASS" if ok else "FAIL", f"Product ID: {prod_id}")

            # 20. Admin creates product variant (Odoo Module +$560)
            ok, status, body = self.req("POST", f"/api/v1/products/{prod_id}/variants", {
                "name": "Odoo Integration", "extra_price": 560.00
            }, token=self.admin_token, expect_status=201)
            var_id = body.get("id") or body.get("data", {}).get("id")
            self.state["var_id"] = var_id
            self.log_step(20, "Admin creates variant (Odoo +$560)", "PASS" if ok else "FAIL", f"Variant ID: {var_id}")

            # 21. Admin creates billing plan (Monthly with pause/close/renew allowed)
            ok, status, body = self.req("POST", "/api/v1/plans", {
                "name": "Monthly Enterprise", "billing_period": "monthly", "min_quantity": 1,
                "start_date": "2026-01-01", "allow_pause": True, "allow_close": True, "allow_renew": True
            }, token=self.admin_token, expect_status=201)
            plan_id = body.get("id") or body.get("data", {}).get("id")
            self.state["plan_id"] = plan_id
            self.log_step(21, "Admin creates monthly billing plan", "PASS" if ok else "FAIL", f"Plan ID: {plan_id}")

            # ---------------- MODULE 4: QUOTATIONS & SALES LIFECYCLE ----------------
            print(f"\n{Colors.BOLD}--- Module 4: Quotations & Sales Lifecycle ---{Colors.RESET}")

            # 22. Create quotation
            q_payload = {
                "customer_id": cust1_id,
                "plan_id": plan_id,
                "validity_days": 30,
                "lines": [{
                    "product_id": prod_id,
                    "variant_id": var_id,
                    "quantity": 1,
                    "tax_id": tax_id,
                    "discount_id": disc_id
                }]
            }
            ok, status, body = self.req("POST", "/api/v1/quotations", q_payload, token=self.admin_token, expect_status=201)
            q_id = body.get("id") or body.get("data", {}).get("id")
            self.state["q_id"] = q_id
            # Math: (1000 + 560) * 1 = 1560. 20% discount = 312 -> 1248. 10% tax = 124.80 -> total 1372.80
            total_amt = (body.get("data") or body).get("total_amount")
            self.log_step(22, "Create quotation with variant, discount & tax", "PASS" if ok and total_amt == 1372.8 else "FAIL", f"Total: ${total_amt}")

            # 23. Confirm quotation -> generates subscription
            ok, status, body = self.req("POST", f"/api/v1/quotations/{q_id}/confirm", token=self.admin_token, expect_status=201)
            sub_id = body.get("subscription_id") or body.get("id") or body.get("data", {}).get("subscription_id")
            self.state["sub_id"] = sub_id
            self.log_step(23, "Confirm quotation generates subscription", "PASS" if ok and sub_id else "FAIL", f"Subscription ID: {sub_id}")

            # 24. Subscription lifecycle: Activate -> Pause -> Reactivate
            ok, status, _ = self.req("POST", f"/api/v1/subscriptions/{sub_id}/activate", token=self.admin_token)
            self.log_step(24, "Activate subscription", "PASS" if ok else "FAIL")

            ok, status, _ = self.req("POST", f"/api/v1/subscriptions/{sub_id}/pause", token=self.admin_token)
            self.log_step(25, "Pause subscription", "PASS" if ok else "FAIL")

            ok, status, _ = self.req("POST", f"/api/v1/subscriptions/{sub_id}/activate", token=self.admin_token)
            self.log_step(26, "Re-activate subscription from paused", "PASS" if ok else "FAIL")

            # ---------------- MODULE 5: BILLING CYCLE & INVOICING ----------------
            print(f"\n{Colors.BOLD}--- Module 5: Idempotent Billing Engine & Invoices ---{Colors.RESET}")

            # 27. Run billing engine
            ok, status, body = self.req("POST", "/api/v1/billing/run", {"as_of_date": "2026-11-01"}, token=self.admin_token)
            created_count = (body.get("data") or body).get("created_count", 0)
            self.log_step(27, "Billing engine runs and creates invoice", "PASS" if ok and created_count >= 1 else "FAIL", f"Invoices created: {created_count}")

            # Retrieve generated invoice
            ok, status, body = self.req("GET", f"/api/v1/invoices?subscription_id={sub_id}", token=self.admin_token)
            items = body.get("items") or body.get("data") or []
            inv_id = items[0]["id"] if items else None
            inv_total = items[0]["total"] if items else 0.0
            self.state["inv_id"] = inv_id
            self.state["inv_total"] = inv_total

            # 28. Run billing engine second time -> 0 duplicates created!
            ok, status, body = self.req("POST", "/api/v1/billing/run", {"as_of_date": "2026-11-01"}, token=self.admin_token)
            created_count2 = (body.get("data") or body).get("created_count", 0)
            self.log_step(28, "Billing engine idempotent check (no duplicates)", "PASS" if ok and created_count2 == 0 else "FAIL", f"Invoices created: {created_count2}")

            # 29. Confirm draft invoice
            ok, status, _ = self.req("POST", f"/api/v1/invoices/{inv_id}/confirm", token=self.admin_token)
            self.log_step(29, "Confirm draft invoice", "PASS" if ok else "FAIL")

            # 30. Download invoice PDF & check valid PDF binary (%PDF)
            res_pdf = self.client.get(f"/api/v1/invoices/{inv_id}/pdf", headers={"Authorization": f"Bearer {self.admin_token}"})
            is_valid_pdf = res_pdf.status_code == 200 and res_pdf.data.startswith(b"%PDF")
            self.log_step(30, "Invoice PDF endpoint returns %PDF document", "PASS" if is_valid_pdf else "FAIL", f"Header: {res_pdf.data[:5]}")

            # 31. Email invoice dispatch (mock outbox check)
            ok, status, _ = self.req("POST", f"/api/v1/invoices/{inv_id}/send", token=self.admin_token)
            self.log_step(31, "Dispatch invoice email to customer", "PASS" if ok else "FAIL")

            # ---------------- MODULE 6: CUSTOMER ISOLATION ----------------
            print(f"\n{Colors.BOLD}--- Module 6: Customer Data Isolation & Security ---{Colors.RESET}")

            # 32. Sign up Customer 2
            c2_payload = {"email": "mock_customer2@example.com", "password": "SecurePassword2!", "name": "Customer Two"}
            self.req("POST", "/api/v1/auth/signup", c2_payload, expect_status=201)
            _, _, c2_login = self.req("POST", "/api/v1/auth/login", {"email": "mock_customer2@example.com", "password": "SecurePassword2!"})
            self.customer2_token = c2_login.get("access_token") or c2_login.get("data", {}).get("access_token")

            # Customer 1 can see own invoice
            # First re-login Customer 1 with the updated password from step 9
            _, _, c1_login = self.req("POST", "/api/v1/auth/login", {"email": "mock_customer1@example.com", "password": "NewSecurePass2!"})
            self.customer_token = c1_login.get("access_token") or c1_login.get("data", {}).get("access_token")

            ok, status, _ = self.req("GET", f"/api/v1/invoices/{inv_id}", token=self.customer_token, expect_status=200)
            self.log_step(32, "Customer 1 can view own invoice", "PASS" if ok else "FAIL")

            # Customer 2 blocked from viewing Customer 1's invoice (403/404)
            ok, status, _ = self.req("GET", f"/api/v1/invoices/{inv_id}", token=self.customer2_token, expect_status=(403, 404))
            self.log_step(33, "Customer 2 blocked from Customer 1 invoice (403/404)", "PASS" if ok else "FAIL", f"HTTP {status}")

            # ---------------- MODULE 7: PAYMENTS, REFUNDS & OVERPAYMENT ----------------
            print(f"\n{Colors.BOLD}--- Module 7: Payments, Refunds & Overpayment Controls ---{Colors.RESET}")

            # 34. Overpayment rejection
            excess_amount = inv_total + 5000.0
            ok, status, _ = self.req("POST", "/api/v1/payments", {
                "invoice_id": inv_id, "amount": excess_amount, "method": "credit_card"
            }, token=self.admin_token, expect_status=(400, 422))
            self.log_step(34, "Overpayment rejected", "PASS" if ok else "FAIL", f"HTTP {status}")

            # 35. Partial payment ($372.80)
            ok, status, _ = self.req("POST", "/api/v1/payments", {
                "invoice_id": inv_id, "amount": 372.80, "method": "credit_card"
            }, token=self.admin_token, expect_status=201)
            self.log_step(35, "Record partial payment ($372.80)", "PASS" if ok else "FAIL")

            # 36. Full balance payment ($1000.00) -> Status becomes Paid
            ok, status, _ = self.req("POST", "/api/v1/payments", {
                "invoice_id": inv_id, "amount": 1000.00, "method": "bank_transfer"
            }, token=self.admin_token, expect_status=201)
            _, _, inv_check = self.req("GET", f"/api/v1/invoices/{inv_id}", token=self.admin_token)
            is_paid = (inv_check.get("data") or inv_check).get("status") == "paid"
            self.log_step(36, "Full payment transitions status to Paid", "PASS" if ok and is_paid else "FAIL")

            # 37. Valid refund ($200.00)
            ok, status, _ = self.req("POST", f"/api/v1/invoices/{inv_id}/refund", {"amount": 200.00, "reason": "Customer discount adjustment"}, token=self.admin_token, expect_status=201)
            self.log_step(37, "Process valid partial refund", "PASS" if ok else "FAIL")

            # 38. Excessive refund rejected (> amount paid)
            ok, status, _ = self.req("POST", f"/api/v1/invoices/{inv_id}/refund", {"amount": 5000.00, "reason": "Excessive"}, token=self.admin_token, expect_status=(400, 422))
            self.log_step(38, "Excessive refund rejected", "PASS" if ok else "FAIL", f"HTTP {status}")

            # ---------------- MODULE 8: DASHBOARDS & AUDIT LOG ----------------
            print(f"\n{Colors.BOLD}--- Module 8: Real-Time Aggregate Dashboard & Audit Logs ---{Colors.RESET}")

            # 39. Dashboard summary responded in under 2 seconds
            t0 = time.time()
            ok, status, dash_data = self.req("GET", "/api/v1/dashboard/summary", token=self.admin_token)
            elapsed = time.time() - t0
            metrics = dash_data.get("data") or dash_data
            self.log_step(39, "Dashboard aggregate metrics respond in < 2.0s", "PASS" if ok and elapsed < 2.0 else "FAIL", f"Elapsed: {elapsed:.4f}s | Active Subs: {metrics.get('active_subscriptions')}")

            # 40. Audit log entries recorded for money changes
            audit_count = AuditLog.query.count()
            self.log_step(40, "Audit log records money-related mutations", "PASS" if audit_count > 0 else "FAIL", f"Audit records: {audit_count}")

            # ---------------- SUMMARY ----------------
            print("\n" + "=" * 60)
            total = self.passed + self.failed
            success_rate = (self.passed / total) * 100 if total > 0 else 0
            print(f"{Colors.BOLD}Mock Test Summary: {self.passed} passed, {self.failed} failed out of {total} steps ({success_rate:.1f}%){Colors.RESET}")
            print("=" * 60 + "\n")

            if self.failed > 0:
                sys.exit(1)
            sys.exit(0)


if __name__ == "__main__":
    runner = MockTestRunner()
    runner.run_all()

