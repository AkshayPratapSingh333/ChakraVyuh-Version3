"""
HONEYPOT MONITOR - Central Aggregation and Analysis System
Collects attacks from all honeypots, generates alerts, and feeds data to ML detector
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path("honeypot_logs") / "monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HONEYPOT_MONITOR")

class HoneypotMonitor:
    """
    Central monitoring system that:
    1. Aggregates attacks from all honeypots
    2. Correlates attacks from same source
    3. Generates high-confidence threat alerts
    4. Exports data for ML training
    5. Identifies attack patterns and campaigns
    """
    
    def __init__(self):
        self.log_dir = Path("honeypot_logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.attacks = []
        self.attacker_profiles = defaultdict(lambda: {
            'total_attacks': 0,
            'attack_types': [],
            'timestamps': [],
            'severity_levels': [],
            'tactics': set(),
            'is_campaign': False
        })
        
    def read_attack_logs(self):
        """Read all attack logs from honeypots"""
        
        honeypot_files = [
            'ssh_attacks.json',
            'sql_attacks.json',
            'web_attacks.json'
        ]
        
        for log_file in honeypot_files:
            file_path = self.log_dir / log_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    for line in f:
                        try:
                            attack = json.loads(line.strip())
                            self.attacks.append(attack)
                        except json.JSONDecodeError:
                            pass
    
    def analyze_attacks(self):
        """Analyze all collected attacks"""
        
        for attack in self.attacks:
            source_ip = attack.get('source_ip')
            attack_type = attack.get('type')
            timestamp = attack.get('timestamp')
            
            if source_ip:
                profile = self.attacker_profiles[source_ip]
                profile['total_attacks'] += 1
                profile['attack_types'].append(attack_type)
                profile['timestamps'].append(timestamp)
                
                # Determine tactic from attack type
                tactic = self.classify_tactic(attack_type)
                profile['tactics'].add(tactic)
                
                # Detect campaign (multiple attack types from same source)
                if len(set(profile['attack_types'])) >= 3:
                    profile['is_campaign'] = True
    
    def classify_tactic(self, attack_type):
        """Classify attack type to MITRE ATT&CK tactic"""
        
        tactic_map = {
            'SSH_AUTH_ATTACK': 'Valid Accounts / Brute Force',
            'SSH_BRUTEFORCE': 'Brute Force',
            'DB_AUTH_ATTACK': 'Valid Accounts / Credential Access',
            'SQL_INJECTION': 'Exploitation / Code Injection',
            'XSS': 'Exploitation / Code Injection',
            'COMMAND_INJECTION': 'Exploitation / Code Injection',
            'PATH_TRAVERSAL': 'Exploitation / Defense Evasion',
            'XXE': 'Exploitation / Code Injection',
        }
        
        return tactic_map.get(attack_type, 'Unknown')
    
    def generate_alerts(self):
        """Generate high-confidence threats based on patterns"""
        
        alerts = []
        
        for attacker_ip, profile in self.attacker_profiles.items():
            
            # Alert 1: Brute force (>5 attempts in short time)
            if profile['total_attacks'] > 5:
                # Check if attacks are within short time window
                if len(profile['timestamps']) >= 2:
                    timestamps = sorted(profile['timestamps'])
                    time_diff = datetime.fromisoformat(timestamps[-1]) - datetime.fromisoformat(timestamps[0])
                    
                    if time_diff.total_seconds() < 3600:  # Within 1 hour
                        alerts.append({
                            'alert_id': f"ALERT_{attacker_ip}_{int(time.time())}",
                            'severity': 'CRITICAL',
                            'type': 'COORDINATED_ATTACK',
                            'source_ip': attacker_ip,
                            'description': f'{profile["total_attacks"]} attack attempts in {time_diff.total_seconds()} seconds',
                            'attack_types': list(set(profile['attack_types'])),
                            'tactics': list(profile['tactics']),
                            'confidence': 0.95,
                            'is_campaign': profile['is_campaign'],
                            'timestamp': datetime.now().isoformat()
                        })
            
            # Alert 2: Multi-vector attack (campaign)
            elif profile['is_campaign']:
                alerts.append({
                    'alert_id': f"ALERT_{attacker_ip}_{int(time.time())}",
                    'severity': 'HIGH',
                    'type': 'MULTI_VECTOR_ATTACK',
                    'source_ip': attacker_ip,
                    'description': f'Multiple attack vectors detected: {", ".join(set(profile["attack_types"]))}',
                    'attack_types': list(set(profile['attack_types'])),
                    'tactics': list(profile['tactics']),
                    'confidence': 0.85,
                    'is_campaign': True,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Alert 3: SQL Injection (immediate threat)
            elif 'SQL_INJECTION' in profile['attack_types']:
                alerts.append({
                    'alert_id': f"ALERT_{attacker_ip}_{int(time.time())}",
                    'severity': 'CRITICAL',
                    'type': 'SQL_INJECTION_ATTEMPT',
                    'source_ip': attacker_ip,
                    'description': 'SQL Injection attack detected - Database at risk',
                    'attack_types': ['SQL_INJECTION'],
                    'tactics': ['Exploitation'],
                    'confidence': 0.98,
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def export_training_data(self):
        """Export honeypot data for ML model training"""
        
        training_data = {
            'metadata': {
                'source': 'honeypot',
                'collected_at': datetime.now().isoformat(),
                'total_attacks': len(self.attacks),
                'unique_attackers': len(self.attacker_profiles)
            },
            'raw_attacks': self.attacks,
            'attacker_profiles': {
                ip: {
                    'total_attacks': profile['total_attacks'],
                    'attack_types': list(set(profile['attack_types'])),
                    'tactics': list(profile['tactics']),
                    'is_campaign': profile['is_campaign'],
                    'attack_count_by_type': self.count_attacks_by_type(profile['attack_types'])
                }
                for ip, profile in self.attacker_profiles.items()
            }
        }
        
        # Save to file
        export_path = self.log_dir / "training_data.json"
        with open(export_path, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        logger.info(f"Training data exported to {export_path}")
        return training_data
    
    def count_attacks_by_type(self, attack_types):
        """Count attacks by type"""
        counts = defaultdict(int)
        for attack_type in attack_types:
            counts[attack_type] += 1
        return dict(counts)
    
    def generate_report(self):
        """Generate comprehensive honeypot report"""
        
        self.read_attack_logs()
        self.analyze_attacks()
        alerts = self.generate_alerts()
        training_data = self.export_training_data()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_attacks': len(self.attacks),
                'unique_attackers': len(self.attacker_profiles),
                'alerts_generated': len(alerts),
                'attack_types': list(set(a.get('type') for a in self.attacks if a.get('type')))
            },
            'top_attackers': self.get_top_attackers(5),
            'alerts': alerts,
            'attack_distribution': self.get_attack_distribution()
        }
        
        # Save report
        report_path = self.log_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report generated: {report_path}")
        return report
    
    def get_top_attackers(self, n=5):
        """Get top N attackers by attack count"""
        sorted_attackers = sorted(
            self.attacker_profiles.items(),
            key=lambda x: x[1]['total_attacks'],
            reverse=True
        )
        
        return [
            {
                'ip': ip,
                'attack_count': profile['total_attacks'],
                'attack_types': list(set(profile['attack_types'])),
                'is_campaign': profile['is_campaign']
            }
            for ip, profile in sorted_attackers[:n]
        ]
    
    def get_attack_distribution(self):
        """Get distribution of attack types"""
        distribution = defaultdict(int)
        
        for attack in self.attacks:
            attack_type = attack.get('type')
            if attack_type:
                distribution[attack_type] += 1
        
        return dict(distribution)

def monitor_in_realtime():
    """Continuously monitor for new attacks"""
    monitor = HoneypotMonitor()
    
    logger.info("Starting Honeypot Monitor (Real-time mode)")
    print("=" * 60)
    print("HONEYPOT MONITOR - Real-time Attack Analysis")
    print("=" * 60)
    
    while True:
        try:
            report = monitor.generate_report()
            
            # Display summary
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Attack Summary:")
            print(f"  Total Attacks: {report['summary']['total_attacks']}")
            print(f"  Unique Attackers: {report['summary']['unique_attackers']}")
            print(f"  New Alerts: {report['summary']['alerts_generated']}")
            
            if report['top_attackers']:
                print(f"\n  Top Attackers:")
                for attacker in report['top_attackers']:
                    print(f"    - {attacker['ip']}: {attacker['attack_count']} attacks")
            
            # Wait before next scan
            time.sleep(30)
            
            # Reset for next cycle
            monitor = HoneypotMonitor()
            
        except KeyboardInterrupt:
            logger.info("Monitor shutting down...")
            break
        except Exception as e:
            logger.error(f"Monitor error: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_in_realtime()
