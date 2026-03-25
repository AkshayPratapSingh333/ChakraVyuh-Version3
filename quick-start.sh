#!/bin/bash
# ChakraVyuh Dashboard - Quick Start Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   ⚔️  ChakraVyuh - Testing & SOC Dashboard Launcher            ║"
echo "║   Network Anomaly Detection with Real-time Monitoring         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 14+"
    exit 1
fi

echo "✓ Python: $(python --version)"
echo "✓ Node.js: $(node --version)"
echo ""

# Setup Backend
echo "════════════════════════════════════════════════════════════════"
echo "STEP 1: Backend Setup"
echo "════════════════════════════════════════════════════════════════"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

echo "Activating virtual environment..."
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo "✓ Backend ready"
echo ""

# Setup Frontend
echo "════════════════════════════════════════════════════════════════"
echo "STEP 2: Frontend Setup"
echo "════════════════════════════════════════════════════════════════"

cd frontend_dashboard

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install -q
fi

echo "✓ Frontend ready"
cd ..
echo ""

# Instructions
echo "════════════════════════════════════════════════════════════════"
echo "STEP 3: Start Services"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Run these commands in separate terminals:"
echo ""
echo "Terminal 1 - Backend API:"
echo "  cd backend_api"
echo "  python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Terminal 2 - Frontend Dashboard:"
echo "  cd frontend_dashboard"
echo "  npm start"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "API Documentation: http://localhost:8000/docs"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✓ Setup complete! Follow the commands above to start."
