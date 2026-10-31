#!/usr/bin/env python3
"""
test_backend.py - Standalone HTTP smoke test for Subscription Management System API.
Only depends on requests and the standard library.
Talks to the live API over HTTP.
"""

import os
import sys

# Auto-fallback to virtualenv python if requests is not installed in current interpreter
try:
    import requests
except ImportError:
    venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("[FATAL] 'requests' library not found. Please activate your virtualenv or run: pip install requests")
        sys.exit(1)

import time
import uuid
import subprocess

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000/api/v1")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@12345")

EP = {
    "health": "/health",
    "signup": "/auth/signup",
    "login": "/auth/login",
    "logout": "/auth/logout",
    "forgot_password": "/auth/forgot-password",
    "reset_password": "/auth/reset-password",
    "staff": "/staff",
    "staff_detail": "/staff/{id}",
    "taxes": "/taxes",
    "discounts": "/discounts",
    "products": "/products",
    "variants": "/products/{id}/variants",
    "plans": "/plans",
    "customers": "/customers",
    "quotations": "/quotations",
    "confirm_quotation": "/quotations/{id}/confirm",
    "subscriptions": "/subscriptions",
    "activate_subscription": "/subscriptions/{id}/activate",
    "pause_subscription": "/subscriptions/{id}/pause",
    "billing_run": "/billing/run",
    "invoices": "/invoices",
    "confirm_invoice": "/invoices/{id}/confirm",
    "invoice_pdf": "/invoices/{id}/pdf",
    "invoices_overdue": "/invoices/overdue",
    "payments": "/payments",
    "dashboard_summary": "/dashboard/summary",
}

SUFFIX = uuid.uuid4().hex[:6]


def PAYLOAD(name, **kwargs):
    payloads = {
        "valid_signup": {
            "email": f"smoke_cust_{SUFFIX}@example.com",
            "password": f"SecurePassword!{SUFFIX}123",
            "name": f"Smoke Customer {SUFFIX}",
            "company": "Smoke Test Corp",
            "phone": "555-0199",
            "billing_address": "789 Test Ave",
        },
        "weak_signup": {
            "email": f"weak_{SUFFIX}@example.com",
            "password": "weak",
            "name": "Weak Pass User",
        },
        "wrong_login": {
            "email": f"smoke_cust_{SUFFIX}@example.com",
            "password": "WrongPassword!999",
        },
        "customer_login": {
            "email": f"smoke_cust_{SUFFIX}@example.com",
            "password": f"SecurePassword!{SUFFIX}123",
        },
        "admin_login": {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
        },
        "forgot_password": {
            "email": f"smoke_cust_{SUFFIX}@example.com",
        },
        "create_tax": {
            "name": f"Smoke VAT {SUFFIX}",
            "rate": 10.0,
        },
        "create_discount": {
            "code": f"DISC_{SUFFIX.upper()}",
            "description": "Smoke Discount 10%",
            "discount_type": "percentage",
            "value": 10.0,
            "min_quantity": 1,
        },
        "create_product": {
            "name": f"Cloud Service {SUFFIX}",
            "sales_price": 100.0,
            "cost_price": 25.0,
        },
        "create_variant": {
            "name": f"High Capacity {SUFFIX}",
            "extra_price": 50.0,
        },
        "create_plan": {
            "name": f"Monthly Plan {SUFFIX}",
            "billing_period": "monthly",
            "min_quantity": 1,
            "start_date": "2026-01-01",
            "allow_pause": True,
            "allow_close": True,
            "allow_renew": True,
        },
        "create_staff": {
            "email": f"staff_{SUFFIX}@example.com",
            "password": f"StaffPass!{SUFFIX}123",
            "name": f"Staff Member {SUFFIX}",
            "department": "Engineering",
            "role": "staff",
        },
        "staff_login": {
            "email": f"staff_{SUFFIX}@example.com",
            "password": f"StaffPass!{SUFFIX}123",
        },
        "create_cust2": {
            "email": f"smoke_cust2_{SUFFIX}@example.com",
            "password": f"SecurePassword2!{SUFFIX}123",
            "name": f"Second Customer {SUFFIX}",
        },
        "cust2_login": {
            "email": f"smoke_cust2_{SUFFIX}@example.com",
            "password": f"SecurePassword2!{SUFFIX}123",
        },
    }
    base = payloads.get(name, {}).copy()
    base.update(kwargs)
    return base


class SmokeTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.context = {}
        self.server_process = None

    def ensure_server_running(self):
        health_url = BASE_URL.rstrip("/") + EP["health"]
        try:
            r = requests.get(health_url, timeout=1.5)
            if r.status_code == 200:
                return  # Server is already running
        except Exception:
            pass

        # Try to automatically launch server
        run_py = os.path.join(os.path.dirname(__file__), "run.py")
        if os.path.exists(run_py):
            print(f"[INFO] Server not responding at {health_url}.")
            print(f"[INFO] Auto-starting backend server via '{run_py}' for this test run...")
            env = os.environ.copy()
            env["PORT"] = "5000"
            self.server_process = subprocess.Popen(
                [sys.executable, run_py],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
            # Wait up to 5 seconds for server to boot
            for _ in range(25):
                time.sleep(0.2)
                try:
                    r = requests.get(health_url, timeout=1.0)
                    if r.status_code == 200:
                        print("[INFO] Backend server started successfully!\n")
                        return
                except Exception:
                    pass

        print(f"\n[FATAL] Could not connect to API server at {health_url}. Is the server running?")
        print("Please start the server in another terminal using: python run.py\n")
        sys.exit(1)

    def cleanup(self):
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=2)
            except Exception:
                pass

    def report(self, step_name, status, message=""):
        tag = f"[{status}]"
        if message:
            print(f"{tag:<8} {step_name} - {message}")
        else:
            print(f"{tag:<8} {step_name}")

        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "SKIP":
            self.skipped += 1

    def request(self, method, path, **kwargs):
        url = BASE_URL.rstrip("/") + path
        try:
            return requests.request(method, url, timeout=10, **kwargs)
        except requests.exceptions.ConnectionError:
            print(
                f"\n[FATAL] Could not connect to API server at {url}. Is the server running?\n"
            )
            self.cleanup()
            sys.exit(1)

    def run(self):
        self.ensure_server_running()

        print(f"=== Starting Smoke Test against {BASE_URL} (Suffix: {SUFFIX}) ===\n")

        try:
            self._execute_steps()
        finally:
            self.cleanup()

        # Summary
        print("\n" + "=" * 45)
        print(
            f"Test Summary: {self.passed} passed, {self.failed} failed, {self.skipped} skipped"
        )
        print("=" * 45 + "\n")

        if self.failed > 0:
            sys.exit(1)
        sys.exit(0)

    def _execute_steps(self):
        # Step 1: health check
        try:
            r = self.request("GET", EP["health"])
            if r.status_code == 200:
                self.report("1. health check", "PASS")
            else:
                self.report(
                    "1. health check",
                    "FAIL",
                    f"HTTP {r.status_code}: {r.text}",
                )
        except Exception as e:
            self.report("1. health check", "FAIL", str(e))

        # Step 2: signup valid
        signup_payload = PAYLOAD("valid_signup")
        r = self.request("POST", EP["signup"], json=signup_payload)
        if r.status_code == 201:
            data = r.json().get("data") or r.json()
            self.context["customer_id"] = data.get("customer_id") or data.get("id")
            self.report("2. signup valid", "PASS")
        else:
            self.report(
                "2. signup valid", "FAIL", f"HTTP {r.status_code}: {r.text}"
            )

        # Step 3: signup duplicate email rejected
        r = self.request("POST", EP["signup"], json=signup_payload)
        if r.status_code in (400, 409):
            self.report("3. signup duplicate email rejected", "PASS")
        else:
            self.report(
                "3. signup duplicate email rejected",
                "FAIL",
                f"Expected 400/409, got HTTP {r.status_code}: {r.text}",
            )

        # Step 4: signup weak password rejected
        r = self.request("POST", EP["signup"], json=PAYLOAD("weak_signup"))
        if r.status_code in (400, 422):
            self.report("4. signup weak password rejected", "PASS")
        else:
            self.report(
                "4. signup weak password rejected",
                "FAIL",
                f"Expected 400/422, got HTTP {r.status_code}: {r.text}",
            )

        # Step 5: login wrong password rejected
        r = self.request("POST", EP["login"], json=PAYLOAD("wrong_login"))
        if r.status_code == 401:
            self.report("5. login wrong password rejected", "PASS")
        else:
            self.report(
                "5. login wrong password rejected",
                "FAIL",
                f"Expected 401, got HTTP {r.status_code}: {r.text}",
            )

        # Step 6: customer login
        r = self.request("POST", EP["login"], json=PAYLOAD("customer_login"))
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token") or data.get("data", {}).get(
                "access_token"
            )
            self.context["customer_token"] = token
            cust_id = data.get("customer_id") or data.get("data", {}).get(
                "customer_id"
            )
            if cust_id:
                self.context["customer_id"] = cust_id
            self.report("6. customer login", "PASS")
        else:
            self.report(
                "6. customer login", "FAIL", f"HTTP {r.status_code}: {r.text}"
            )

        # Step 7: admin login
        r = self.request("POST", EP["login"], json=PAYLOAD("admin_login"))
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token") or data.get("data", {}).get(
                "access_token"
            )
            self.context["admin_token"] = token
            self.report("7. admin login", "PASS")
        else:
            self.report(
                "7. admin login", "FAIL", f"HTTP {r.status_code}: {r.text}"
            )

        # Step 8: forgot-password request
        r = self.request(
            "POST", EP["forgot_password"], json=PAYLOAD("forgot_password")
        )
        if r.status_code == 200:
            self.report("8. forgot-password request", "PASS")
        else:
            self.report(
                "8. forgot-password request",
                "FAIL",
                f"HTTP {r.status_code}: {r.text}",
            )

        # Step 9: protected route without token returns 401
        r = self.request("GET", EP["staff"])
        if r.status_code == 401:
            self.report("9. protected route without token returns 401", "PASS")
        else:
            hint = " (Check endpoint path)" if r.status_code in (404, 405) else ""
            self.report(
                "9. protected route without token returns 401",
                "FAIL",
                f"Expected 401, got HTTP {r.status_code}: {r.text}{hint}",
            )

        # Step 10: customer blocked from creating product (403)
        cust_token = self.context.get("customer_token")
        if cust_token:
            r = self.request(
                "POST",
                EP["products"],
                json=PAYLOAD("create_product"),
                headers={"Authorization": f"Bearer {cust_token}"},
            )
            if r.status_code == 403:
                self.report(
                    "10. customer blocked from creating product (403)", "PASS"
                )
            else:
                self.report(
                    "10. customer blocked from creating product (403)",
                    "FAIL",
                    f"Expected 403, got HTTP {r.status_code}: {r.text}",
                )
        else:
            self.report(
                "10. customer blocked from creating product (403)",
                "SKIP",
                "Customer token missing",
            )

        # Step 11: customer blocked from creating staff (403)
        if cust_token:
            r = self.request(
                "POST",
                EP["staff"],
                json=PAYLOAD("create_staff"),
                headers={"Authorization": f"Bearer {cust_token}"},
            )
            if r.status_code == 403:
                self.report(
                    "11. customer blocked from creating staff (403)", "PASS"
                )
            else:
                self.report(
                    "11. customer blocked from creating staff (403)",
                    "FAIL",
                    f"Expected 403, got HTTP {r.status_code}: {r.text}",
                )
        else:
            self.report(
                "11. customer blocked from creating staff (403)",
                "SKIP",
                "Customer token missing",
            )

        # Step 12: admin creates tax, discount, product, variant, plan
        adm_token = self.context.get("admin_token")
        if adm_token:
            headers = {"Authorization": f"Bearer {adm_token}"}
            try:
                # Tax
                r_tax = self.request(
                    "POST", EP["taxes"], json=PAYLOAD("create_tax"), headers=headers
                )
                tax_id = (r_tax.json().get("data") or r_tax.json()).get("id")

                # Discount
                r_disc = self.request(
                    "POST",
                    EP["discounts"],
                    json=PAYLOAD("create_discount"),
                    headers=headers,
                )
                disc_id = (r_disc.json().get("data") or r_disc.json()).get("id")

                # Product
                r_prod = self.request(
                    "POST",
                    EP["products"],
                    json=PAYLOAD("create_product"),
                    headers=headers,
                )
                prod_id = (r_prod.json().get("data") or r_prod.json()).get("id")

                # Variant
                r_var = self.request(
                    "POST",
                    EP["variants"].format(id=prod_id),
                    json=PAYLOAD("create_variant"),
                    headers=headers,
                )
                var_id = (r_var.json().get("data") or r_var.json()).get("id")

                # Plan
                r_plan = self.request(
                    "POST", EP["plans"], json=PAYLOAD("create_plan"), headers=headers
                )
                plan_id = (r_plan.json().get("data") or r_plan.json()).get("id")

                if all([tax_id, disc_id, prod_id, var_id, plan_id]):
                    self.context.update(
                        {
                            "tax_id": tax_id,
                            "discount_id": disc_id,
                            "product_id": prod_id,
                            "variant_id": var_id,
                            "plan_id": plan_id,
                        }
                    )
                    self.report(
                        "12. admin creates tax, discount, product, variant, plan",
                        "PASS",
                    )
                else:
                    self.report(
                        "12. admin creates tax, discount, product, variant, plan",
                        "FAIL",
                        f"Failed creating entities: tax={tax_id}, disc={disc_id}, prod={prod_id}, var={var_id}, plan={plan_id}",
                    )
            except Exception as e:
                self.report(
                    "12. admin creates tax, discount, product, variant, plan",
                    "FAIL",
                    str(e),
                )
        else:
            self.report(
                "12. admin creates tax, discount, product, variant, plan",
                "SKIP",
                "Admin token missing",
            )

        # Step 13: admin creates staff and staff logs in
        if adm_token:
            r_staff = self.request(
                "POST",
                EP["staff"],
                json=PAYLOAD("create_staff"),
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_staff.status_code == 201:
                r_slogin = self.request(
                    "POST", EP["login"], json=PAYLOAD("staff_login")
                )
                if r_slogin.status_code == 200:
                    st_token = r_slogin.json().get("access_token") or r_slogin.json().get(
                        "data", {}
                    ).get("access_token")
                    self.context["staff_token"] = st_token
                    self.report(
                        "13. admin creates staff and staff logs in", "PASS"
                    )
                else:
                    self.report(
                        "13. admin creates staff and staff logs in",
                        "FAIL",
                        f"Staff login failed: HTTP {r_slogin.status_code}",
                    )
            else:
                self.report(
                    "13. admin creates staff and staff logs in",
                    "FAIL",
                    f"Staff create failed: HTTP {r_staff.status_code}",
                )
        else:
            self.report(
                "13. admin creates staff and staff logs in",
                "SKIP",
                "Admin token missing",
            )

        # Step 14: staff blocked from creating product (403)
        st_token = self.context.get("staff_token")
        if st_token:
            r = self.request(
                "POST",
                EP["products"],
                json=PAYLOAD("create_product"),
                headers={"Authorization": f"Bearer {st_token}"},
            )
            if r.status_code == 403:
                self.report(
                    "14. staff blocked from creating product (403)", "PASS"
                )
            else:
                self.report(
                    "14. staff blocked from creating product (403)",
                    "FAIL",
                    f"Expected 403, got HTTP {r.status_code}: {r.text}",
                )
        else:
            self.report(
                "14. staff blocked from creating product (403)",
                "SKIP",
                "Staff token missing",
            )

        # Step 15: create quotation
        if adm_token and self.context.get("plan_id"):
            q_body = {
                "customer_id": self.context["customer_id"],
                "plan_id": self.context["plan_id"],
                "validity_days": 30,
                "lines": [
                    {
                        "product_id": self.context["product_id"],
                        "variant_id": self.context["variant_id"],
                        "quantity": 2,
                        "tax_id": self.context["tax_id"],
                        "discount_id": self.context["discount_id"],
                    }
                ],
            }
            r_q = self.request(
                "POST",
                EP["quotations"],
                json=q_body,
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_q.status_code == 201:
                q_id = (r_q.json().get("data") or r_q.json()).get("id")
                self.context["quotation_id"] = q_id
                self.report("15. create quotation", "PASS")
            else:
                self.report(
                    "15. create quotation",
                    "FAIL",
                    f"HTTP {r_q.status_code}: {r_q.text}",
                )
        else:
            self.report("15. create quotation", "SKIP", "Prerequisites missing")

        # Step 16: confirm quotation to create the subscription
        q_id = self.context.get("quotation_id")
        if q_id and adm_token:
            r_cq = self.request(
                "POST",
                EP["confirm_quotation"].format(id=q_id),
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_cq.status_code in (200, 201):
                c_data = r_cq.json().get("data") or r_cq.json()
                sub_id = c_data.get("subscription_id") or c_data.get("id")
                self.context["subscription_id"] = sub_id
                self.report(
                    "16. confirm quotation to create the subscription", "PASS"
                )
            else:
                self.report(
                    "16. confirm quotation to create the subscription",
                    "FAIL",
                    f"HTTP {r_cq.status_code}: {r_cq.text}",
                )
        else:
            self.report(
                "16. confirm quotation to create the subscription",
                "SKIP",
                "Quotation ID missing",
            )

        # Step 17: activate subscription
        sub_id = self.context.get("subscription_id")
        if sub_id and adm_token:
            r_act = self.request(
                "POST",
                EP["activate_subscription"].format(id=sub_id),
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_act.status_code == 200:
                self.report("17. activate subscription", "PASS")
            else:
                self.report(
                    "17. activate subscription",
                    "FAIL",
                    f"HTTP {r_act.status_code}: {r_act.text}",
                )
        else:
            self.report(
                "17. activate subscription", "SKIP", "Subscription ID missing"
            )

        # Step 18: billing run creates an invoice
        if adm_token and sub_id:
            r_bill = self.request(
                "POST",
                EP["billing_run"],
                json={"as_of_date": "2026-11-01"},
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_bill.status_code == 200:
                r_invs = self.request(
                    "GET",
                    f"{EP['invoices']}?subscription_id={sub_id}",
                    headers={"Authorization": f"Bearer {adm_token}"},
                )
                items = r_invs.json().get("items") or r_invs.json().get("data") or []
                if items:
                    inv = items[0]
                    self.context["invoice_id"] = inv["id"]
                    self.context["invoice_total"] = inv["total"]
                    self.report("18. billing run creates an invoice", "PASS")
                else:
                    self.report(
                        "18. billing run creates an invoice",
                        "FAIL",
                        "No invoice found for subscription after billing run",
                    )
            else:
                self.report(
                    "18. billing run creates an invoice",
                    "FAIL",
                    f"HTTP {r_bill.status_code}: {r_bill.text}",
                )
        else:
            self.report(
                "18. billing run creates an invoice",
                "SKIP",
                "Prerequisites missing",
            )

        # Step 19: billing run a second time creates no duplicate invoice
        if adm_token and sub_id:
            r_bill2 = self.request(
                "POST",
                EP["billing_run"],
                json={"as_of_date": "2026-11-01"},
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            r_invs2 = self.request(
                "GET",
                f"{EP['invoices']}?subscription_id={sub_id}",
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            items2 = (
                r_invs2.json().get("items") or r_invs2.json().get("data") or []
            )
            if len(items2) == 1:
                self.report(
                    "19. billing run a second time creates no duplicate invoice",
                    "PASS",
                )
            else:
                self.report(
                    "19. billing run a second time creates no duplicate invoice",
                    "FAIL",
                    f"Expected 1 invoice, found {len(items2)}",
                )
        else:
            self.report(
                "19. billing run a second time creates no duplicate invoice",
                "SKIP",
                "Prerequisites missing",
            )

        # Step 20: confirm invoice
        inv_id = self.context.get("invoice_id")
        if inv_id and adm_token:
            r_cinv = self.request(
                "POST",
                EP["confirm_invoice"].format(id=inv_id),
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_cinv.status_code == 200:
                self.report("20. confirm invoice", "PASS")
            else:
                self.report(
                    "20. confirm invoice",
                    "FAIL",
                    f"HTTP {r_cinv.status_code}: {r_cinv.text}",
                )
        else:
            self.report("20. confirm invoice", "SKIP", "Invoice ID missing")

        # Step 21: invoice PDF is a valid PDF (starts with %PDF)
        if inv_id and adm_token:
            r_pdf = self.request(
                "GET",
                EP["invoice_pdf"].format(id=inv_id),
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_pdf.status_code == 200 and r_pdf.content.startswith(b"%PDF"):
                self.report(
                    "21. invoice PDF is a valid PDF (starts with %PDF)", "PASS"
                )
            else:
                self.report(
                    "21. invoice PDF is a valid PDF (starts with %PDF)",
                    "FAIL",
                    f"Status {r_pdf.status_code}, starts with {r_pdf.content[:10]}",
                )
        else:
            self.report(
                "21. invoice PDF is a valid PDF (starts with %PDF)",
                "SKIP",
                "Invoice ID missing",
            )

        # Step 22: customer can list own invoices
        if cust_token and inv_id:
            r_myinv = self.request(
                "GET",
                EP["invoices"],
                headers={"Authorization": f"Bearer {cust_token}"},
            )
            my_items = (
                r_myinv.json().get("items") or r_myinv.json().get("data") or []
            )
            if any(i["id"] == inv_id for i in my_items):
                self.report("22. customer can list own invoices", "PASS")
            else:
                self.report(
                    "22. customer can list own invoices",
                    "FAIL",
                    f"Invoice {inv_id} not in customer list",
                )
        else:
            self.report(
                "22. customer can list own invoices",
                "SKIP",
                "Prerequisites missing",
            )

        # Step 23: a different customer gets 403/404 for someone else's invoice
        if inv_id:
            self.request("POST", EP["signup"], json=PAYLOAD("create_cust2"))
            r_c2log = self.request(
                "POST", EP["login"], json=PAYLOAD("cust2_login")
            )
            c2_token = r_c2log.json().get("access_token") or r_c2log.json().get(
                "data", {}
            ).get("access_token")

            if c2_token:
                r_other = self.request(
                    "GET",
                    f"{EP['invoices']}/{inv_id}",
                    headers={"Authorization": f"Bearer {c2_token}"},
                )
                if r_other.status_code in (403, 404):
                    self.report(
                        "23. a different customer gets 403/404 for someone else's invoice",
                        "PASS",
                    )
                else:
                    self.report(
                        "23. a different customer gets 403/404 for someone else's invoice",
                        "FAIL",
                        f"Expected 403/404, got HTTP {r_other.status_code}: {r_other.text}",
                    )
            else:
                self.report(
                    "23. a different customer gets 403/404 for someone else's invoice",
                    "SKIP",
                    "Customer 2 login failed",
                )
        else:
            self.report(
                "23. a different customer gets 403/404 for someone else's invoice",
                "SKIP",
                "Invoice ID missing",
            )

        # Step 24: record a payment
        inv_total = self.context.get("invoice_total", 50.0)
        pay_amount = min(50.0, float(inv_total))
        if inv_id and adm_token:
            pay_body = {
                "invoice_id": inv_id,
                "amount": pay_amount,
                "method": "credit_card",
                "date": "2026-10-31",
                "note": "Smoke test payment",
            }
            r_pay = self.request(
                "POST",
                EP["payments"],
                json=pay_body,
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_pay.status_code == 201:
                self.report("24. record a payment", "PASS")
            else:
                self.report(
                    "24. record a payment",
                    "FAIL",
                    f"HTTP {r_pay.status_code}: {r_pay.text}",
                )
        else:
            self.report("24. record a payment", "SKIP", "Invoice ID missing")

        # Step 25: overpayment rejected
        if inv_id and adm_token:
            excess_amount = float(inv_total) + 1000.0
            pay_excess = {
                "invoice_id": inv_id,
                "amount": excess_amount,
                "method": "credit_card",
            }
            r_opay = self.request(
                "POST",
                EP["payments"],
                json=pay_excess,
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_opay.status_code in (400, 422):
                self.report("25. overpayment rejected", "PASS")
            else:
                self.report(
                    "25. overpayment rejected",
                    "FAIL",
                    f"Expected 400/422, got HTTP {r_opay.status_code}: {r_opay.text}",
                )
        else:
            self.report(
                "25. overpayment rejected", "SKIP", "Invoice ID missing"
            )

        # Step 26: overdue list works
        if adm_token:
            r_overdue = self.request(
                "GET",
                EP["invoices_overdue"],
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            if r_overdue.status_code == 200:
                self.report("26. overdue list works", "PASS")
            else:
                self.report(
                    "26. overdue list works",
                    "FAIL",
                    f"HTTP {r_overdue.status_code}: {r_overdue.text}",
                )
        else:
            self.report(
                "26. overdue list works", "SKIP", "Admin token missing"
            )

        # Step 27: dashboard responds in under 2 seconds
        if adm_token:
            t0 = time.time()
            r_dash = self.request(
                "GET",
                EP["dashboard_summary"],
                headers={"Authorization": f"Bearer {adm_token}"},
            )
            elapsed = time.time() - t0
            if r_dash.status_code == 200 and elapsed < 2.0:
                self.report(
                    "27. dashboard responds in under 2 seconds",
                    "PASS",
                    f"Took {elapsed:.3f}s",
                )
            else:
                self.report(
                    "27. dashboard responds in under 2 seconds",
                    "FAIL",
                    f"Status: {r_dash.status_code}, Elapsed: {elapsed:.3f}s",
                )
        else:
            self.report(
                "27. dashboard responds in under 2 seconds",
                "SKIP",
                "Admin token missing",
            )

        # Step 28: logout
        if cust_token:
            r_logout = self.request(
                "POST",
                EP["logout"],
                headers={"Authorization": f"Bearer {cust_token}"},
            )
            if r_logout.status_code == 200:
                self.report("28. logout", "PASS")
            else:
                self.report(
                    "28. logout",
                    "FAIL",
                    f"HTTP {r_logout.status_code}: {r_logout.text}",
                )
        else:
            self.report("28. logout", "SKIP", "Customer token missing")


if __name__ == "__main__":
    runner = SmokeTestRunner()
    runner.run()
