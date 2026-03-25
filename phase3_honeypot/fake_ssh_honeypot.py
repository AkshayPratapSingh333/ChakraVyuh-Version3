"""
FAKE SSH HONEYPOT SERVICE
Mimics a real SSH server to capture attack attempts
Logs all connection attempts, bruteforce attempts, and unusual commands
"""

import socket
import threading
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
log_dir = Path("honeypot_logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "ssh_honeypot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SSH_HONEYPOT")

class SSHHoneypot:
    """
    Fake SSH server that:
    1. Accepts connections on port 2222
    2. Mimics SSH protocol handshake
    3. Logs all authentication attempts
    4. Records bruteforce attacks
    5. Captures malicious commands
    """
    
    def __init__(self, host='localhost', port=2222):
        self.host = host
        self.port = port
        self.server_socket = None
        self.attack_log = []
        self.failed_logins = {}  # Track failed attempts per IP
        
    def start(self):
        """Start the honeypot server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        logger.info(f"SSH Honeypot listening on {self.host}:{self.port}")
        print(f"✓ SSH Honeypot started on {self.host}:{self.port}")
        
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                # Handle each connection in a separate thread
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                thread.start()
        except KeyboardInterrupt:
            logger.info("SSH Honeypot shutting down...")
            self.server_socket.close()
    
    def handle_client(self, client_socket, client_address):
        """Handle individual SSH connection"""
        client_ip = client_address[0]
        logger.info(f"[ALERT] Connection from {client_ip}")
        
        try:
            # Send fake SSH banner
            ssh_banner = b"SSH-2.0-OpenSSH_7.4\r\n"
            client_socket.send(ssh_banner)
            logger.debug(f"Sent SSH banner to {client_ip}")
            
            # Receive client banner
            client_banner = client_socket.recv(1024)
            logger.debug(f"Received from {client_ip}: {client_banner.decode('utf-8', errors='ignore')}")
            
            # Simulate authentication exchange
            auth_request = self.receive_data(client_socket, client_ip)
            
            if auth_request:
                self.analyze_auth(auth_request, client_ip)
                
                # Log failed authentication
                if client_ip in self.failed_logins:
                    self.failed_logins[client_ip] += 1
                else:
                    self.failed_logins[client_ip] = 1
                
                # Detect bruteforce (>5 attempts = bruteforce)
                if self.failed_logins[client_ip] > 5:
                    logger.warning(f"[BRUTEFORCE DETECTED] {client_ip} - {self.failed_logins[client_ip]} attempts")
                
                # Send denial
                denial = b"\x00\x00\x00\x24\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                client_socket.send(denial)
            
        except Exception as e:
            logger.error(f"Error handling {client_ip}: {str(e)}")
        finally:
            client_socket.close()
            logger.info(f"Connection from {client_ip} closed")
    
    def receive_data(self, client_socket, client_ip):
        """Receive data from client"""
        try:
            data = client_socket.recv(4096)
            return data
        except:
            return None
    
    def analyze_auth(self, auth_data, client_ip):
        """Analyze authentication attempt for attacks"""
        try:
            auth_str = auth_data.decode('utf-8', errors='ignore')
            
            # Check for common attacks
            attacks = {
                'root': 'Attempting root access',
                'admin': 'Attempting admin access',
                'oracle': 'Attempting database access',
                'test': 'Attempting test account access',
                'password': 'Password in cleartext detected',
            }
            
            for keyword, description in attacks.items():
                if keyword.lower() in auth_str.lower():
                    logger.warning(f"[ATTACK] {client_ip} - {description}")
                    self.log_attack({
                        'type': 'SSH_AUTH_ATTACK',
                        'source_ip': client_ip,
                        'description': description,
                        'timestamp': datetime.now().isoformat(),
                        'payload': auth_str[:200]
                    })
        except:
            pass
    
    def log_attack(self, attack_info):
        """Log attack information to file"""
        self.attack_log.append(attack_info)
        
        with open(log_dir / "ssh_attacks.json", "a") as f:
            f.write(json.dumps(attack_info) + "\n")

if __name__ == "__main__":
    honeypot = SSHHoneypot()
    honeypot.start()
