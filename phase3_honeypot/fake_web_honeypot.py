"""
FAKE WEB APPLICATION HONEYPOT
Mimics a vulnerable web application to capture HTTP attacks
Logs all requests, detects injection attempts, and records attack payloads
"""

from flask import Flask, request, Response
import logging
import json
from datetime import datetime
from pathlib import Path
import re
from threading import Thread

# Configure logging
log_dir = Path("honeypot_logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "web_honeypot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WEB_HONEYPOT")

app = Flask(__name__)

class WebHoneypot:
    """
    Fake web application that:
    1. Mimics a vulnerable web app on port 8080
    2. Accepts all HTTP methods and payloads
    3. Detects common web attacks (XSS, SQLi, command injection, etc.)
    4. Records all attack attempts with payloads
    5. Provides realistic error messages to keep attackers engaged
    """
    
    def __init__(self):
        self.attack_log = []
        self.attack_patterns = {
            'XSS': [
                r'(<script|javascript:|onerror=|onload=)',
                r'(<iframe|<img)',
                r'(alert\(|prompt\(|confirm\()',
            ],
            'SQL_INJECTION': [
                r"(\bUNION\b.*\bSELECT\b)",
                r"(\bOR\b.*=.*)",
                r"(--\s|#|\/\*)",
                r"(\bDROP\b|\bDELETE\b)",
            ],
            'COMMAND_INJECTION': [
                r'(;|\||&{1,2})\s*(cat|ls|whoami|id|rm|curl|wget)',
                r'(`|\.|\$\()',
            ],
            'PATH_TRAVERSAL': [
                r'(\.\./|\.\.\\)',
                r'(%2e%2f)',
            ],
            'XXE': [
                r'(<!ENTITY|<!DOCTYPE)',
                r'(SYSTEM|PUBLIC)',
            ],
        }
    
    def log_attack(self, attack_info):
        """Log attack details"""
        self.attack_log.append(attack_info)
        
        with open(log_dir / "web_attacks.json", "a") as f:
            f.write(json.dumps(attack_info) + "\n")
        
        logger.warning(f"[ATTACK] {attack_info['type']} from {attack_info['source_ip']}")
    
    def analyze_request(self, client_ip):
        """Analyze incoming request for attacks"""
        
        # Combine all request data for analysis
        full_request = f"{request.method} {request.path} {request.query_string.decode('utf-8', errors='ignore')} "
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                full_request += request.get_data(as_text=True)
            except:
                pass
        
        # Check headers
        for header, value in request.headers:
            full_request += f"{header}: {value} "
        
        # Detect attacks
        detected_attacks = []
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_request, re.IGNORECASE):
                    detected_attacks.append(attack_type)
                    break
        
        if detected_attacks:
            self.log_attack({
                'type': detected_attacks[0],
                'source_ip': client_ip,
                'method': request.method,
                'path': request.path,
                'query': request.query_string.decode('utf-8', errors='ignore'),
                'headers': dict(request.headers),
                'payload_sample': full_request[:1000],
                'timestamp': datetime.now().isoformat(),
                'severity': 'HIGH'
            })
            return detected_attacks[0]
        
        return None
    
    def start(self, host='0.0.0.0', port=8080):
        """Start the web honeypot"""
        logger.info(f"Web Honeypot starting on {host}:{port}")
        print(f"✓ Web Honeypot starting on {host}:{port}")
        
        # Set up Flask route handlers
        self.setup_routes()
        
        # Run Flask app
        app.run(host=host, port=port, debug=False, threaded=True)
    
    def setup_routes(self):
        """Setup Flask routes to catch all traffic"""
        honeypot = self
        
        @app.before_request
        def log_request():
            client_ip = request.remote_addr
            logger.info(f"[REQUEST] {request.method} {request.path} from {client_ip}")
            
            # Analyze for attacks
            attack_type = honeypot.analyze_request(client_ip)
            
            # Store in request context for response
            request.attack_detected = attack_type
        
        @app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
        @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
        def catch_all(path):
            """Catch all HTTP requests"""
            
            # Fake response based on what endpoint was accessed
            if 'login' in path or 'admin' in path:
                html = """
                <html>
                <head><title>Admin Login</title></head>
                <body>
                    <h1>Admin Login</h1>
                    <form method="POST">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Login</button>
                    </form>
                </body>
                </html>
                """
                return Response(html, status=401, mimetype='text/html')
            
            elif 'database' in path or 'api' in path:
                return Response(
                    json.dumps({'error': 'Authorization required', 'code': 401}),
                    status=401,
                    mimetype='application/json'
                )
            
            elif 'file' in path or 'download' in path:
                return Response(
                    "Error: File not found or access denied",
                    status=403,
                    mimetype='text/plain'
                )
            
            else:
                html = """
                <html>
                <head><title>Honeypot Web Server</title></head>
                <body>
                    <h1>Welcome to Our Server</h1>
                    <p>This is a legitimate web server with sensitive data.</p>
                    <ul>
                        <li><a href="/admin">Admin Panel</a></li>
                        <li><a href="/api/users">User API</a></li>
                        <li><a href="/database">Database Admin</a></li>
                    </ul>
                </body>
                </html>
                """
                return Response(html, status=200, mimetype='text/html')

# Create honeypot instance
honeypot = WebHoneypot()

if __name__ == "__main__":
    honeypot.start()
