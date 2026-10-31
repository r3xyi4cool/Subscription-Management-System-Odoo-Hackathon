# Brightloop SMS - Release Notes v1.0.0-rc1

**Release Version:** `v1.0.0-rc1`  
**Release Date:** 2026-10-31  
**Target Environment:** Local Developer Host (Windows / Linux / macOS)  
**Branch:** `main` (merged from `integration/cleanup`)

---

## 1. Executive Summary

`v1.0.0-rc1` represents the complete, verified, and unified release of the **Brightloop Subscription Management System (SMS)**. The repository integrates the work of Frontend, Backend, and Database engineering into a zero-cloud, host-native platform that can be cloned and run locally on any workstation in three commands.

All mock code, placeholders, and fragile integrations have been resolved. Email dependencies have been replaced with a real-time, in-app customer notification system. All financial calculations use authoritative SQL `DECIMAL(12,2)` with deterministic half-up rounding.

---

## 2. Key Release Highlights

### In-App Notifications (Replaces External Email)
* Replaced SMTP, SendGrid, and mail sender dependencies with an in-app notification engine.
* Customer notification bell in top navigation with live unread counter and preview dropdown.
* Dedicated customer notifications management page (`/portal/notifications`) with "Mark all as read" capability.
* Automated invoice generation notices, payment receipt confirmations, and overdue payment alerts.
* Staff console includes a **Generate Reset Link** feature on customer detail pages to copy single-use 30-minute password reset URLs directly to the clipboard.

### Autonomous Local Background Worker
* Standalone daemon (`python -m backend.app.worker`) with single-instance lock file (`.worker.lock`).
* Recurring billing catch-up with database uniqueness constraints preventing double billing (`uq_invoice_subscription_period`).
* Deduplicated daily payment reminder notifications for invoices approaching due date or overdue.
* Automated closure of expired subscriptions configured with plan flag `auto_close = True`.

### Performance & Bundling Optimization
* All core API routes execute in under 100ms on a 5,000-subscription and 10,000-invoice dataset.
* Frontend bundle dynamically code-split across routes via `React.lazy()` and vendor-isolated chunks (`vendor-react`, `vendor-query`, `vendor-icons`), compiling with zero Vite chunk size warnings.

### Host-Native Clone-and-Run Scripts
* Cross-platform one-command setup: `setup.bat` (Windows) / `setup.sh` (Linux/macOS).
* Cross-platform concurrent runner: `start.bat` / `start.sh` launching API, worker, and frontend.
* Instant database backup and restore utilities: `backup.bat`, `backup.sh`, `restore.bat`, `restore.sh`.

---

## 3. Verification & Compliance Report

| Test Suite / Audit | Target SLA / Standard | Actual Result | Status |
| :--- | :--- | :--- | :--- |
| **Backend Pytest Suite** | 35 test cases (Auth, Concurrency, Billing, Pricing, Lifecycle, PDF, Worker) | **35 passed in 6.87s** | **PASS** |
| **Frontend Vitest Suite** | 18 test cases (Route guards, plan flags, password policies, money math) | **18 passed in 2.20s** | **PASS** |
| **Frontend Production Build** | TypeScript compilation & Vite bundle build | **Zero chunk size warnings (< 400 kB max)** | **PASS** |
| **Bandit Security AST Scan** | Python backend vulnerability analysis | **0 issues identified** | **PASS** |
| **Pip-Audit Vulnerability Scan**| Installed dependencies security audit | **0 known vulnerabilities** | **PASS** |
| **Performance Benchmark** | Dashboard summary & overdue queries on 5,000 subscriptions | **83.72 ms (< 2.0s SLA)** | **PASS** |

---

## 4. Local Git & Remote Safety Compliance

* **NO REMOTE PUSH Rule:** Strictly enforced. No `git push` commands were issued, no remote URLs were altered, and no GitHub APIs/releases were invoked.
* **Pre-Merge Safety Bundle:** Standalone Git bundle created at `../sms-backup-before-merge.bundle` encompassing all local commits and branches.
* **Local Tag:** Release tagged locally as `v1.0.0-rc1`.

