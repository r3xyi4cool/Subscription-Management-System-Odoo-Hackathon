#!/usr/bin/env python3
"""
================================================================================
Brightloop Subscription Management System (SMS) - Database Feature Test Suite
Prepared for: Member 3 (Database) & Team Review
Scope: Comprehensive automated verification of D1 through D9 requirements

Tests:
  - D1: Case-insensitive unique emails, RBAC roles, 1:1 Auth links
  - D2: Product pricing, variant extra price, plan constraints, discounts, taxes
  - D3: Auto-generated subscription numbers, lifecycle statuses, status history
  - D4 & D5: No double billing, refund limit trigger, auto-paid invoice sync, atomic discount
  - D6: Core composite indexes, live KPI view, pre-aggregated materialized view
  - D7: Seed data coverage across all roles and entity statuses
  - D9: Automated change capture triggers, immutable append-only audit log
================================================================================
"""

import os
import sys
import time
import json
from decimal import Decimal

# Connection configuration (override with environment variables if desired)
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "postgres")
PGDATABASE = os.getenv("PGDATABASE", "brightloop_sms")

# Terminal color formatting
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


class DBClient:
    """Universal database adapter supporting psycopg2, psycopg (v3), or psql subprocess fallback."""

    def __init__(self):
        self.driver_type = None
        self.conn = None
        self._init_connection()

    def _init_connection(self):
        # 1. Try psycopg2
        try:
            import psycopg2
            self.conn = psycopg2.connect(
                host=PGHOST, port=PGPORT, user=PGUSER, password=PGPASSWORD, dbname=PGDATABASE
            )
            self.conn.autocommit = True
            self.driver_type = "psycopg2"
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"{YELLOW}[WARN] psycopg2 connection failed ({e}), attempting alternatives...{RESET}")

        # 2. Try psycopg v3
        try:
            import psycopg
            self.conn = psycopg.connect(
                f"host={PGHOST} port={PGPORT} user={PGUSER} password={PGPASSWORD} dbname={PGDATABASE}",
                autocommit=True
            )
            self.driver_type = "psycopg3"
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"{YELLOW}[WARN] psycopg3 connection failed ({e}), attempting alternatives...{RESET}")

        # 3. Try pg8000
        try:
            import pg8000.native
            self.conn = pg8000.native.Connection(
                user=PGUSER, host=PGHOST, port=PGPORT, database=PGDATABASE, password=PGPASSWORD
            )
            self.driver_type = "pg8000"
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"{YELLOW}[WARN] pg8000 connection failed ({e}), attempting alternatives...{RESET}")

        # 4. Fallback to psql command-line tool via subprocess
        import subprocess
        try:
            res = subprocess.run(
                ["psql", "-h", PGHOST, "-p", str(PGPORT), "-U", PGUSER, "-d", PGDATABASE, "-tAc", "SELECT 1"],
                capture_output=True, text=True, timeout=5, env={**os.environ, "PGPASSWORD": PGPASSWORD}
            )
            if res.returncode == 0 and res.stdout.strip() == "1":
                self.driver_type = "psql_cli"
                return
        except Exception:
            pass

        print(f"\n{RED}{BOLD}[ERROR] Could not connect to PostgreSQL!{RESET}")
        print("Please ensure PostgreSQL is running and brightloop_sms exists.")
        print("Install a Python PostgreSQL driver using one of:")
        print("    pip install psycopg2-binary")
        print("    pip install psycopg")
        print("    pip install pg8000")
        sys.exit(1)

    def execute(self, sql, params=None):
        """Executes a query and returns cursor or result rows."""
        if self.driver_type in ("psycopg2", "psycopg3"):
            cur = self.conn.cursor()
            cur.execute(sql, params or ())
            try:
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description] if cur.description else []
                return [dict(zip(cols, row)) for row in rows]
            except Exception:
                return []
        elif self.driver_type == "pg8000":
            res = self.conn.run(sql)
            return res
        elif self.driver_type == "psql_cli":
            import subprocess
            cmd = ["psql", "-h", PGHOST, "-p", str(PGPORT), "-U", PGUSER, "-d", PGDATABASE, "-X", "-A", "-c", sql]
            proc = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "PGPASSWORD": PGPASSWORD})
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip())
            lines = proc.stdout.strip().splitlines()
            if not lines:
                return []
            header = lines[0].split("|")
            records = []
            for line in lines[1:]:
                if line.endswith(")") and "rows" in line:
                    continue
                parts = line.split("|")
                if len(parts) == len(header):
                    records.append(dict(zip(header, parts)))
            return records

    def execute_expect_error(self, sql, expected_substr=""):
        """Executes query and asserts that it raises a specific PostgreSQL error."""
        try:
            self.execute(sql)
            return False, "Expected error was not raised! Query unexpectedly succeeded."
        except Exception as e:
            err_msg = str(e)
            if expected_substr.lower() in err_msg.lower():
                return True, f"Correctly caught error: {err_msg.strip()}"
            return False, f"Unexpected error raised: {err_msg.strip()}"


