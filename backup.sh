#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  Brightloop SMS - Database Backup Utility"
echo "========================================================"
echo ""

mkdir -p backups
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SOURCE_DB="instance/subscription_system.db"
BACKUP_FILE="backups/subscription_system_${TIMESTAMP}.db"

if [ -f "$SOURCE_DB" ]; then
    echo "[INFO] Backing up SQLite database..."
    cp "$SOURCE_DB" "$BACKUP_FILE"
    echo "[SUCCESS] Database backed up to: $BACKUP_FILE"
    ls -lh "$BACKUP_FILE"
else
    echo "[WARNING] SQLite database '$SOURCE_DB' not found."
    echo "If using PostgreSQL, run pg_dump or check your DATABASE_URL."
    exit 1
fi
echo ""
