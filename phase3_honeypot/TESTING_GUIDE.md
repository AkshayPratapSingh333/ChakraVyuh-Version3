# STEP-BY-STEP HONEYPOT TESTING GUIDE

## Complete Testing Walkthrough for Beginners & Advanced Users

---

## PART 1: INITIAL SETUP (15 minutes)

### Step 1.1: Navigate to honeypot directory
```bash
cd d:\ComputerScienceProject\ChakraVyuh-Version3\phase3_honeypot
```

### Step 1.2: Check Python installation
```bash
python --version
# Expected: Python 3.8 or higher
# If not installed, download from https://www.python.org/downloads/
```

### Step 1.3: Install dependencies
```bash
pip install -r requirements.txt
# Expected output:
# Successfully installed flask-3.0.0 requests-2.31.0
```

### Step 1.4: Verify log directory
```bash
# Linux/Mac
mkdir -p honeypot_logs
ls -la honeypot_logs/

# Windows
mkdir honeypot_logs
dir honeypot_logs
```

---

## PART 2: LAUNCH HONEYPOTS (5 minutes)

### Option A: Automatic Launch (Recommended)

**Windows:**
```bash
start_honeypots.bat
# This opens 4 new command windows with all services
```

**Linux/Mac:**
```bash
chmod +x start_honeypots.sh
./start_honeypots.sh
# This runs all services in background
```

### Option B: Manual Launch (Educational)

Open **4 separate terminals** and run:

**Terminal 1 - SSH:**
```bash
python fake_ssh_honeypot.py
# Expected:
# [time] - INFO - SSH Honeypot listening on localhost:2222
# ✓ SSH Honeypot started on localhost:2222
```

**Terminal 2 - SQL:**
```bash
python fake_sql_honeypot.py
# Expected:
# [time] - INFO - SQL Honeypot listening on localhost:3307
# ✓ SQL Honeypot started on localhost:3307
```

**Terminal 3 - Web:**
```bash
python fake_web_honeypot.py
# Expected:
# ✓ Web Honeypot starting on 0.0.0.0:8080
# * Running on http://127.0.0.1:8080
```

**Terminal 4 - Monitor:**
```bash
python honeypot_monitor.py
# Expected:
# ============================================================
# HONEYPOT MONITOR - Real-time Attack Analysis
# ============================================================
# (Waiting for attacks...)
```

---

## PART 3: ATTACKER PERSPECTIVE - MANUAL TESTING

### Attack Type 1: SSH Connection Attempts

**Scenario:** You're an attacker trying to brute-force SSH

**Commands to try (New Terminal 5):**

```bash
# Attempt 1: Basic connection
telnet localhost 2222

# Expected honeypot output:
# [ALERT] Connection from 127.0.0.1
# Sent SSH banner to 127.0.0.1

# Attempt 2: Using netcat (if installed)
echo "root:password" | nc localhost 2222

# Attempt 3: Using PowerShell (Windows)
$socket = New-Object System.Net.Sockets.TcpClient
$socket.Connect('localhost', 2222)
$stream = $socket.GetStream()
$reader = New-Object System.IO.StreamReader($stream)
$banner = $reader.ReadLine()
Write-Host "Got: $banner"
$socket.Close()
```

**What the honeypot logs:**
```json
{
  "type": "SSH_AUTH_ATTACK",
  "source_ip": "127.0.0.1",
  "description": "Attempting root access",
  "timestamp": "2024-01-15T14:30:45.123456"
}
```

**Monitor detects:**
```
[ALERT] SSH_AUTH_ATTACK from 127.0.0.1
```

---

### Attack Type 2: SQL Injection Attempts

**Scenario:** You're trying to steal data from database

**Commands to try:**

```bash
# Attempt 1: Direct injection
echo "1' OR '1'='1" | nc localhost 3307

# Attempt 2: Using Python
python -c "
import socket
s = socket.socket()
s.connect(('localhost', 3307))
s.send(b\"1' OR '1'='1\")
s.close()
"

# Attempt 3: UNION-based injection
echo "' UNION SELECT * FROM users --" | nc localhost 3307

# Attempt 4: DROP command
echo "; DROP TABLE users; --" | nc localhost 3307
```

**What the honeypot logs:**
```json
{
  "type": "SQL_INJECTION",
  "source_ip": "127.0.0.1",
  "pattern_matched": "(\bUNION\b.*\bSELECT\b)",
  "query_sample": "' UNION SELECT * FROM users --",
  "severity": "HIGH",
  "timestamp": "2024-01-15T14:31:15.123456"
}
```

**Monitor detects:**
```
[ALERT] SQL_INJECTION_ATTEMPT from 127.0.0.1 (Confidence: 0.98)
Alert Type: CRITICAL - Database at risk
```

---

### Attack Type 3: Web Application Attacks

