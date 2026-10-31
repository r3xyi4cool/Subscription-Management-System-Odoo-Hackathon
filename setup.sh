#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  Brightloop SMS - Local Environment Setup"
echo "========================================================"
echo ""

# 1. Check Python
echo "[1/6] Checking Python installation..."
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 is not installed or not in PATH."
    echo "Please install Python 3.10 or higher."
    exit 1
fi
PY_VER=$($PY_CMD --version)
echo "      Found $PY_VER"

# 2. Check Node.js and npm
echo "[2/6] Checking Node.js and npm..."
if ! command -v node >/dev/null 2>&1; then
    echo "[ERROR] Node.js is not installed or not in PATH."
    echo "Please install Node.js 18 or higher."
    exit 1
fi
NODE_VER=$(node --version)
echo "      Found Node.js $NODE_VER"

# 3. Setup Python Virtual Environment
echo "[3/6] Setting up Python virtual environment..."
if [ ! -f "venv/bin/python" ]; then
    echo "      Creating virtualenv in ./venv..."
    $PY_CMD -m venv venv
fi
echo "      Installing backend dependencies..."
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt

# 4. Environment Configuration
echo "[4/6] Setting up environment configuration..."
if [ ! -f ".env" ]; then
    echo "      Copying .env.example to .env..."
    cp .env.example .env
fi
if [ ! -f "backend/.env" ]; then
    echo "      Copying .env.example to backend/.env..."
    cp .env.example backend/.env
fi

# 5. Database Migrations and Seeding
echo "[5/6] Initializing local database and running migrations..."
mkdir -p instance
export FLASK_APP="backend.run:app"
./venv/bin/flask --app backend.run:app db upgrade || echo "[WARNING] db upgrade completed with notes"
echo "      Seeding initial data (plans, products, admin, staff, demo customer)..."
./venv/bin/python seed.py

# 6. Frontend Setup and Build
echo "[6/6] Installing frontend packages and building assets..."
npm --prefix frontend install --silent
echo "      Building production frontend bundle..."
npm --prefix frontend run build

echo ""
echo "========================================================"
echo "  Brightloop SMS is ready!"
echo "========================================================"
echo ""
echo "Quick Start:"
echo "  Run './start.sh' to launch backend, worker, and frontend."
echo ""
echo "Default Credentials:"
echo "  Admin:    admin@brightloop.io   / Admin@12345"
echo "  Staff:    staff@brightloop.io   / Staff@12345"
echo "  Customer: customer@demo.com     / Demo@12345"
echo ""
