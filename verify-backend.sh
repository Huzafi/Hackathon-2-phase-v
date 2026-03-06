#!/bin/bash

# Backend Verification Script
# This script checks if the backend is properly configured and ready to run

echo "=================================="
echo "Backend Setup Verification"
echo "=================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

# Check Python
echo "1. Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ Python found: $PYTHON_VERSION"
else
    echo "   ❌ Python 3 not found"
    exit 1
fi

# Check virtual environment
echo ""
echo "2. Checking virtual environment..."
if [ -d ".venv" ]; then
    echo "   ✅ Virtual environment exists"

    # Activate it for remaining checks
    source .venv/bin/activate
else
    echo "   ⚠️  Virtual environment not found, creating..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "   ✅ Virtual environment created"
fi

# Check dependencies
echo ""
echo "3. Checking required packages..."

PACKAGES=("fastapi" "sqlmodel" "uvicorn" "psycopg2" "python_jose" "passlib" "aiokafka" "openai" "dapr")
MISSING=0

for pkg in "${PACKAGES[@]}"; do
    if python -c "import ${pkg}" 2>/dev/null; then
        echo "   ✅ $pkg installed"
    else
        echo "   ❌ $pkg missing"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "⚠️  Installing missing packages..."
    pip install -r requirements.txt -q
    echo "   ✅ Packages installed"
fi

# Check .env file
echo ""
echo "4. Checking .env configuration..."
if [ -f ".env" ]; then
    echo "   ✅ .env file found"

    # Check for required keys
    if grep -q "DATABASE_URL" .env; then
        echo "   ✅ DATABASE_URL configured"
    else
        echo "   ❌ DATABASE_URL missing from .env"
    fi

    if grep -q "JWT_SECRET" .env; then
        echo "   ✅ JWT_SECRET configured"
    else
        echo "   ❌ JWT_SECRET missing from .env"
    fi
else
    echo "   ⚠️  .env file not found, using .env.example"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✅ Created .env from template"
    fi
fi

# Check source code
echo ""
echo "5. Checking source code..."
if [ -f "src/main.py" ]; then
    echo "   ✅ src/main.py found"
else
    echo "   ❌ src/main.py not found"
    exit 1
fi

# Summary
echo ""
echo "=================================="
echo "✅ Verification Complete!"
echo "=================================="
echo ""
echo "To start the backend, run:"
echo "  cd backend"
echo "  source .venv/bin/activate"
echo "  python -m uvicorn src.main:app --reload --port 8000"
echo ""
