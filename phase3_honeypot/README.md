# CHAKRAVYUH PHASE 3: HONEYPOT SYSTEM

## Overview

A comprehensive honeypot system designed to:
- **Mimic real services** (SSH, SQL Database, Web App)
- **Attract attackers** with seemingly valuable targets
- **Isolate attacks** in controlled environment
- **Record every attack** for analysis
- **Feed ML detector** with real attack patterns

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│        ATTACKER / RED TEAM / PENETRATION TESTER         │
└────────────┬────────────────────────────────────────────┘
             │
             ├─────────────────┬──────────────────┬──────────────────┐
             ▼                 ▼                  ▼                  ▼
        ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ SSH Service │  │ SQL Database │  │ Web Service  │  │  Monitoring  │
        │ :2222       │  │ :3307        │  │ :8080        │  │   System     │
        └─────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
             │                 │                  │                  ▲
             └─────────────────┼──────────────────┴──────────────────┘
                               │
                      ┌────────▼────────┐
                      │ Honeypot Logs   │
                      │ JSON Format     │
                      └────────┬────────┘
                               │
                      ┌────────▼─────────────┐
                      │ Honeypot Monitor    │
                      │ - Aggregates logs   │
                      │ - Detects campaigns │
                      │ - Generates alerts  │
                      │ - Exports ML data   │
                      └────────┬────────────┘
                               │
                      ┌────────▼────────────────┐
                      │ Phase 1 ML Detector    │
                      │ (Real-time analysis)   │
                      └────────────────────────┘
```

---

## QUICK START (5 MINUTES)

### 1. Install Dependencies
```bash
cd d:\ComputerScienceProject\ChakraVyuh-Version3\phase3_honeypot

# Install required packages
pip install -r requirements.txt
```

### 2. Start Honeypots (Open 4 Terminals)

**Terminal 1 - SSH Honeypot:**
```bash
cd d:\ComputerScienceProject\ChakraVyuh-Version3\phase3_honeypot
python fake_ssh_honeypot.py
```
Expected Output:
```
✓ SSH Honeypot started on localhost:2222
```

**Terminal 2 - SQL Database Honeypot:**
```bash
cd d:\ComputerScienceProject\ChakraVyuh-Version3\phase3_honeypot
python fake_sql_honeypot.py
```
Expected Output:
```
✓ SQL Honeypot started on localhost:3307
```

**Terminal 3 - Web Honeypot:**
```bash
cd d:\ComputerScienceProject\ChakraVyuh-Version3\phase3_honeypot
python fake_web_honeypot.py
```
Expected Output:
```
✓ Web Honeypot starting on 0.0.0.0:8080
```

**Terminal 4 - Honeypot Monitor:**
```bash
cd d:\ComputerScienceProject\ChakraVyuh-Version3\phase3_honeypot
python honeypot_monitor.py
```
Expected Output:
```
============================================================
HONEYPOT MONITOR - Real-time Attack Analysis
============================================================
```

### 3. Run Attack Tests (New Terminal)
```bash
cd d:\ComputerScienceProject\ChakraVyuh-Version3\phase3_honeypot
python attack_test_toolkit.py
```

---

## DETAILED SETUP & CONFIGURATION

### Environment Variables

```bash
# Windows Command Prompt
set SSH_PORT=2222
set SQL_PORT=3307
set WEB_PORT=8080
set LOG_DIR=honeypot_logs

