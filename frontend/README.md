# Brightloop SMS - Subscription Management System Frontend

A complete, production-grade frontend for Brightloop Software's Subscription Management System (SMS), built with React 18, TypeScript, Vite, Tailwind CSS, and TanStack Query.

---

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Run development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Available Scripts

- `npm run dev`: Starts the Vite development server (port 5173)
- `npm run build`: Compiles TypeScript and builds production assets into `dist/`
- `npm run lint`: Performs type validation with `tsc --noEmit`
- `npm run test`: Executes the Vitest test suite

---

## Environment Variables

Configurable in `.env` (or `.env.example`):

```env
# Set to false to connect directly to the backend
VITE_USE_MOCK=false

# API Base URL (defaults to /api, which Vite proxies to http://localhost:5000)
VITE_API_BASE_URL=/api
```

---

## Project Structure

```
frontend/
  src/
    api/                 # REST API client, endpoint functions, types contract, TanStack hooks
    app/                 # Router, guards (RequireAuth, RequireRole), AuthContext
    components/          # DataTable (server-paginated), StatusBadge, MoneyText, ConfirmDialog,
                         # EmptyState, ErrorState, PageHeader, FormField, PasswordChecklist...
    features/
      auth/              # Login, Signup, Forgot/Reset Password
      staff/             # Staff team management (Admin)
      customers/         # Customer directory & customer detail
      catalogue/         # Products, Plans, Tax rules, Discount rules (Admin)
      quotations/        # Quotation templates & proposal management
      subscriptions/     # Lifecycle state machine & subscription detail
      invoices/          # Invoice details, outstanding ledger, PDF download
      billing/           # Automated billing run trigger & execution report
      payments/          # Payments ledger & inward recording
      refunds/           # Refund workflows & threshold approval
      dashboard/         # Executive telemetry, MRR, ARR, churn, collection rate charts
      portal/            # Customer self-service dashboard & guarded actions
      audit/             # Immutable audit log viewer (Admin)
    lib/                 # money.ts (paise math), dates.ts, permissions.ts, csv.ts
    main.tsx             # Application bootstrap & entry point
  docs/API_CONTRACT.md   # Exhaustive REST API contract for backend integration
  vite.config.ts         # Includes /api proxy to backend port 5000
```