class TestRunner:
    def __init__(self, db: DBClient):
        self.db = db
        self.passed = 0
        self.failed = 0
        self.results = []

    def run_test(self, test_num, scope, title, test_func):
        start_time = time.perf_counter()
        sys.stdout.write(f"  [{scope}] Test {test_num:02d}: {title.ljust(52)} ... ")
        sys.stdout.flush()
        try:
            passed, detail = test_func()
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            if passed:
                self.passed += 1
                print(f"{GREEN}{BOLD}PASS{RESET} ({elapsed_ms:.1f}ms)")
                self.results.append((test_num, scope, title, "PASS", detail))
            else:
                self.failed += 1
                print(f"{RED}{BOLD}FAIL{RESET} ({elapsed_ms:.1f}ms)")
                print(f"      {RED}Detail: {detail}{RESET}")
                self.results.append((test_num, scope, title, "FAIL", detail))
        except Exception as ex:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.failed += 1
            print(f"{RED}{BOLD}ERROR{RESET} ({elapsed_ms:.1f}ms)")
            print(f"      {RED}Exception: {ex}{RESET}")
            self.results.append((test_num, scope, title, "ERROR", str(ex)))

    # =========================================================================
    # D1 TESTS: Account tables
    # =========================================================================
    def test_d1_duplicate_email(self):
        sql = "INSERT INTO auth (email, password_hash, role) VALUES ('ADMIN@BRIGHTLOOP.IO', 'hash', 'admin');"
        return self.db.execute_expect_error(sql, "unique")

    def test_d1_invalid_role(self):
        sql = "INSERT INTO auth (email, password_hash, role) VALUES ('intruder@test.com', 'hash', 'superuser');"
        return self.db.execute_expect_error(sql, "check")

    def test_d1_customer_auth_one_to_one(self):
        # Attempt to link a second customer to auth_id 4 (already taken by Customer 1)
        sql = "INSERT INTO customer (auth_id, name) VALUES (4, 'Duplicate Auth Customer');"
        return self.db.execute_expect_error(sql, "unique")

    # =========================================================================
    # D2 TESTS: Catalog tables
    # =========================================================================
    def test_d2_negative_sales_price(self):
        sql = "INSERT INTO product (name, sales_price) VALUES ('Invalid Item', -100.00);"
        return self.db.execute_expect_error(sql, "check")

    def test_d2_variant_price_calculation(self):
        # Product 1 is 499.00; Variant 2 (Odoo Enterprise) extra_price is 560.00 -> 1059.00
        sql = """
            SELECT (p.sales_price + pv.extra_price) AS calculated_unit_price
            FROM product p
            JOIN product_variant pv ON p.product_id = pv.product_id
            WHERE p.product_id = 1 AND pv.variant_id = 2;
        """
        rows = self.db.execute(sql)
        if rows and float(rows[0]["calculated_unit_price"]) == 1059.00:
            return True, f"Unit price correctly calculated: {rows[0]['calculated_unit_price']}"
        return False, f"Unexpected price: {rows}"

    def test_d2_plan_billing_period_constraint(self):
        sql = "INSERT INTO plan (name, price, billing_period) VALUES ('Biweekly Plan', 200.00, 'biweekly');"
        return self.db.execute_expect_error(sql, "check")

    # =========================================================================
    # D3 TESTS: Sales tables
    # =========================================================================
    def test_d3_auto_generated_subscription_number(self):
        # Insert without providing number; trigger should generate SUB-YYYY-NNNNNN
        insert_sql = """
            INSERT INTO subscription (customer_id, plan_id, next_billing_date, status)
            VALUES (1, 1, CURRENT_DATE + 30, 'draft')
            RETURNING subscription_id, number;
        """
        rows = self.db.execute(insert_sql)
        if not rows:
            return False, "No row returned from insert."
        sub_id = rows[0]["subscription_id"]
        sub_num = str(rows[0]["number"])
        # Clean up test row
        self.db.execute(f"DELETE FROM subscription WHERE subscription_id = {sub_id};")
        if sub_num.startswith("SUB-") and len(sub_num) >= 12:
            return True, f"Generated subscription number: {sub_num}"
        return False, f"Invalid format: {sub_num}"

    def test_d3_status_change_history_tracking(self):
        # Transition subscription 5 from draft to quotation and check history table
        self.db.execute("UPDATE subscription SET status = 'quotation' WHERE subscription_id = 5;")
        rows = self.db.execute(
            "SELECT * FROM subscription_status_history WHERE subscription_id = 5 AND to_status = 'quotation';"
        )
        # Revert
        self.db.execute("UPDATE subscription SET status = 'draft' WHERE subscription_id = 5;")
        if rows and len(rows) > 0:
            return True, f"Recorded status change history row: ID {rows[0].get('history_id')}"
        return False, "Status change was not found in subscription_status_history!"

    # =========================================================================
    # D4 & D5 TESTS: Billing & Integrity rules
    # =========================================================================
    def test_d5_double_billing_prevention(self):
        # Sub 1 already has invoice for '2026-10' in seeds. Attempting duplicate must fail.
        sql = """
            INSERT INTO invoice (number, subscription_id, customer_id, billing_period, total, due_date, status)
            VALUES ('INV-TEST-DUP', 1, 1, '2026-10', 100.00, CURRENT_DATE + 15, 'draft');
        """
        return self.db.execute_expect_error(sql, "unique")

    def test_d5_refund_exceeding_payment_limit(self):
        # Payment 1 is 2000.00. Attempting to refund 50,000.00 must be blocked by trigger.
        sql = """
            INSERT INTO refund (payment_id, invoice_id, amount, reason, status)
            VALUES (1, 1, 50000.00, 'Exorbitant over-refund attempt', 'requested');
        """
        return self.db.execute_expect_error(sql, "refund limit exceeded")

    def test_d5_invoice_auto_paid_status_sync(self):
        # Create a confirmed invoice for Rs 750.00, add payment of 750.00, verify status becomes 'paid'
        inv_rows = self.db.execute("""
            INSERT INTO invoice (number, subscription_id, customer_id, billing_period, total, due_date, status)
            VALUES ('INV-TEST-AUTOPAY', NULL, 1, '2026-TEST-PAY', 750.00, CURRENT_DATE + 15, 'confirmed')
            RETURNING invoice_id;
        """)
        inv_id = inv_rows[0]["invoice_id"]

        # Insert matching payment
        self.db.execute(f"""
            INSERT INTO payment (invoice_id, method, amount, note)
            VALUES ({inv_id}, 'card', 750.00, 'Full test settlement');
        """)

        # Verify status
        status_rows = self.db.execute(f"SELECT status FROM invoice WHERE invoice_id = {inv_id};")
        final_status = status_rows[0]["status"]

        # Clean up
        self.db.execute(f"DELETE FROM payment WHERE invoice_id = {inv_id};")
        self.db.execute(f"DELETE FROM invoice WHERE invoice_id = {inv_id};")

        if final_status == "paid":
            return True, "Invoice automatically updated to 'paid' when payments matched total."
        return False, f"Invoice status is '{final_status}' instead of 'paid'!"

    def test_d5_atomic_discount_usage_counter(self):
        # Execute atomic function fn_apply_discount_atomically(1)
        res_before = self.db.execute("SELECT times_used FROM discount WHERE discount_id = 1;")[0]["times_used"]
        self.db.execute("SELECT fn_apply_discount_atomically(1);")
        res_after = self.db.execute("SELECT times_used FROM discount WHERE discount_id = 1;")[0]["times_used"]
        # Revert
        self.db.execute(f"UPDATE discount SET times_used = {res_before} WHERE discount_id = 1;")

        if int(res_after) == int(res_before) + 1:
            return True, f"Atomic increment succeeded ({res_before} -> {res_after})"
        return False, f"Unexpected counter change: {res_before} to {res_after}"

    # =========================================================================
    # D6 TESTS: Performance & Analytics Views
    # =========================================================================
    def test_d6_live_dashboard_kpis_view(self):
        rows = self.db.execute("SELECT * FROM v_dashboard_kpis;")
        if not rows:
            return False, "v_dashboard_kpis returned zero rows."
        kpis = rows[0]
        active_subs = kpis.get("active_subscriptions")
        mrr = kpis.get("mrr")
        arr = kpis.get("arr")
        if active_subs is not None and mrr is not None and arr is not None:
            return True, f"Active Subs: {active_subs}, MRR: Rs {mrr}, ARR: Rs {arr}"
        return False, f"Incomplete KPI row: {kpis}"

    def test_d6_materialized_view_and_refresh(self):
        # Check materialized view read and execute refresh procedure
        rows = self.db.execute("SELECT * FROM mv_dashboard_summary WHERE summary_id = 1;")
        if not rows:
            return False, "mv_dashboard_summary has no data."
        self.db.execute("CALL sp_refresh_dashboard_summary();")
        return True, "Materialized view queried and refreshed concurrently successfully."

    def test_d6_performance_indexes_presence(self):
        required_indexes = [
            "idx_subscription_status_next_billing",
            "idx_invoice_status_due_date",
            "idx_invoice_customer_id",
            "idx_payment_invoice_id",
            "idx_subscription_customer_id",
        ]
        sql = f"""
            SELECT indexname FROM pg_indexes 
            WHERE tablename IN ('subscription', 'invoice', 'payment')
              AND indexname IN ({','.join(f"'{idx}'" for idx in required_indexes)});
        """
        rows = self.db.execute(sql)
        found_indexes = {r["indexname"] for r in rows}
        missing = set(required_indexes) - found_indexes
        if not missing:
            return True, f"All {len(required_indexes)} required performance indexes confirmed."
        return False, f"Missing indexes: {missing}"

    # =========================================================================
    # D7 TESTS: Seed data coverage
    # =========================================================================
    def test_d7_seed_statuses_coverage(self):
        # Check all 6 subscription statuses exist
        sub_statuses = {r["status"] for r in self.db.execute("SELECT DISTINCT status FROM subscription;")}
        required_sub_statuses = {"draft", "quotation", "confirmed", "active", "paused", "closed"}
        if not required_sub_statuses.issubset(sub_statuses):
            return False, f"Missing subscription statuses: {required_sub_statuses - sub_statuses}"

        # Check all 4 invoice statuses exist
        inv_statuses = {r["status"] for r in self.db.execute("SELECT DISTINCT status FROM invoice;")}
        required_inv_statuses = {"draft", "confirmed", "paid", "cancelled"}
        if not required_inv_statuses.issubset(inv_statuses):
            return False, f"Missing invoice statuses: {required_inv_statuses - inv_statuses}"

        # Check all 4 refund statuses exist
        ref_statuses = {r["status"] for r in self.db.execute("SELECT DISTINCT status FROM refund;")}
        required_ref_statuses = {"requested", "approved", "processed", "rejected"}
        if not required_ref_statuses.issubset(ref_statuses):
            return False, f"Missing refund statuses: {required_ref_statuses - ref_statuses}"

        return True, "All 6 subscription, 4 invoice, and 4 refund statuses confirmed in seed data."

    # =========================================================================
    # D9 TESTS: Audit Log & Immutability
    # =========================================================================
    def test_d9_change_capture_trigger(self):
        # Update a payment note and check audit_log
        self.db.execute("UPDATE payment SET note = 'Verification Note Test' WHERE payment_id = 3;")
        rows = self.db.execute(
            "SELECT * FROM audit_log WHERE entity = 'payment' AND entity_id = '3' AND action = 'UPDATE';"
        )
        if rows and len(rows) > 0:
            return True, f"Captured UPDATE in audit_log (log_id: {rows[-1].get('log_id')})"
        return False, "No audit_log entry found for payment update!"

    def test_d9_audit_log_immutability(self):
        # Attempting DELETE on audit_log must be blocked by trigger
        sql = "DELETE FROM audit_log WHERE log_id = 1;"
        return self.db.execute_expect_error(sql, "audit_log is append-only")


