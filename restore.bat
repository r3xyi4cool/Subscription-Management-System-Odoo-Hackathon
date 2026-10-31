@echo off
setlocal

echo ========================================================
echo   Brightloop SMS - Database Restore Utility
echo ========================================================
echo.

set "BACKUP_TARGET=%~1"

if "%BACKUP_TARGET%"=="" (
    echo Available backups in .\backups:
    dir /b /o-d backups\*.db 2>nul
    echo.
    set /p "BACKUP_TARGET=Enter backup filename to restore (e.g. backups\subscription_system_xxxx.db): "
)

if "%BACKUP_TARGET%"=="" (
    echo [ERROR] No backup file specified.
    exit /b 1
)

if not exist "%BACKUP_TARGET%" (
    if exist "backups\%BACKUP_TARGET%" (
        set "BACKUP_TARGET=backups\%BACKUP_TARGET%"
    ) else (
        echo [ERROR] Backup file '%BACKUP_TARGET%' not found.
        exit /b 1
    )
)

if not exist "instance" mkdir instance

echo Restoring '%BACKUP_TARGET%' to 'instance\subscription_system.db'...
copy /y "%BACKUP_TARGET%" "instance\subscription_system.db" >nul
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Database restored successfully from: %BACKUP_TARGET%
) else (
    echo [ERROR] Database restore failed.
    exit /b 1
)
echo.
