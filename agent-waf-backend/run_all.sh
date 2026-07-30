#!/bin/bash

echo "========================================="
echo " Starting Agent WAF & React Frontend"
echo "========================================="

# Start the FastAPI Backend
echo "[1/2] Starting WAF Proxy Backend (Port 8000)..."
# Setup Python environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment with uv..."
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    source .venv/bin/activate
fi

uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 2

# Start the React Frontend
echo "[2/2] Starting React Frontend..."
cd ../agent-waf-frontend || { echo "Frontend directory not found!"; exit 1; }

# Install dependencies if node_modules is missing
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

echo "========================================="
echo " Both services are running!"
echo " Backend:  http://127.0.0.1:8000"
echo " Frontend: check Vite output for the URL (usually http://localhost:5173)"
echo " Press Ctrl+C to stop both."
echo "========================================="

# Trap Ctrl+C to kill both background processes
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" EXIT

# Wait indefinitely
wait
