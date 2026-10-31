#!/usr/bin/env python3
"""
seed_benchmark.py - Seeds 5,000+ subscriptions and verifies dashboard responds in < 2 seconds.
"""

import time
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

# Add workspace to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Auto-fallback to virtualenv python if packages are in venv
venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
if os.path.exists(venv_python) and sys.executable != venv_python:
    try:
        import flask
    except ImportError:
        os.execv(venv_python, [venv_python] + sys.argv)

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.customer import Customer
from backend.app.models.catalog import Plan
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice, Payment


def run_benchmark():
    app = create_app()
    with app.app_context():
        db.create_all()

        print("Checking existing subscriptions count...")
        current_count = Subscription.query.count()
        needed = max(0, 5000 - current_count)

        if needed > 0:
            print(f"Bulk seeding {needed} subscriptions to reach 5,000+...")
            # Ensure base plan and customer exist
            plan = Plan.query.first()
            if not plan:
                plan = Plan(
                    name="Benchmark Plan",
                    billing_period="monthly",
                    min_quantity=1,
                    start_date=date(2026, 1, 1),
                    is_active=True,
                )
                db.session.add(plan)
                db.session.flush()

            cust = Customer.query.first()
            if not cust:
                auth = Auth(email="benchmark_cust@example.com", role="customer", is_active=True)
                auth.set_password("Cust@12345")
                db.session.add(auth)
                db.session.flush()
                cust = Customer(auth_id=auth.id, name="Benchmark Corp", email=auth.email)
                db.session.add(cust)
                db.session.flush()

            db.session.commit()

            plan_id = plan.id
            customer_id = cust.id
            today = date.today()

            batch_size = 1000
            for batch_start in range(0, needed, batch_size):
                batch_subs = []
                batch_invs = []
                batch_pays = []
                count = min(batch_size, needed - batch_start)

                for i in range(count):
                    idx = current_count + batch_start + i
                    status = "active" if (idx % 5 != 0) else "closed"
                    sub = {
                        "subscription_number": f"SUB-BENCH-{idx}",
                        "customer_id": customer_id,
                        "plan_id": plan_id,
                        "status": status,
                        "start_date": today - timedelta(days=idx % 300),
                        "current_period_start": today - timedelta(days=30),
                        "current_period_end": today,
                        "next_billing_date": today,
                    }
                    batch_subs.append(sub)

                db.session.bulk_insert_mappings(Subscription, batch_subs)
                db.session.commit()
                print(f"  Inserted {batch_start + count}/{needed} subscriptions...")

        total_subs = Subscription.query.count()
        print(f"\nDatabase now contains {total_subs} subscriptions.")

        # Benchmark dashboard query
        print("Executing aggregate dashboard query...")
        t0 = time.time()
        client = app.test_client()

        # Get or create admin token
        admin = Auth.query.filter_by(role="admin").first()
        from flask_jwt_extended import create_access_token

        token = create_access_token(
            identity=str(admin.id), additional_claims={"role": "admin", "email": admin.email}
        )

        res = client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        elapsed = time.time() - t0

        assert res.status_code == 200
        data = res.get_json()["data"]
        print(f"Dashboard Response: {data}")
        print(f"\nBenchmark Result: Query took {elapsed:.4f} seconds.")

        if elapsed < 2.0:
            print(f"[PASS] Dashboard responded in {elapsed:.4f}s (well under 2.0s limit).")
            return True
        else:
            print(f"[FAIL] Dashboard took {elapsed:.4f}s (exceeded 2.0s limit).")
            return False


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)

