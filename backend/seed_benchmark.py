#!/usr/bin/env python3
"""
seed_benchmark.py - Local Performance Benchmarking Suite for SMS
Generates 1,000 customers, 5,000 subscriptions, 10,000 invoices, 10,000 audit logs,
and benchmarks dashboard and billing endpoints to verify sub-2.0s response times.
"""

import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.customer import Customer
from backend.app.models.catalog import Plan, Product
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice, InvoiceLine, Payment
from backend.app.models.audit import AuditLog
from backend.app.services.billing_service import BillingService
from flask_jwt_extended import create_access_token


def run_benchmark(db_url: str = None) -> dict:
    if db_url:
        os.environ["DATABASE_URL"] = db_url

    app = create_app()

    with app.app_context():
        db.create_all()

        print("=" * 70)
        print("          SMS BENCHMARK DATASET GENERATION & PERFORMANCE RUNNER")
        print("=" * 70)

        # 1. Base Setup (Admin, Plans, Products)
        admin = Auth.query.filter_by(role="admin").first()
        if not admin:
            admin = Auth(email="admin_bench@example.com", role="admin", is_active=True)
            admin.set_password("Admin@12345")
            db.session.add(admin)
            db.session.commit()

        plan = Plan.query.first()
        if not plan:
            plan = Plan(
                name="Enterprise Monthly",
                billing_period="monthly",
                min_quantity=1,
                start_date=date(2026, 1, 1),
                is_active=True,
            )
            db.session.add(plan)
            db.session.commit()

        product = Product.query.first()
        if not product:
            product = Product(name="Core License", sales_price=Decimal("150.00"), is_active=True)
            db.session.add(product)
            db.session.commit()

        today = date.today()

        # 2. Customers (Target: 1,000)
        current_custs = Customer.query.count()
        needed_custs = max(0, 1000 - current_custs)
        if needed_custs > 0:
            print(f"  Bulk inserting {needed_custs} customers...")
            cust_mappings = []
            for i in range(needed_custs):
                idx = current_custs + i + 1
                cust_mappings.append({
                    "name": f"Customer Enterprise {idx}",
                    "email": f"client{idx}@corp.local",
                    "company": f"Corp {idx} Inc",
                })
            db.session.bulk_insert_mappings(Customer, cust_mappings)
            db.session.commit()

        all_cust_ids = [c[0] for c in db.session.query(Customer.id).all()]

        # 3. Subscriptions (Target: 5,000)
        current_subs = Subscription.query.count()
        needed_subs = max(0, 5000 - current_subs)
        if needed_subs > 0:
            print(f"  Bulk inserting {needed_subs} subscriptions...")
            sub_mappings = []
            for i in range(needed_subs):
                idx = current_subs + i + 1
                cust_id = all_cust_ids[i % len(all_cust_ids)]
                status = "active" if (idx % 6 != 0) else ("paused" if (idx % 12 == 0) else "closed")
                due_offset = 0 if (i < 100 and status == "active") else ((idx % 45) + 1)
                sub_mappings.append({
                    "subscription_number": f"SUB-BENCH-{idx:06d}",
                    "customer_id": cust_id,
                    "plan_id": plan.id,
                    "status": status,
                    "start_date": today - timedelta(days=idx % 365),
                    "current_period_start": today - timedelta(days=30),
                    "current_period_end": today + timedelta(days=due_offset),
                    "next_billing_date": today if (i < 100 and status == "active") else today + timedelta(days=due_offset),
                })
                if len(sub_mappings) >= 2000:
                    db.session.bulk_insert_mappings(Subscription, sub_mappings)
                    db.session.commit()
                    sub_mappings = []

            if sub_mappings:
                db.session.bulk_insert_mappings(Subscription, sub_mappings)
                db.session.commit()

        # 4. Invoices (Target: 10,000)
        current_invs = Invoice.query.count()
        needed_invs = max(0, 10000 - current_invs)
        if needed_invs > 0:
            print(f"  Bulk inserting {needed_invs} invoices...")
            statuses = ["paid", "confirmed", "paid", "draft", "cancelled"]
            inv_mappings = []
            for i in range(needed_invs):
                idx = current_invs + i + 1
                cust_id = all_cust_ids[i % len(all_cust_ids)]
                st = statuses[idx % len(statuses)]
                due_delta = (idx % 20) - 5
                sub_id = (i % 5000) + 1
                period_cycle = 3 + (i // 5000)
                p_start = today - timedelta(days=30 * period_cycle)
                p_end = today - timedelta(days=30 * (period_cycle - 1))
                inv_mappings.append({
                    "invoice_number": f"INV-BENCH-{idx:06d}",
                    "subscription_id": sub_id,
                    "customer_id": cust_id,
                    "status": st,
                    "issue_date": today - timedelta(days=15),
                    "due_date": today + timedelta(days=due_delta),
                    "billing_period_start": p_start,
                    "billing_period_end": p_end,
                    "subtotal": Decimal("150.00"),
                    "tax_amount": Decimal("15.00"),
                    "discount_amount": Decimal("0.00"),
                    "total": Decimal("165.00"),
                    "amount_paid": Decimal("165.00") if st == "paid" else Decimal("0.00"),
                })
                if len(inv_mappings) >= 2000:
                    db.session.bulk_insert_mappings(Invoice, inv_mappings)
                    db.session.commit()
                    inv_mappings = []

            if inv_mappings:
                db.session.bulk_insert_mappings(Invoice, inv_mappings)
                db.session.commit()

        # 5. Audit Logs (Target: 10,000)
        current_logs = AuditLog.query.count()
        needed_logs = max(0, 10000 - current_logs)
        if needed_logs > 0:
            print(f"  Bulk inserting {needed_logs} audit logs...")
            log_mappings = []
            for i in range(needed_logs):
                log_mappings.append({
                    "auth_id": admin.id,
                    "entity_type": "subscription" if i % 2 == 0 else "invoice",
                    "entity_id": (i % 5000) + 1,
                    "action": "benchmark_event",
                    "new_values": "{}",
                    "timestamp": datetime.now(timezone.utc),
                })
                if len(log_mappings) >= 2500:
                    db.session.bulk_insert_mappings(AuditLog, log_mappings)
                    db.session.commit()
                    log_mappings = []
            if log_mappings:
                db.session.bulk_insert_mappings(AuditLog, log_mappings)
                db.session.commit()

        # Print Dataset Metrics
        total_custs = Customer.query.count()
        total_subs = Subscription.query.count()
        active_subs = Subscription.query.filter_by(status="active").count()
        total_invs = Invoice.query.count()
        total_logs = AuditLog.query.count()

        print("-" * 70)
        print(f"Current Dataset Metrics:")
        print(f"  - Customers:            {total_custs:,}")
        print(f"  - Subscriptions:        {total_subs:,} ({active_subs:,} active)")
        print(f"  - Invoices:             {total_invs:,}")
        print(f"  - Audit Logs:           {total_logs:,}")
        print("-" * 70)

        # 2. Benchmark Queries / Endpoints
        print("Executing benchmark tests against target endpoints (< 2.0s spec):")
        client = app.test_client()
        token = create_access_token(
            identity=str(admin.id),
            additional_claims={"role": "admin", "email": admin.email},
        )
        headers = {"Authorization": f"Bearer {token}"}

        results = {}

        # a. GET /dashboard/summary (with filters)
        t0 = time.time()
        res_a = client.get("/api/v1/dashboard/summary?status=active", headers=headers)
        elapsed_a = time.time() - t0
        assert res_a.status_code == 200
        results["dashboard_summary"] = elapsed_a
        print(f"  a. GET /dashboard/summary (filtered):   {elapsed_a*1000:.2f} ms ({elapsed_a:.4f}s)")

        # b. GET /dashboard/overdue
        t0 = time.time()
        res_b = client.get("/api/v1/dashboard/overdue?page=1&per_page=20", headers=headers)
        elapsed_b = time.time() - t0
        assert res_b.status_code == 200
        results["dashboard_overdue"] = elapsed_b
        print(f"  b. GET /dashboard/overdue:             {elapsed_b*1000:.2f} ms ({elapsed_b:.4f}s)")

        # c. GET /invoices/outstanding
        t0 = time.time()
        res_c = client.get("/api/v1/invoices/outstanding?page=1&per_page=20", headers=headers)
        elapsed_c = time.time() - t0
        assert res_c.status_code == 200
        results["invoices_outstanding"] = elapsed_c
        print(f"  c. GET /invoices/outstanding:          {elapsed_c*1000:.2f} ms ({elapsed_c:.4f}s)")

        # d. GET /subscriptions (paginated)
        t0 = time.time()
        res_d = client.get("/api/v1/subscriptions?page=1&per_page=50", headers=headers)
        elapsed_d = time.time() - t0
        assert res_d.status_code == 200
        results["subscriptions_paginated"] = elapsed_d
        print(f"  d. GET /subscriptions (paginated 50):  {elapsed_d*1000:.2f} ms ({elapsed_d:.4f}s)")

        # e. Billing cycle tick (5,000 subscriptions, due subscriptions billed)
        t0 = time.time()
        billing_result = BillingService.generate_invoices_for_due_subscriptions(as_of_date=today)
        elapsed_e = time.time() - t0
        results["billing_cycle_tick"] = elapsed_e
        print(
            f"  e. Billing cycle tick:                 {elapsed_e*1000:.2f} ms ({elapsed_e:.4f}s) "
            f"[{billing_result['created_count']} generated, {billing_result['skipped_count']} skipped]"
        )

        print("=" * 70)
        all_passed = all(t < 2.0 for t in results.values())
        if all_passed:
            print("[SUCCESS] All endpoints responded in < 2.0s! Performance verification PASSED.")
        else:
            print("[FAILURE] One or more endpoints exceeded the 2.0s limit.")

        return results


if __name__ == "__main__":
    benchmark_results = run_benchmark()
    sys.exit(0 if all(t < 2.0 for t in benchmark_results.values()) else 1)