# Or in Python:
import os
os.environ['SSH_PORT'] = '2222'
```

### Log Locations
All logs are stored in `honeypot_logs/` directory:
```
honeypot_logs/
├── ssh_honeypot.log          # SSH service general log
├── ssh_attacks.json          # SSH attacks (JSON format)
├── sql_honeypot.log          # SQL service general log
├── sql_attacks.json          # SQL attacks (JSON format)
├── web_honeypot.log          # Web service general log
├── web_attacks.json          # Web attacks (JSON format)
├── monitor.log               # Monitor activity
├── training_data.json        # ML training data
└── report_YYYYMMDD_HHMMSS.json  # Generated reports
```

---

## COMMAND REFERENCE & TESTING

### TEST 1: SSH Brute Force Detection

**What it does:** Simulates attacker trying multiple username/password combinations

**Command:**
```bash
python attack_test_toolkit.py
# Then watch for "TEST 2: SSH Brute Force Attack" output
```

**Expected Honeypot Output:**
```
2024-01-15 10:23:45 - WARNING - [ATTACK] localhost - Attempting root access
2024-01-15 10:23:46 - WARNING - [BRUTEFORCE DETECTED] 127.0.0.1 - 6 attempts
```

**Expected Monitor Output:**
```
[10:24:15] Attack Summary:
  Total Attacks: 10
  Unique Attackers: 1
  New Alerts: 1

  Top Attackers:
    - 127.0.0.1: 10 attacks
```

**What gets logged:**
```json
{
  "type": "SSH_AUTH_ATTACK",
  "source_ip": "127.0.0.1",
  "description": "Attempting root access",
  "timestamp": "2024-01-15T10:23:45.123456",
  "payload": "root:password123"
}
```

---

### TEST 2: SQL Injection Detection

**What it does:** Sends various SQL injection patterns to database

**Command:**
```bash
python attack_test_toolkit.py
# Then watch for "TEST 4: SQL Injection Attacks" output
```

**Expected Honeypot Output:**
```
2024-01-15 10:24:30 - WARNING - [SQL INJECTION DETECTED] 127.0.0.1 - Pattern: (\bUNION\b.*\bSELECT\b)
```

**Expected Alert Generated:**
```json
{
  "alert_id": "ALERT_127.0.0.1_1705318470",
  "severity": "CRITICAL",
  "type": "SQL_INJECTION_ATTEMPT",
  "source_ip": "127.0.0.1",
  "description": "SQL Injection attack detected - Database at risk",
  "confidence": 0.98,
  "timestamp": "2024-01-15T10:24:30.123456"
}
```

---

### TEST 3: XSS Attack Detection

**What it does:** Tests various Cross-Site Scripting payloads

**Command:**
```bash
# Using curl
curl "http://localhost:8080/search?q=<script>alert('XSS')</script>"

# Or via attack toolkit
python attack_test_toolkit.py
# Watch for "TEST 6: XSS Attacks"
```

**Expected Honeypot Output:**
```
2024-01-15 10:25:15 - WARNING - [ATTACK] 127.0.0.1 - XSS
```

**Payload logged:**
```json
{
  "type": "XSS",
  "source_ip": "127.0.0.1",
  "method": "GET",
  "path": "/search",
  "payload_sample": "alert('XSS')",
  "timestamp": "2024-01-15T10:25:15.123456"
}
```

---

### TEST 4: Command Injection Detection

**What it does:** Attempts to execute system commands through web app

**Command:**
```bash
curl "http://localhost:8080/execute?cmd=;ls%20-la"

