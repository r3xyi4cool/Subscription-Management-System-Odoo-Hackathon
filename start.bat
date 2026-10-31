@echo off
setlocal

echo ========================================================
echo   Brightloop SMS - Starting Services
echo ========================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run 'setup.bat' first.
    exit /b 1
)

echo [1/3] Starting Backend API on http://127.0.0.1:5000...
start "Brightloop SMS - Backend API (5000)" cmd /k "venv\Scripts\python.exe backend\run.py"

echo [2/3] Starting Background Worker (Billing & In-App Reminders)...
start "Brightloop SMS - Billing Worker" cmd /k "venv\Scripts\python.exe -m backend.app.worker --interval 60"

echo [3/3] Starting Frontend Dev Server on http://localhost:5173...
start "Brightloop SMS - Frontend (5173)" cmd /k "npm --prefix frontend run dev"

echo.
echo ========================================================
echo   All services have been launched in separate windows!
echo ========================================================
echo.
echo   Frontend:        http://localhost:5173
echo   Backend API:     http://localhost:5000/api/v1
echo.
echo   Default Credentials:
echo     Admin:    admin@brightloop.io / Admin@12345
echo     Staff:    staff@brightloop.io / Staff@12345
echo     Customer: customer@demo.com   / Demo@12345
echo.
echo Keep those terminal windows open while testing or interacting.
echo To stop services, simply close the respective command windows.
echo.
pause
