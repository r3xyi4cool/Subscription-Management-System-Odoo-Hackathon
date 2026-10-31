@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   Brightloop SMS - Local Environment Setup
echo ========================================================
echo.

:: 1. Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    py --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python is not installed or not in PATH.
        echo Please install Python 3.10 or higher from https://python.org
        exit /b 1
    )
    set "PY_CMD=py"
) else (
    set "PY_CMD=python"
)

for /f "tokens=2 delims= " %%v in ('%PY_CMD% --version 2^>^&1') do set "PY_VER=%%v"
echo       Found Python %PY_VER%

:: 2. Check Node.js and npm
echo [2/6] Checking Node.js and npm...
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js 18 or higher from https://nodejs.org
    exit /b 1
)
for /f "delims=" %%v in ('node --version') do set "NODE_VER=%%v"
echo       Found Node.js %NODE_VER%

:: 3. Setup Python Virtual Environment
echo [3/6] Setting up Python virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo       Creating virtualenv in .\venv...
    %PY_CMD% -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)
echo       Installing backend dependencies...
venv\Scripts\python.exe -m pip install --quiet --upgrade pip
venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install backend dependencies.
    exit /b 1
)

:: 4. Environment Configuration
echo [4/6] Setting up environment configuration...
if not exist ".env" (
    echo       Copying .env.example to .env...
    copy .env.example .env >nul
)
if not exist "backend\.env" (
    echo       Copying .env.example to backend\.env...
    copy .env.example backend\.env >nul
)

:: 5. Database Migrations and Seeding
echo [5/6] Initializing local database and running migrations...
if not exist "instance" mkdir instance
set "FLASK_APP=backend.run:app"
venv\Scripts\python.exe -m flask --app backend.run:app db upgrade
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Flask db upgrade encountered an issue, proceeding to run seed...
)
echo       Seeding initial data (plans, products, admin, staff, demo customer)...
venv\Scripts\python.exe seed.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Database seeding failed.
    exit /b 1
)

:: 6. Frontend Setup and Build
echo [6/6] Installing frontend packages and building assets...
call npm --prefix frontend install --silent
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm install failed.
    exit /b 1
)
echo       Building production frontend bundle...
call npm --prefix frontend run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Frontend build failed.
    exit /b 1
)

echo.
echo ========================================================
echo   Brightloop SMS is ready!
echo ========================================================
echo.
echo Quick Start:
echo   Run 'start.bat' to launch the backend, worker, and frontend.
echo.
echo Default Credentials:
echo   Admin:    admin@brightloop.io   / Admin@12345
echo   Staff:    staff@brightloop.io   / Staff@12345
echo   Customer: customer@demo.com     / Demo@12345
echo.
