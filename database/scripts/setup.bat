@echo off
REM ==============================================================================
REM Script: setup.bat
REM Description: Windows CMD one-command database provisioning
REM Scope: D7 - Repeatable Setup (Brightloop SMS)
REM ==============================================================================

set PGHOST=%PGHOST%
if "%PGHOST%"=="" set PGHOST=localhost
set PGPORT=%PGPORT%
if "%PGPORT%"=="" set PGPORT=5432
set PGUSER=%PGUSER%
if "%PGUSER%"=="" set PGUSER=postgres
set PGDATABASE=%PGDATABASE%
if "%PGDATABASE%"=="" set PGDATABASE=brightloop_sms

echo ==========================================================
echo  Brightloop SMS: Windows Database Provisioning
echo ==========================================================
echo Target DB: %PGDATABASE% on %PGHOST%:%PGPORT%
echo ----------------------------------------------------------

psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d postgres -c "SELECT 1 FROM pg_database WHERE datname='%PGDATABASE%';" | findstr "1" >nul
if errorlevel 1 (
    echo Creating database %PGDATABASE%...
    psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d postgres -c "CREATE DATABASE %PGDATABASE%;"
)

echo Executing migrations and seed data...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -f "%~dp0setup.sql"

if errorlevel 1 (
    echo [ERROR] Provisioning failed!
    exit /b 1
)

echo ==========================================================
echo  PROVISIONING COMPLETE!
echo ==========================================================
exit /b 0
