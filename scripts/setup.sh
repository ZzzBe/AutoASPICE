#!/bin/bash
# AutoDev Studio - Setup Script
# Initializes Python backend environment and installs dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "========================================"
echo "  AutoDev Studio - Environment Setup"
echo "========================================"
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
    echo "✅ Found Python: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON=python
    echo "✅ Found Python: $(python --version)"
else
    echo "❌ Python 3.10+ is required but not found."
    echo "   Install from: https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "   Python version: $PY_VER"

# Create virtual environment
VENV_DIR="$BACKEND_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "📦 Creating Python virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    echo "✅ Virtual environment created at $VENV_DIR"
else
    echo "✅ Virtual environment already exists"
fi

# Activate and install
source "$VENV_DIR/bin/activate"

echo ""
echo "📥 Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r "$BACKEND_DIR/requirements.txt" -q

echo "✅ Python dependencies installed"
echo ""

# Build manifests
echo "📊 Building agent manifests..."
cd "$PROJECT_ROOT/manifest"
$PYTHON build_manifest.py
echo "✅ Manifests built"

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "To start AutoDev Studio:"
echo "  1. Start backend:  cd backend && python main.py"
echo "  2. Start frontend: cd client && npm run dev"
echo ""
echo "Or use the launcher: ./scripts/launch.sh"
