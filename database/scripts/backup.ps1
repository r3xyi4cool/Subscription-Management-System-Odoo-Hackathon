# ==============================================================================
# Script: backup.ps1
# Description: Automated PostgreSQL daily backup with retention for Windows
# Scope: D8 - Database Backups (Brightloop SMS)
# ==============================================================================

param (
    [string]$PgHost = $env:PGHOST ?? "localhost",
    [string]$PgPort = $env:PGPORT ?? "5432",
    [string]$PgUser = $env:PGUSER ?? "postgres",
    [string]$PgDatabase = $env:PGDATABASE ?? "brightloop_sms",
    [string]$BackupDir = $env:BACKUP_DIR ?? "$PSScriptRoot\..\backups",
    [int]$RetentionDays = 14
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = Join-Path $BackupDir "${PgDatabase}_backup_${Timestamp}.dump"
$LogFile = Join-Path $BackupDir "backup.log"

function Log-Message([string]$Message) {
    $Line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $Line
    Add-Content -Path $LogFile -Value $Line
}

Log-Message "Starting database backup for '$PgDatabase' on ${PgHost}:${PgPort}..."

try {
    # Check if pg_dump is available
    $PgDumpCmd = Get-Command "pg_dump" -ErrorAction SilentlyContinue
    if (-not $PgDumpCmd) {
        throw "pg_dump executable not found in PATH. Please install PostgreSQL client tools or update PATH."
    }

    $DumpArgs = @(
        "-h", $PgHost,
        "-p", $PgPort,
        "-U", $PgUser,
        "-F", "c",
        "-b",
        "-v",
        "-f", $BackupFile,
        $PgDatabase
    )

    & pg_dump $DumpArgs 2>&1 | Out-File -FilePath $LogFile -Append

    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump exited with error code $LASTEXITCODE"
    }

    $FileInfo = Get-Item $BackupFile
    $FileSizeKb = [math]::Round($FileInfo.Length / 1KB, 2)
    Log-Message "Backup completed successfully: $BackupFile (${FileSizeKb} KB)"

    # Enforce retention policy
    Log-Message "Enforcing retention policy ($RetentionDays days)..."
    $CutoffDate = (Get-Date).AddDays(-$RetentionDays)
    Get-ChildItem -Path $BackupDir -Filter "${PgDatabase}_backup_*.dump" |
        Where-Object { $_.LastWriteTime -lt $CutoffDate } |
        ForEach-Object {
            Log-Message "Purging expired backup: $($_.Name)"
            Remove-Item $_.FullName -Force
        }

    Log-Message "Backup and retention completed successfully."
}
catch {
    Log-Message "ERROR: $($_.Exception.Message)"
    exit 1
}
