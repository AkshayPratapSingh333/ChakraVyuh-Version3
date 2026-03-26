@echo off
REM ChakraVyuh Dashboard - Quick Start Script for Windows

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║   ⚔️  ChakraVyuh - Testing ^& SOC Dashboard Launcher            ║
echo ║   Network Anomaly Detection with Real-time Monitoring         ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js 14+
    pause
    exit /b 1
)

echo ✓ Python: 
python --version
echo ✓ Node.js: 
node --version
echo.

REM Setup Backend
echo ════════════════════════════════════════════════════════════════
echo STEP 1: Backend Setup
echo ════════════════════════════════════════════════════════════════

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -q -r requirements.txt

echo ✓ Backend ready
echo.

REM Setup Frontend
echo ════════════════════════════════════════════════════════════════
echo STEP 2: Frontend Setup
echo ════════════════════════════════════════════════════════════════

cd frontend_dashboard

if not exist "node_modules" (
    echo Installing Node dependencies...
    call npm install -q
)

echo ✓ Frontend ready
cd ..
echo.

REM Instructions
echo ════════════════════════════════════════════════════════════════
echo STEP 3: Start Services
echo ════════════════════════════════════════════════════════════════
echo.
echo Run these commands in separate terminals:
echo.
echo Terminal 1 - Backend API:
echo   cd backend_api
echo   python main.py
echo.
echo Terminal 2 - Frontend Dashboard:
echo   cd frontend_dashboard
echo   npm run dev
echo.
echo Then open: http://localhost:3000
echo.
echo ════════════════════════════════════════════════════════════════
echo API Documentation: http://localhost:8000/docs
echo ════════════════════════════════════════════════════════════════
echo.
echo ✓ Setup complete! Follow the commands above to start.
echo.
pause
