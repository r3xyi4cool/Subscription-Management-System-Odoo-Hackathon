# ==============================================================================
# Script: setup.ps1
# Description: One-command build script creating database, running migrations and seeds
# Scope: D7 - Repeatable Setup (Brightloop SMS)
# ==============================================================================

param (
    [string]$PgHost = $env:PGHOST ?? "localhost",
    [string]$PgPort = $env:PGPORT ?? "5432",
    [string]$PgUser = $env:PGUSER ?? "postgres",
    [string]$PgDatabase = $env:PGDATABASE ?? "brightloop_sms"
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================================="
Write-Host " Brightloop SMS: One-Command Database Provisioning"
Write-Host "=========================================================="
Write-Host "Target DB: $PgDatabase on ${PgHost}:${PgPort} (User: $PgUser)"
Write-Host "----------------------------------------------------------"

try {
    # Check if psql is present
    $PsqlCmd = Get-Command "psql" -ErrorAction SilentlyContinue
    if (-not $PsqlCmd) {
        throw "psql executable not found in PATH. Please install PostgreSQL client tools or update PATH."
    }

    # Verify if DB exists, create if not
    $DbCheck = & psql -h $PgHost -p $PgPort -U $PgUser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$PgDatabase'"
    if ($DbCheck -ne "1") {
        Write-Host "Creating database '$PgDatabase'..."
        & psql -h $PgHost -p $PgPort -U $PgUser -d postgres -c "CREATE DATABASE $PgDatabase;"
    } else {
        Write-Host "Database '$PgDatabase' already exists."
    }

    # Execute setup.sql
    $SetupSql = Join-Path $PSScriptRoot "setup.sql"
    Write-Host "Executing migrations and seed data from $SetupSql..."
    & psql -h $PgHost -p $PgPort -U $PgUser -d $PgDatabase -f $SetupSql

    Write-Host "=========================================================="
    Write-Host " PROVISIONING COMPLETE!"
    Write-Host "=========================================================="
}
catch {
    Write-Error "Provisioning failed: $($_.Exception.Message)"
    exit 1
}
