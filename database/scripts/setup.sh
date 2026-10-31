#!/usr/bin/env bash
# ==============================================================================
# Script: setup.sh
# Description: One-command build script creating database, running migrations and seeds
# Scope: D7 - Repeatable Setup (Brightloop SMS)
# ==============================================================================

set -euo pipefail

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGDATABASE="${PGDATABASE:-brightloop_sms}"

echo "=========================================================="
echo " Brightloop SMS: One-Command Database Provisioning"
echo "=========================================================="
echo "Target DB: ${PGDATABASE} on ${PGHOST}:${PGPORT} (User: ${PGUSER})"
echo "----------------------------------------------------------"

# Check if database exists, create if not
if ! psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -lqt | cut -d \| -f 1 | grep -qw "${PGDATABASE}"; then
    echo "Creating database '${PGDATABASE}'..."
    psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c "CREATE DATABASE ${PGDATABASE};"
else
    echo "Database '${PGDATABASE}' already exists."
fi

# Run setup script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -f "${SCRIPT_DIR}/setup.sql"

echo "=========================================================="
echo " PROVISIONING COMPLETE!"
echo "=========================================================="
exit 0
