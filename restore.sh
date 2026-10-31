#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  Brightloop SMS - Database Restore Utility"
echo "========================================================"
echo ""

BACKUP_TARGET="$1"

if [ -z "$BACKUP_TARGET" ]; then
    echo "Available backups in ./backups:"
    ls -lt backups/*.db 2>/dev/null || true
    echo ""
    read -rp "Enter backup filename to restore: " BACKUP_TARGET
fi

if [ -z "$BACKUP_TARGET" ]; then
    echo "[ERROR] No backup file specified."
    exit 1
fi

if [ ! -f "$BACKUP_TARGET" ]; then
    if [ -f "backups/$BACKUP_TARGET" ]; then
        BACKUP_TARGET="backups/$BACKUP_TARGET"
    else
        echo "[ERROR] Backup file '$BACKUP_TARGET' not found."
        exit 1
    fi
fi

mkdir -p instance
echo "Restoring '$BACKUP_TARGET' to 'instance/subscription_system.db'..."
cp -f "$BACKUP_TARGET" "instance/subscription_system.db"
echo "[SUCCESS] Database restored successfully from: $BACKUP_TARGET"
echo ""

