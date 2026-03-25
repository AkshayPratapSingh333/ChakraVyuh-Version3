"""
FAKE SQL DATABASE HONEYPOT
Mimics MySQL/PostgreSQL to capture SQL injection and database attacks
Logs all connection attempts and malicious queries
"""

import socket
import threading
import json
import logging
import re
from datetime import datetime
from pathlib import Path

# Configure logging
log_dir = Path("honeypot_logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "sql_honeypot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SQL_HONEYPOT")

class SQLHoneypot:
    """
    Fake SQL database server that:
    1. Accepts connections on port 3306 (MySQL-like)
    2. Mimics MySQL protocol
    3. Logs all authentication attempts
    4. Detects SQL injection patterns
    5. Records database queries
    """
    
    def __init__(self, host='0.0.0.0', port=3307):
        self.host = host
        self.port = port
        self.server_socket = None
        self.attack_log = []
        
        # SQL Injection patterns to detect
        self.sql_injection_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bOR\b.*?=.*?)",
            r"(--\s|#|\/\*)",
            r"(\bDROP\b|\bDELETE\b|\bTRUNCATE\b)",
            r"(\bINSERT\b|\bUPDATE\b.*\bSET\b)",
            r"(xp_|sp_)",  # Extended/system procedures
            r"(EXEC|EXECUTE)",
        ]
        
    def start(self):
        """Start the honeypot server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            logger.info(f"SQL Honeypot listening on {self.host}:{self.port}")
            print(f"✓ SQL Honeypot started on {self.host}:{self.port}")
            
            while True:
                client_socket, client_address = self.server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                thread.start()
        except KeyboardInterrupt:
            logger.info("SQL Honeypot shutting down...")
            if self.server_socket:
                self.server_socket.close()
        except Exception as e:
            logger.error(f"SQL Honeypot startup error: {str(e)}", exc_info=True)
            print(f"✗ SQL Honeypot failed to start: {str(e)}")
            raise
    
    def handle_client(self, client_socket, client_address):
        """Handle SQL client connection"""
        client_ip = client_address[0]
        logger.info(f"[ALERT] Database connection from {client_ip}")
        
        try:
            # Send MySQL Initialization Packet (fake but valid)
            mysql_banner = self.create_mysql_init_packet()
            client_socket.send(mysql_banner)
            logger.debug(f"Sent MySQL banner to {client_ip}")
            
            # Receive client response (usually authentication)
            auth_data = client_socket.recv(4096)
            
            if auth_data:
                self.analyze_auth(auth_data, client_ip)
                
                # Send authentication response (OK)
                ok_packet = b"\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00"
                client_socket.send(ok_packet)
                
                # Now receive potential queries
                while True:
                    query_data = client_socket.recv(4096)
                    if not query_data:
                        break
                    
                    self.analyze_query(query_data, client_ip)
                    
                    # Send error response to trigger more attempts
                    error_packet = self.create_error_packet()
                    client_socket.send(error_packet)
            
        except Exception as e:
            logger.error(f"Error handling {client_ip}: {str(e)}")
        finally:
            client_socket.close()
            logger.info(f"Database connection from {client_ip} closed")
    
    def create_mysql_init_packet(self):
        """Create fake MySQL initialization packet"""
        # Simplified MySQL greeting packet
        return (
            b"\x0a"  # Protocol version
            b"5.7.30-0ubuntu0.18.04.1" + b"\x00"  # Server version
            b"\x01\x00\x00\x00"  # Connection ID
            b"y)7)Ks_v\x00"  # Auth plugin data (part 1)
            b"\xff\xf7"  # Server capabilities
            b"\x21"  # Server charset
            b"\x00\x00"  # Server status
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )
    
    def create_error_packet(self):
        """Create MySQL error packet to keep attacker engaged"""
        # Error: Access denied for user
        error_msg = "Access denied for user"
        return (
            b"\xff\x15\x04"  # Error header
            + b"28000"  # SQLSTATE
            + error_msg.encode() + b"\x00"
        )
    
    def analyze_auth(self, auth_data, client_ip):
        """Analyze authentication attempt"""
        try:
            auth_str = auth_data.decode('utf-8', errors='ignore')
            
            # Check for common database user attacks
            db_users = ['root', 'admin', 'sa', 'postgres', 'oracle', 'mysql']
            for user in db_users:
                if user.lower() in auth_str.lower():
                    logger.warning(f"[ATTACK] {client_ip} - Attempting {user} database access")
                    self.log_attack({
                        'type': 'DB_AUTH_ATTACK',
                        'source_ip': client_ip,
                        'target_user': user,
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            logger.debug(f"Error analyzing auth from {client_ip}: {str(e)}")
    
    def analyze_query(self, query_data, client_ip):
        """Analyze SQL queries for injection attacks"""
        try:
            query_str = query_data.decode('utf-8', errors='ignore')
            
            # Check for SQL injection patterns
            for pattern in self.sql_injection_patterns:
                if re.search(pattern, query_str, re.IGNORECASE):
                    logger.warning(f"[SQL INJECTION DETECTED] {client_ip} - Pattern: {pattern}")
                    self.log_attack({
                        'type': 'SQL_INJECTION',
                        'source_ip': client_ip,
                        'pattern_matched': pattern,
                        'query_sample': query_str[:500],
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'HIGH'
                    })
                    break
        except Exception as e:
            logger.debug(f"Error analyzing query from {client_ip}: {str(e)}")
    
    def log_attack(self, attack_info):
        """Log attack information"""
        self.attack_log.append(attack_info)
        
        with open(log_dir / "sql_attacks.json", "a") as f:
            f.write(json.dumps(attack_info) + "\n")

if __name__ == "__main__":
    honeypot = SQLHoneypot()
    honeypot.start()
