#!/usr/bin/env bash
# ==============================================================================
# Script: backup.sh
# Description: Automated PostgreSQL daily backup with compression and retention
# Scope: D8 - Database Backups (Brightloop SMS)
# ==============================================================================

set -euo pipefail

# Configuration parameters (Override via environment variables if desired)
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGDATABASE="${PGDATABASE:-brightloop_sms}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${PGDATABASE}_backup_${TIMESTAMP}.dump"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

log() {
    local msg="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo "${msg}"
    echo "${msg}" >> "${LOG_FILE}"
}

log "Starting database backup for '${PGDATABASE}' on ${PGHOST}:${PGPORT}..."

# Execute pg_dump using custom format (-Fc: compressed, flexible, supports parallel restore)
if pg_dump -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -F c -b -v -f "${BACKUP_FILE}" "${PGDATABASE}" >> "${LOG_FILE}" 2>&1; then
    BACKUP_SIZE=$(ls -lh "${BACKUP_FILE}" | awk '{print $5}')
    log "Backup successful: ${BACKUP_FILE} (Size: ${BACKUP_SIZE})"
else
    log "ERROR: Database backup failed! Check log file: ${LOG_FILE}"
    exit 1
fi

# Retention enforcement: Remove backups older than RETENTION_DAYS
log "Enforcing retention policy (${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "${PGDATABASE}_backup_*.dump" -type f -mtime +"${RETENTION_DAYS}" -print -delete >> "${LOG_FILE}" 2>&1 || true
log "Retention purge complete."

exit 0
