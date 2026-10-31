#!/usr/bin/env bash

echo "========================================================"
echo "  Brightloop SMS - Starting Services"
echo "========================================================"
echo ""

if [ ! -f "venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Please run './setup.sh' first."
    exit 1
fi

cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo "[1/3] Starting Backend API on http://127.0.0.1:5000..."
./venv/bin/python backend/run.py &
BACKEND_PID=$!

echo "[2/3] Starting Background Worker..."
./venv/bin/python -m backend.app.worker --interval 60 &
WORKER_PID=$!

echo "[3/3] Starting Frontend Dev Server on http://localhost:5173..."
npm --prefix frontend run dev &
FRONTEND_PID=$!

echo ""
echo "========================================================"
echo "  All services are running! Press Ctrl+C to stop all."
echo "========================================================"
echo ""
echo "  Frontend:    http://localhost:5173"
echo "  Backend API: http://localhost:5000/api/v1"
echo ""
echo "  Default Credentials:"
echo "    Admin:    admin@brightloop.io / Admin@12345"
echo "    Staff:    staff@brightloop.io / Staff@12345"
echo "    Customer: customer@demo.com   / Demo@12345"
echo ""

wait

