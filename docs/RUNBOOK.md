# Brightloop SMS - Operational Runbook

This runbook covers operational routines, local task automation, database administration, and release publishing steps.

---

## 1. Local Service Management

### Quick Start (All Services)
* **Windows:**
  ```cmd
  setup.bat   :: Run once during initial setup
  start.bat   :: Launches Backend (5000), Worker, and Frontend (5173) in separate windows
  ```
* **Linux / macOS:**
  ```bash
  ./setup.sh  :: Initial provisioning
  ./start.sh  :: Launches concurrent local processes with graceful Ctrl+C shutdown
  ```

### Manual Individual Service Commands
If running services individually in separate terminals:

1. **Backend REST API:**
   ```bash
   # Windows
   .\venv\Scripts\python.exe backend\run.py
   # Linux / macOS
   ./venv/bin/python backend/run.py
   ```
2. **Background Worker (Billing & In-App Reminders):**
   ```bash
   # Continuous daemon running every 60 seconds
   python -m backend.app.worker --interval 60

   # Single one-shot tick (for cron integration or test verification)
   python -m backend.app.worker --once

   # Time-travel simulation (evaluate state as of a future date)
   python -m backend.app.worker --once --as-of 2026-12-01
   ```
3. **Frontend Dev Server:**
   ```bash
   npm --prefix frontend run dev
   ```

---

## 2. Database Backup & Disaster Recovery

### Creating a Snapshot Backup
* **Windows:**
  ```cmd
  backup.bat
  ```
  Copies `instance\subscription_system.db` to `backups\subscription_system_YYYYMMDD_HHMMSS.db`.
* **Linux / macOS:**
  ```bash
  ./backup.sh
  ```

### Restoring from a Snapshot
* **Windows:**
  ```cmd
  restore.bat backups\subscription_system_YYYYMMDD_HHMMSS.db
  ```
* **Linux / macOS:**
  ```bash
  ./restore.sh backups/subscription_system_YYYYMMDD_HHMMSS.db
  ```

---

## 3. Database Reset & Seeding

To clear all test transactions and restore clean baseline accounts:

```bash
# Windows
.\venv\Scripts\python.exe seed.py

# Linux / macOS
./venv/bin/python seed.py
```

To run the large-scale performance benchmark dataset (1,000 customers, 5,000 subscriptions, 10,000 invoices):

```bash
python seed_benchmark.py
```

---

## 4. Test Verification Routine

Execute all unit and integration test suites:

```bash
# Backend pytest suite (35 tests)
python -m pytest backend/tests/

# Frontend component & route guard test suite (18 tests)
npm --prefix frontend test -- --run

# Frontend TypeScript check and production bundle build
npm --prefix frontend run build
```

---

## 5. Publishing to Remote Repository (Manual Operator Step)

Per the **NO REMOTE PUSH** safety rule, all git commits, rebases, and release tags have been executed strictly on this local machine. No remote repository was contacted or altered.

When you are ready to publish these changes to your remote Git server (e.g., GitHub, GitLab):

```bash
# 1. Inspect local branch status and commit history
git status
git log --oneline -n 10

# 2. Verify git remote configuration
git remote -v

# 3. Push local main branch and the v1.0.0-rc1 release tag
git push origin main
git push origin v1.0.0-rc1

# 4. (Optional) If pushing the integration/cleanup tracking branch:
git push origin integration/cleanup
```