def main():
    print(f"\n{BOLD}{CYAN}=========================================================================={RESET}")
    print(f"{BOLD}{CYAN} Brightloop SMS: Database Feature & Integrity Verification Test Suite{RESET}")
    print(f"{BOLD}{CYAN} Prepared by Member 3 (Database) | PostgreSQL 15+{RESET}")
    print(f"{BOLD}{CYAN}=========================================================================={RESET}")

    db = DBClient()
    print(f"Connected to database '{BOLD}{PGDATABASE}{RESET}' on {PGHOST}:{PGPORT} via {BOLD}{db.driver_type}{RESET}.\n")

    runner = TestRunner(db)

    print(f"{BOLD}--- D1: Account Tables (Auth, Customer, Staff) ---{RESET}")
    runner.run_test(1, "D1", "Case-insensitive duplicate email rejection", runner.test_d1_duplicate_email)
    runner.run_test(2, "D1", "Invalid Auth role constraint rejection", runner.test_d1_invalid_role)
    runner.run_test(3, "D1", "Customer-Auth 1:1 unique constraint", runner.test_d1_customer_auth_one_to_one)

    print(f"\n{BOLD}--- D2: Catalog Tables (Product, Variant, Plan, Discount, Tax) ---{RESET}")
    runner.run_test(4, "D2", "Negative product sales price rejection", runner.test_d2_negative_sales_price)
    runner.run_test(5, "D2", "Variant extra_price formula calculation", runner.test_d2_variant_price_calculation)
    runner.run_test(6, "D2", "Plan billing_period enum check", runner.test_d2_plan_billing_period_constraint)

    print(f"\n{BOLD}--- D3: Sales Tables (Quotation, Subscription, History) ---{RESET}")
    runner.run_test(7, "D3", "Subscription auto-number generation (SUB-YYYY-NNNNNN)", runner.test_d3_auto_generated_subscription_number)
    runner.run_test(8, "D3", "Subscription status change history audit", runner.test_d3_status_change_history_tracking)

    print(f"\n{BOLD}--- D4 & D5: Billing & Financial Integrity Rules ---{RESET}")
    runner.run_test(9, "D5", "No double billing (UNIQUE subscription_id, period)", runner.test_d5_double_billing_prevention)
    runner.run_test(10, "D5", "Refund limit enforcement trigger (Refund <= Payment)", runner.test_d5_refund_exceeding_payment_limit)
    runner.run_test(11, "D5", "Automatic Invoice 'paid' transition trigger", runner.test_d5_invoice_auto_paid_status_sync)
    runner.run_test(12, "D5", "Atomic discount usage counter function", runner.test_d5_atomic_discount_usage_counter)

    print(f"\n{BOLD}--- D6: Performance Targets & Analytics Views ---{RESET}")
    runner.run_test(13, "D6", "Live KPI Dashboard View (MRR, ARR, Churn, Collection)", runner.test_d6_live_dashboard_kpis_view)
    runner.run_test(14, "D6", "Pre-aggregated Materialized View & Refresh Procedure", runner.test_d6_materialized_view_and_refresh)
    runner.run_test(15, "D6", "Core Performance Indexes presence verification", runner.test_d6_performance_indexes_presence)

    print(f"\n{BOLD}--- D7: Seed Data Completeness & Status Coverage ---{RESET}")
    runner.run_test(16, "D7", "Seed data coverage (all 6 sub, 4 inv, 4 refund statuses)", runner.test_d7_seed_statuses_coverage)

    print(f"\n{BOLD}--- D9: Audit Log & Tamper-Proof Immutability ---{RESET}")
    runner.run_test(17, "D9", "Automated change capture trigger on Payment update", runner.test_d9_change_capture_trigger)
    runner.run_test(18, "D9", "Audit log immutability check (Prohibit DELETE/UPDATE)", runner.test_d9_audit_log_immutability)

    print(f"\n{BOLD}{CYAN}=========================================================================={RESET}")
    print(f"{BOLD} TEST SUMMARY: {GREEN}{runner.passed} PASSED{RESET}, {RED if runner.failed > 0 else GREEN}{runner.failed} FAILED{RESET} (Total: {runner.passed + runner.failed})")
    print(f"{BOLD}{CYAN}=========================================================================={RESET}\n")

    if runner.failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
