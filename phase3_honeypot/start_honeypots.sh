#!/bin/bash
# HONEYPOT QUICK START SCRIPT FOR LINUX/MAC
# This script starts all honeypot components in the background

echo ""
echo "========================================================"
echo "  ChakraVyuh Phase 3 - Honeypot System Starter"
echo "========================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "Checking dependencies..."
pip3 install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Run: pip3 install -r requirements.txt"
    exit 1
fi

# Create logs directory
mkdir -p honeypot_logs

echo ""
echo "========================================================"
echo "  Starting Honeypot Services"
echo "========================================================"
echo ""

# Start SSH Honeypot
echo "[1/4] Starting SSH Honeypot (Port 2222)..."
python3 fake_ssh_honeypot.py > honeypot_logs/ssh.out 2>&1 &
SSH_PID=$!
echo "      PID: $SSH_PID"
sleep 2

# Start SQL Database Honeypot
echo "[2/4] Starting SQL Database Honeypot (Port 3307)..."
python3 fake_sql_honeypot.py > honeypot_logs/sql.out 2>&1 &
SQL_PID=$!
echo "      PID: $SQL_PID"
sleep 2

# Start Web Service Honeypot
echo "[3/4] Starting Web Service Honeypot (Port 8080)..."
python3 fake_web_honeypot.py > honeypot_logs/web.out 2>&1 &
WEB_PID=$!
echo "      PID: $WEB_PID"
sleep 2

# Start Honeypot Monitor
echo "[4/4] Starting Honeypot Monitor..."
python3 honeypot_monitor.py > honeypot_logs/monitor.out 2>&1 &
MONITOR_PID=$!
echo "      PID: $MONITOR_PID"
sleep 2

echo ""
echo "========================================================"
echo "  All Honeypot Services Started!"
echo "========================================================"
echo ""
echo "Services Running:"
echo "   [✓] SSH Honeypot   - ssh://localhost:2222 (PID: $SSH_PID)"
echo "   [✓] SQL Honeypot   - localhost:3307 (PID: $SQL_PID)"
echo "   [✓] Web Honeypot   - http://localhost:8080 (PID: $WEB_PID)"
echo "   [✓] Monitor        - Analyzing attacks (PID: $MONITOR_PID)"
echo ""
echo "Logs Location:"
echo "   honeypot_logs/"
echo ""
echo "Next Steps:"
echo "   1. In new terminal, run: python3 attack_test_toolkit.py"
echo "   2. Monitor will show detected attacks in real-time"
echo ""
echo "To stop all honeypots, run:"
echo "   kill $SSH_PID $SQL_PID $WEB_PID $MONITOR_PID"
echo ""

# Save PIDs to file for easy cleanup
echo "$SSH_PID" > honeypot_logs/.pids
echo "$SQL_PID" >> honeypot_logs/.pids
echo "$WEB_PID" >> honeypot_logs/.pids
echo "$MONITOR_PID" >> honeypot_logs/.pids

echo "Honeypots running in background. Press Ctrl+C to stop."
wait
