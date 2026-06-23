#!/bin/bash
# AutoDev Studio - Launcher
# Starts both backend and frontend for development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting AutoDev Studio..."
echo ""

# CRITICAL: Unset ELECTRON_RUN_AS_NODE if inherited from parent environment
# Otherwise Electron runs as plain Node.js instead of a desktop app
if [ -n "$ELECTRON_RUN_AS_NODE" ]; then
    echo "⚠️  Detected ELECTRON_RUN_AS_NODE, unsetting..."
    unset ELECTRON_RUN_AS_NODE
fi

# Start backend
echo "📡 Starting FastAPI backend..."
cd "$PROJECT_ROOT/backend"
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
python3 main.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "   Waiting for backend health check..."
for i in $(seq 1 30); do
    if curl -s http://localhost:5090/health > /dev/null 2>&1; then
        echo "   ✅ Backend is ready"
        break
    fi
    sleep 0.5
done

# Start frontend
echo ""
echo "🖥️  Starting Electron frontend..."
cd "$PROJECT_ROOT/client"
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "========================================"
echo "  AutoDev Studio is running!"
echo "========================================"
echo ""
echo "  Backend:  http://localhost:5090"
echo "  Frontend: http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop all services"

# Trap and cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping AutoDev Studio..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM
wait