# Or via attack toolkit
python attack_test_toolkit.py
# Watch for "TEST 8: Command Injection Attacks"
```

**Expected Honeypot Output:**
```
2024-01-15 10:26:00 - WARNING - [ATTACK] 127.0.0.1 - COMMAND_INJECTION
```

**Payload logged:**
```json
{
  "type": "COMMAND_INJECTION",
  "source_ip": "127.0.0.1",
  "method": "GET",
  "payload_sample": "ls -la",
  "timestamp": "2024-01-15T10:26:00.123456"
}
```

---

### TEST 5: Multi-Vector Attack Campaign

**What it does:** Simulates sophisticated attacker using multiple attack vectors

**Command:**
```bash
python attack_test_toolkit.py
# Watch for "TEST 10: Coordinated Multi-Vector Attack Campaign"
```

**Expected Monitor Alert:**
```json
{
  "alert_id": "ALERT_127.0.0.1_1705318500",
  "severity": "HIGH",
  "type": "MULTI_VECTOR_ATTACK",
  "source_ip": "127.0.0.1",
  "description": "Multiple attack vectors detected: SSH_AUTH_ATTACK, SQL_INJECTION, XSS",
  "attack_types": ["SSH_AUTH_ATTACK", "SQL_INJECTION", "XSS"],
  "tactics": ["Valid Accounts", "Exploitation"],
  "confidence": 0.85,
  "is_campaign": true,
  "timestamp": "2024-01-15T10:26:30.123456"
}
```

---

## MANUAL TESTING AS AN ATTACKER

### Test 1: Manual SSH Connection
```bash
# Connect to SSH honeypot
ssh -p 2222 root@localhost

# Or using basic socket connection (Windows PowerShell)
$socket = New-Object System.Net.Sockets.TcpClient
$socket.Connect('localhost', 2222)
$stream = $socket.GetStream()
$reader = New-Object System.IO.StreamReader($stream)
$writer = New-Object System.IO.StreamWriter($stream)
$banner = $reader.ReadLine()
Write-Host "SSH Banner: $banner"
$socket.Close()
```

**What honeypot logs:**
```
2024-01-15 10:30:00 - INFO - [ALERT] Connection from 127.0.0.1
2024-01-15 10:30:00 - DEBUG - Sent SSH banner to 127.0.0.1
2024-01-15 10:30:01 - INFO - Connection from 127.0.0.1 closed
```

---

### Test 2: Manual SQL Injection
```bash
# Using PowerShell script to connect to database
Add-Type -AssemblyName System.Data
$conn = New-Object System.Data.SqlClient.SqlConnection
$conn.ConnectionString = "Server=localhost,3307;User Id=sa;Password=password;"

try {
    $conn.Open()
    Write-Host "Connected to database"
    
    # Send SQL injection payload
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "1' OR '1'='1"
    $cmd.ExecuteReader()
}
catch {
    Write-Host "Connection failed (expected)"
}
finally {
    $conn.Close()
}
```

Or simpler with netcat:
```bash
# Connect and send injection
echo "1' OR '1'='1" | nc localhost 3307
```

**What honeypot logs:**
```
2024-01-15 10:31:00 - WARNING - [SQL INJECTION DETECTED] 127.0.0.1 - Pattern: (\bOR\b.*=.*)
2024-01-15 10:31:00 - INFO - Attack logged to sql_attacks.json
```

---

### Test 3: Web Application Attacks

**XSS Attack:**
```bash
curl "http://localhost:8080/search?q=<script>alert('XSS')</script>"
curl "http://localhost:8080/admin?email=<img%20src=x%20onerror=alert(1)>"
```

**SQL Injection via Web:**
```bash
curl -X POST "http://localhost:8080/api/users" \
  -d "username=admin' --&password=anything"
```

**Command Injection:**
```bash
curl "http://localhost:8080/execute?cmd=;ls%20-la;id;"
curl "http://localhost:8080/ping?host=google.com%20|%20whoami"
```

**Path Traversal:**
```bash
curl "http://localhost:8080/file?path=../../etc/passwd"
curl "http://localhost:8080/download?file=..\\..\\windows\\system32\\config\\sam"
```

---

## MONITORING & ANALYSIS

### View Real-time Logs
```bash
# SSH attacks (in real-time)
tail -f honeypot_logs/ssh_attacks.json

# SQL attacks
tail -f honeypot_logs/sql_attacks.json

# Web attacks
tail -f honeypot_logs/web_attacks.json

# All attacks with pretty formatting
python -m json.tool honeypot_logs/ssh_attacks.json
```

### Generate Report
```bash
# The monitor generates automatic reports
# Check: honeypot_logs/report_YYYYMMDD_HHMMSS.json

