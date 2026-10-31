# ==============================================================================
# Script: restore.ps1
# Description: Restore database from pg_dump custom archive for Windows
# Scope: D8 - Database Restore & Verification (Brightloop SMS)
# ==============================================================================

param (
    [Parameter(Mandatory=$true, Position=0)]
    [string]$BackupFile,

    [Parameter(Position=1)]
    [string]$TargetDb = "brightloop_sms_test_restore",

    [string]$PgHost = $env:PGHOST ?? "localhost",
    [string]$PgPort = $env:PGPORT ?? "5432",
    [string]$PgUser = $env:PGUSER ?? "postgres"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found at: $BackupFile"
    exit 1
}

Write-Host "=========================================================="
Write-Host " Brightloop SMS Database Restore & Verification Procedure"
Write-Host "=========================================================="
Write-Host "Source Backup: $BackupFile"
Write-Host "Target DB:     $TargetDb"
Write-Host "Host:          ${PgHost}:${PgPort} (User: $PgUser)"
Write-Host "----------------------------------------------------------"

try {
    Write-Host "[1/4] Re-creating database '$TargetDb'..."
    & psql -h $PgHost -p $PgPort -U $PgUser -d postgres -c "DROP DATABASE IF EXISTS $TargetDb;" | Out-Null
    & psql -h $PgHost -p $PgPort -U $PgUser -d postgres -c "CREATE DATABASE $TargetDb;" | Out-Null

    Write-Host "[2/4] Restoring schema and data using pg_restore..."
    & pg_restore -h $PgHost -p $PgPort -U $PgUser -d $TargetDb -v --no-owner --no-privileges $BackupFile 2>&1 | Write-Verbose

    Write-Host "[3/4] Verifying table counts in '$TargetDb'..."
    $VerifyQuery = @"
SELECT 
    (SELECT COUNT(*) FROM auth) AS auth_count,
    (SELECT COUNT(*) FROM customer) AS customer_count,
    (SELECT COUNT(*) FROM subscription) AS subscription_count,
    (SELECT COUNT(*) FROM invoice) AS invoice_count,
    (SELECT COUNT(*) FROM payment) AS payment_count,
    (SELECT COUNT(*) FROM refund) AS refund_count,
    (SELECT COUNT(*) FROM audit_log) AS audit_log_count;
"@
    & psql -h $PgHost -p $PgPort -U $PgUser -d $TargetDb -c $VerifyQuery

    Write-Host "[4/4] Verifying KPI calculation on restored database..."
    & psql -h $PgHost -p $PgPort -U $PgUser -d $TargetDb -c "SELECT active_subscriptions, net_revenue_collected, mrr, arr, churn_rate_percent FROM v_dashboard_kpis;"

    Write-Host "=========================================================="
    Write-Host " RESTORE & VERIFICATION SUCCESSFUL!"
    Write-Host "=========================================================="
}
catch {
    Write-Error "Database restore failed: $($_.Exception.Message)"
    exit 1
}
