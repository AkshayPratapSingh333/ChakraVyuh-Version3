@echo off
REM HONEYPOT QUICK START SCRIPT FOR WINDOWS
REM This script starts all honeypot components simultaneously

setlocal enabledelayedexpansion

echo.
echo ========================================================
echo   ChakraVyuh Phase 3 - Honeypot System Starter
echo ========================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

echo Checking dependencies...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   Starting Honeypot Services
echo ========================================================
echo.

REM Create logs directory
if not exist honeypot_logs mkdir honeypot_logs

echo [1/4] Starting SSH Honeypot (Port 2222)...
start "SSH Honeypot" cmd /k "python fake_ssh_honeypot.py"
timeout /t 2 /nobreak

echo [2/4] Starting SQL Database Honeypot (Port 3307)...
start "SQL Honeypot" cmd /k "python fake_sql_honeypot.py"
timeout /t 2 /nobreak

echo [3/4] Starting Web Service Honeypot (Port 8080)...
start "Web Honeypot" cmd /k "python fake_web_honeypot.py"
timeout /t 2 /nobreak

echo [4/4] Starting Honeypot Monitor...
start "Honeypot Monitor" cmd /k "python honeypot_monitor.py"
timeout /t 2 /nobreak

echo.
echo ========================================================
echo   All Honeypot Services Started!
echo ========================================================
echo.
echo Services Running:
echo   [✓] SSH Honeypot   - ssh://localhost:2222
echo   [✓] SQL Honeypot   - localhost:3306
echo   [✓] Web Honeypot   - http://localhost:8080
echo   [✓] Monitor        - Analyzing attacks real-time
echo.
echo Logs Location:
echo   honeypot_logs/
echo.
echo Next Steps:
echo   1. Open new terminal
echo   2. Run: python attack_test_toolkit.py
echo   3. Monitor will show detected attacks
echo.
echo Press any key to close this window...
echo (Honeypot services will continue running in other windows)
pause