**Scenario:** You're exploiting a vulnerable web app

**XSS (Cross-Site Scripting):**
```bash
# Using curl
curl "http://localhost:8080/search?q=<script>alert('XSS')</script>"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8080/search?q=<script>alert('XSS')</script>"

# Payload variations to try:
# <img src=x onerror='alert(1)'>
# <svg/onload=alert('XSS')>
# javascript:alert('XSS')
# <iframe src='javascript:alert(1)'></iframe>
```

**SQL Injection via Web:**
```bash
curl -X POST "http://localhost:8080/api/users" \
  -d "username=admin' --&password=anything"

curl "http://localhost:8080/login?user=admin'%20--&pass=x"
```

**Command Injection:**
```bash
curl "http://localhost:8080/execute?cmd=;ls%20-la"
curl "http://localhost:8080/ping?host=127.0.0.1;whoami"

# Variations:
# ;id;
# &&whoami&&
# |cat /etc/passwd|
# $(whoami)
```

**Path Traversal:**
```bash
curl "http://localhost:8080/file?path=../../etc/passwd"
curl "http://localhost:8080/download?file=..\\..\\windows\\system32\\config\\sam"
```

**What the honeypot logs:**
```json
{
  "type": "XSS",
  "source_ip": "127.0.0.1",
  "method": "GET",
  "path": "/search",
  "payload_sample": "<script>alert('XSS')</script>",
  "severity": "HIGH",
  "timestamp": "2024-01-15T14:32:00.123456"
}
```

---

## PART 4: AUTOMATED ATTACK TESTING

### Run Full Test Suite

```bash
# Open new Terminal 5
python attack_test_toolkit.py
```

**Expected Output:**
```
======================================================================
HONEYPOT ATTACK TEST SUITE - Testing Detection Capabilities
======================================================================

[14:33:15] [INFO] TEST 1: Single SSH Login Attempt
[14:33:15] [INFO]   ✓ Received banner: SSH-2.0-OpenSSH_7.4
[14:33:15] [INFO]   ✓ Test completed

[14:33:17] [INFO] TEST 2: SSH Brute Force Attack (10 attempts)
[14:33:17] [INFO]   Attempt 1: root/root
[14:33:17] [INFO]   Attempt 2: root/123456
...
[14:33:20] [INFO]   ✓ Brute force test completed

[14:33:22] [INFO] TEST 3: SQL Database Connection Attempt
[14:33:22] [INFO]   ✓ Connected to database on localhost:3307
[14:33:22] [INFO]   ✓ Received greeting packet
[14:33:22] [INFO]   ✓ Test completed

[14:33:24] [INFO] TEST 4: SQL Injection Attacks
[14:33:24] [INFO]   Payload 1: 1' OR '1'='1
[14:33:24] [INFO]   Payload 2: 1; DROP TABLE users; --
...
[14:33:27] [INFO]   ✓ SQL Injection tests completed

[14:33:29] [INFO] TEST 5: Basic HTTP Request
[14:33:29] [INFO]   ✓ Status Code: 200
[14:33:29] [INFO]   ✓ Response Length: 284 bytes

[14:33:31] [INFO] TEST 6: XSS (Cross-Site Scripting) Attacks
[14:33:31] [INFO]   Payload 1: <script>alert('XSS')</script> [200]
...
[14:33:35] [INFO]   ✓ XSS tests completed

... (Tests 7-10) ...

======================================================================
TEST EXECUTION SUMMARY
======================================================================

Total Tests: 10
Executed: 10
Failed: 0

Detailed Results:
  ✓ SSH Single Login
  ✓ SSH Brute Force
  ✓ SQL Connection
  ✓ SQL Injection
  ✓ Web Basic Request
  ✓ XSS Attacks
  ✓ Web SQL Injection
  ✓ Command Injection
  ✓ Path Traversal
  ✓ Multi-Vector Campaign

======================================================================
Check honeypot_logs/*.json files for captured attack details
======================================================================
```

---

## PART 5: MONITORING & ANALYSIS

### Watch Attacks in Real-time

**Monitor Terminal Output:**
The monitor displays summary every 30 seconds:
```
[14:34:15] Attack Summary:
  Total Attacks: 45
  Unique Attackers: 1
  New Alerts: 3

  Top Attackers:
    - 127.0.0.1: 45 attacks
```

### Check JSON Logs

**View all SSH attacks:**
```bash
# Linux/Mac
tail -f honeypot_logs/ssh_attacks.json

# Windows (PowerShell)
Get-Content honeypot_logs/ssh_attacks.json -Wait
```

**Pretty print a log file:**
```bash
python -m json.tool honeypot_logs/ssh_attacks.json | more
```

**Count attacks by type:**
```bash
# Linux/Mac
cat honeypot_logs/*_attacks.json | wc -l

# Windows (PowerShell)
@(Get-Content honeypot_logs\*_attacks.json).Count
```

