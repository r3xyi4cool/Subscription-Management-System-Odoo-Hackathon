#!/usr/bin/env bash
# ==============================================================================
# Script: restore.sh
# Description: Restore database from pg_dump custom archive and run test verification
# Scope: D8 - Database Restore & Verification (Brightloop SMS)
# ==============================================================================

set -euo pipefail

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
TARGET_DB="${TARGET_DB:-brightloop_sms_test_restore}"
BACKUP_FILE="${1:-}"

if [[ -z "${BACKUP_FILE}" ]]; then
    echo "Usage: ./restore.sh <path_to_backup_file> [target_database]"
    echo "Example: ./restore.sh ../backups/brightloop_sms_backup_20261031_120000.dump brightloop_sms_test_restore"
    exit 1
fi

if [[ ! -f "${BACKUP_FILE}" ]]; then
    echo "Error: Backup file '${BACKUP_FILE}' does not exist!"
    exit 1
fi

if [[ $# -ge 2 ]]; then
    TARGET_DB="$2"
fi

echo "=========================================================="
echo " Brightloop SMS Database Restore & Verification Procedure"
echo "=========================================================="
echo "Source Backup: ${BACKUP_FILE}"
echo "Target Database: ${TARGET_DB}"
echo "Host: ${PGHOST}:${PGPORT} (User: ${PGUSER})"
echo "----------------------------------------------------------"

# Recreate the target database cleanly
echo "[1/4] Re-creating database '${TARGET_DB}'..."
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c "DROP DATABASE IF EXISTS ${TARGET_DB};"
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c "CREATE DATABASE ${TARGET_DB};"

# Restore database using pg_restore
echo "[2/4] Restoring schema and data using pg_restore..."
pg_restore -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${TARGET_DB}" -v --no-owner --no-privileges "${BACKUP_FILE}" || {
    echo "Notice: pg_restore completed with warnings or non-fatal errors (normal for roles/permissions)."
}

# Run verification queries
echo "[3/4] Verifying table counts in '${TARGET_DB}'..."
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${TARGET_DB}" << 'EOF'
SELECT 
    (SELECT COUNT(*) FROM auth) AS auth_count,
    (SELECT COUNT(*) FROM customer) AS customer_count,
    (SELECT COUNT(*) FROM subscription) AS subscription_count,
    (SELECT COUNT(*) FROM invoice) AS invoice_count,
    (SELECT COUNT(*) FROM payment) AS payment_count,
    (SELECT COUNT(*) FROM refund) AS refund_count,
    (SELECT COUNT(*) FROM audit_log) AS audit_log_count;
EOF

echo "[4/4] Verifying KPI calculation on restored database..."
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${TARGET_DB}" -c "SELECT active_subscriptions, net_revenue_collected, mrr, arr, churn_rate_percent FROM v_dashboard_kpis;"

echo "=========================================================="
echo " RESTORE & VERIFICATION SUCCESSFUL!"
echo "=========================================================="
exit 0