# View latest report
python -m json.tool honeypot_logs/report_*.json | more
```

### Check Generated Alerts
```bash
# Alerts are included in monitor reports
# Example query:
python -c "
import json
with open('honeypot_logs/report_*.json') as f:
    data = json.load(f)
    for alert in data['alerts']:
        print(f\"{alert['severity']} - {alert['type']}: {alert['source_ip']}\")
"
```

---

## STATISTICS & METRICS

### Sample Report Output
```json
{
  "timestamp": "2024-01-15T10:35:00.123456",
  "summary": {
    "total_attacks": 45,
    "unique_attackers": 3,
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
      "ip": "192.168.1.100",
      "attack_count": 20,
      "attack_types": ["SSH_AUTH_ATTACK", "SSH_BRUTEFORCE"],
      "is_campaign": true
    },
    {
      "ip": "192.168.1.101",
      "attack_count": 15,
      "attack_types": ["SQL_INJECTION", "XSS"],
      "is_campaign": false
    }
  ],
  "alerts": [
    {
      "alert_id": "ALERT_192.168.1.100_1705318500",
      "severity": "CRITICAL",
      "type": "COORDINATED_ATTACK",
      "source_ip": "192.168.1.100",
      "confidence": 0.95,
      "is_campaign": true
    }
  ]
}
```

---

## INTEGRATION WITH PHASE 1 ML DETECTOR

### Export Data for Training
```bash
# Training data automatically exported to:
# honeypot_logs/training_data.json

python -c "
import json
with open('honeypot_logs/training_data.json') as f:
    data = json.load(f)
    print(f'Collected {data[\"metadata\"][\"total_attacks\"]} attacks')
    print(f'From {data[\"metadata\"][\"unique_attackers\"]} attackers')
"
```

### Available Attack Signatures
The honeypots capture:
- **SSH**: Authentication attempts, bruteforce patterns
- **SQL**: Injection patterns, database access attempts
- **Web**: XSS, SQLi, Command Injection, XXE, Path Traversal

These can be fed into Phase 1 ML detector for:
- Training on real attack patterns
- Improving detection accuracy
- Identifying new attack techniques

---

## TROUBLESHOOTING

### "Address already in use" Error
```bash
# Find process using port
netstat -ano | findstr :2222

# Kill process (replace PID)
taskkill /PID 12345 /F

# Or use different ports and run script with custom config
```

### Honeypot Not Detecting Attacks
1. Check if honeypot is running: `netstat -ano | findstr LISTEN`
2. Check log file exists: `ls honeypot_logs/`
3. Verify attack payload is being sent
4. Check honeypot standard output for errors

### Flask "RuntimeError: This object has no attribute..."
```bash
# Reinstall Flask
pip uninstall flask -y
pip install flask==3.0.0
```

---

## NEXT STEPS

1. **Automated Attacks**: Modify `attack_test_toolkit.py` to run periodically
2. **Custom Payloads**: Add your own attack patterns in honeypot files
3. **Network Monitoring**: Deploy on real network segment with IDS
4. **ML Feedback Loop**: Use generated attack data to improve Phase 1 detector
5. **Phase 4 Integration**: Connect with Federated Learning system

---

## FILES OVERVIEW

| File | Purpose | Port |
|------|---------|------|
| `fake_ssh_honeypot.py` | Mimics SSH server | 2222 |
| `fake_sql_honeypot.py` | Mimics MySQL/PostgreSQL | 3307 |
| `fake_web_honeypot.py` | Mimics vulnerable web app | 8080 |
| `honeypot_monitor.py` | Central monitoring & alerting | - |
| `attack_test_toolkit.py` | Test framework for attacks | - |
| `requirements.txt` | Python dependencies | - |

---

**Created**: 2024
**Version**: 3.0 (ChakraVyuh Phase 3)
**Status**: Production-Ready