### Generate Analysis Report

The monitor automatically generates reports. View the latest:

```bash
# Find latest report
ls -t honeypot_logs/report_*.json | head -1

# View it
python -m json.tool honeypot_logs/report_*.json
```

**Expected Report Contents:**
```json
{
  "timestamp": "2024-01-15T14:35:00.123456",
  "summary": {
    "total_attacks": 100,
    "unique_attackers": 1,
    "alerts_generated": 5,
    "attack_types": [
      "SSH_AUTH_ATTACK",
      "SSH_BRUTEFORCE",
      "SQL_INJECTION",
      "XSS",
      "COMMAND_INJECTION"
    ]
  },
  "top_attackers": [
    {
      "ip": "127.0.0.1",
      "attack_count": 100,
      "attack_types": ["SSH_AUTH_ATTACK", "SQL_INJECTION", "XSS"],
      "is_campaign": true
    }
  ],
  "alerts": [
    {
      "alert_id": "ALERT_127.0.0.1_1705333200",
      "severity": "CRITICAL",
      "type": "COORDINATED_ATTACK",
      "source_ip": "127.0.0.1",
      "confidence": 0.95
    }
  ]
}
```

---

## PART 6: ADVANCED SCENARIOS

### Scenario 1: Simulate Persistent Attacker

```bash
# Create a loop that repeatedly attacks
for i in {1..20}; do
  echo "Attack iteration $i"
  curl "http://localhost:8080/search?q=<script>alert($i)</script>" 2>/dev/null
  sleep 1
done
```

**Result:** Monitor detects pattern and escalates alert to CAMPAIGN

### Scenario 2: Multi-Source Attacks

Run attack tests from different machines/IPs:
```bash
# From Machine A
python attack_test_toolkit.py localhost

# From Machine B  
python attack_test_toolkit.py localhost

# From Machine C
python attack_test_toolkit.py localhost
```

**Result:** Monitor correlates and identifies coordinated attack

### Scenario 3: Test Detection Accuracy

Modify attack payloads to just below detection threshold:
```bash
# This might NOT be detected:
curl "http://localhost:8080/search?q=alert(1)"

# This WILL be detected:
curl "http://localhost:8080/search?q=<script>alert(1)</script>"
```

Monitor false positives/false negatives in reports.

---

## PART 7: TROUBLESHOOTING

### Problem: Port Already in Use
```bash
# Find what's using port 2222
lsof -i :2222  # Linux/Mac
netstat -ano | findstr :2222  # Windows

# Kill the process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Use different port by editing the Python file:
# Change: self.port = 2222
# To: self.port = 2223
```

### Problem: No Attacks Detected

1. **Check honeypot is running:**
```bash
netstat -tlnp | grep 2222  # Linux
netstat -ano | findstr 2222  # Windows
```

2. **Verify connection works:**
```bash
telnet localhost 2222
# Should show: Connected to localhost
```

3. **Check logs are being written:**
```bash
ls -la honeypot_logs/
# Should show: ssh_attacks.json (not empty)
```

### Problem: Script Won't Start

```bash
# Check Python path
which python3  # Linux/Mac
where python   # Windows

# Run with explicit Python version
python3 fake_ssh_honeypot.py

# If still failing, reinstall requirements
pip install --upgrade -r requirements.txt
```

---

## PART 8: CLEAN UP & SHUTDOWN

### Stop All Services

**Windows (if using .bat):**
```bash
# All windows will close
# Or manually close each window
```

**Linux/Mac (if using .sh):**
```bash
# Kill all honeypot processes
cat honeypot_logs/.pids | xargs kill

# Or manually
pkill -f fake_ssh_honeypot
pkill -f fake_sql_honeypot
pkill -f fake_web_honeypot
pkill -f honeypot_monitor
```

### Archive Logs

```bash
# Create timestamped backup
tar -czf honeypot_logs_$(date +%Y%m%d_%H%M%S).tar.gz honeypot_logs/

# Windows (PowerShell)
Compress-Archive -Path honeypot_logs -DestinationPath "honeypot_logs_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
```

---

## SUCCESS METRICS

### Good Sign (System Working)
✓ Honeypots starting without errors  
✓ Connections accepted from attack scripts  
✓ JSON files being created in honeypot_logs/  
✓ Monitor showing "ATTACK" messages  
✓ Report showing >50 total attacks  

### Best Case Scenario
✓ Multiple alert types generated  
✓ Campaign detection triggered (>1 attack type)  
✓ Confidence scores >0.9  
✓ Training data exported for ML  

---

**Time to Complete All Tests**: ~30 minutes  
**Expected Attack Volume**: 50-100 attacks  
**Skills Demonstrated**: Offensive + Defensive Security
