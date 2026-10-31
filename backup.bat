@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   Brightloop SMS - Database Backup Utility
echo ========================================================
echo.

if not exist "backups" mkdir backups

:: Format date/time string YYYYMMDD_HHMMSS
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set "DT=%%I"
if "%DT%"=="" (
    set "TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
    set "TIMESTAMP=!TIMESTAMP: =0!"
) else (
    set "TIMESTAMP=%DT:~0,8%_%DT:~8,6%"
)

set "SOURCE_DB=instance\subscription_system.db"
set "BACKUP_FILE=backups\subscription_system_%TIMESTAMP%.db"

if exist "%SOURCE_DB%" (
    echo [INFO] Backing up SQLite database...
    copy "%SOURCE_DB%" "%BACKUP_FILE%" >nul
    if %ERRORLEVEL% equ 0 (
        echo [SUCCESS] Database backed up to: %BACKUP_FILE%
        for %%F in ("%BACKUP_FILE%") do echo [SIZE] %%~zF bytes
    ) else (
        echo [ERROR] Backup failed.
        exit /b 1
    )
) else (
    echo [WARNING] Default SQLite database '%SOURCE_DB%' not found.
    echo If using PostgreSQL, run 'pg_dump' or check your DATABASE_URL.
    exit /b 1
)

echo.
