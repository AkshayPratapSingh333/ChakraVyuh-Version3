"""
FastAPI Backend: Testing & SOC Dashboard API
Endpoints for running tests, streaming results, detector stats
WebSocket support for real-time dashboard updates
"""

from fastapi import FastAPI, WebSocket, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add phase1 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'phase1_ml_detector'))

# Try to import PyTorch-dependent modules
PYTORCH_AVAILABLE = False
try:
    from detector_trainer import DetectorTrainer
    from threat_detector import ThreatDetector
    PYTORCH_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"PyTorch not available: {e}. Using mock detector.")
    DetectorTrainer = None
    ThreatDetector = None

from test_framework.payload_generator import TestPayloadGenerator
from test_framework.test_runner import TestRunner

# Initialize FastAPI
app = FastAPI(
    title="ChakraVyuh Testing & SOC Dashboard",
    description="Real-time network anomaly detection testing and monitoring",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
detector: Optional[ThreatDetector] = None
test_runner: Optional[TestRunner] = None
payload_generator: Optional[TestPayloadGenerator] = None
test_queue = asyncio.Queue()
ws_clients: set = set()
demo_alerts = []  # Store mock alerts for demo mode
demo_alert_lock = asyncio.Lock()


# ============================================================================
# INITIALIZATION
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize detector and test framework on startup."""
    global detector, test_runner, payload_generator
    
    logger.info("Initializing ChakraVyuh backend...")
    
    try:
        # Initialize test framework first (works without PyTorch)
        payload_generator = TestPayloadGenerator()
        logger.info("✓ Test payload generator initialized")
        
        # Initialize detector only if PyTorch is available
        if PYTORCH_AVAILABLE:
            try:
                # Train a detector if not exists
                checkpoint_dir = Path('./backend_checkpoints')
                checkpoint_dir.mkdir(exist_ok=True)
                
                # Check for existing checkpoint
                existing_checkpoints = list(checkpoint_dir.glob('detector_*'))
                
                if not existing_checkpoints:
                    logger.info("Training detector...")
                    trainer = DetectorTrainer(
                        checkpoint_dir=str(checkpoint_dir),
                        window_size=5,
                        latent_dim=16,
                        batch_size=32
                    )
                    checkpoint_path = trainer.run_full_pipeline(
                        data_source='synthetic',
                        normal_samples=1000,
                        epochs=30,
                        checkpoint_name='detector_prod'
                    )
                else:
                    checkpoint_path = existing_checkpoints[0]
                
                # Load detector
                detector = ThreatDetector(str(checkpoint_path), threshold_percentile='p95')
                logger.info("✓ Threat detector initialized")
                
            except Exception as e:
                logger.warning(f"Failed to initialize detector: {e}. Running in demo mode.")
                detector = None
        else:
            logger.info("PyTorch not available - running in demo mode. ML features disabled.")
            detector = None
        
        # Initialize test runner (works with or without detector for demo mode)
        test_runner = TestRunner(detector, payload_generator)
        logger.info("✓ Test runner initialized")
        
        logger.info("✓ Backend initialized successfully")
        
        
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        # Still allow startup if at least payload generator works
        if payload_generator is not None:
            logger.warning("Backend running in degraded mode with payload generator only.")
        else:
            raise


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "detector_loaded": detector is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/status")
async def get_status() -> Dict:
    """Get detector and system status."""
    status_data = {
        "system": "running",
        "pytorch_available": PYTORCH_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if detector:
        status_data["detector"] = detector.get_stats()
    else:
        status_data["detector"] = {
            "status": "unavailable",
            "message": "Detector not initialized (PyTorch unavailable or failed to load)"
        }
    
    if test_runner:
        status_data["test_framework"] = test_runner.get_test_summary()
    else:
        status_data["test_framework"] = {
            "status": "demo_mode",
            "message": "Test framework available in demo mode (no ML detection)"
        }
    
    return status_data


# ============================================================================
# DETECTOR ENDPOINTS
# ============================================================================

@app.get("/api/v1/detector/alerts")
async def get_recent_alerts(limit: int = Query(20, ge=1, le=100)) -> List[Dict]:
    """Get recent alerts."""
    if not detector:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    return detector.get_alerts(limit=limit)


@app.get("/api/v1/detector/stats")
async def get_detector_stats() -> Dict:
    """Get detector statistics."""
    if not detector:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    return detector.get_stats()


@app.post("/api/v1/detector/process-flow")
async def process_flow(flow: Dict) -> Dict:
    """
    Process a single network flow.
    
    Expected fields:
    - src_ip, dst_ip, src_port, dst_port, protocol
    - packet_count, total_bytes, duration
    - inter_arrival_time, payload_size_variance
    - flag_pattern, window_size
    """
    if not detector:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    try:
        alert = detector.process_flow(flow)
        
        # Broadcast to WebSocket clients
        await broadcast_update({
            'type': 'new_flow',
            'alert': alert.to_dict() if alert else None,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'status': 'anomalous' if alert else 'normal',
            'alert': alert.to_dict() if alert else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# TESTING ENDPOINTS
# ============================================================================

@app.get("/api/v1/testing/attacks")
async def list_attacks() -> Dict:
    """List available attack types."""
    if not payload_generator:
        return {}  # Fallback to empty during initialization
    
    attacks = [
        'port_scan',
        'dos_flood',
        'brute_force',
        'slow_exfiltration',
        'command_injection',
        'stealth_scanning'
    ]
    
    attack_info = {}
    for attack in attacks:
        attack_info[attack] = payload_generator.get_attack_info(attack)
    
    return attack_info


@app.post("/api/v1/testing/run-test")
async def run_test(
    attack_type: str = Query(...),
    n_flows: int = Query(100, ge=10, le=1000)
) -> Dict:
    """
    Run an attack test.
    Returns detection metrics (real if detector available, simulated otherwise).
    """
    if not test_runner:
        raise HTTPException(status_code=503, detail="Test framework not initialized")
    
    try:
        result = test_runner.run_attack_test(attack_type, n_flows=n_flows)
        
        # In demo mode, create mock alerts for the SOC dashboard
        if not detector:
            demo_severities = {
                'port_scan': 'MEDIUM',
                'dos_flood': 'CRITICAL',
                'brute_force': 'HIGH',
                'slow_exfiltration': 'CRITICAL',
                'command_injection': 'CRITICAL',
                'stealth_scanning': 'MEDIUM'
            }
            
            n_alerts = int(result.n_flows * result.detection_rate)
            for i in range(min(n_alerts, 15)):  # Limit to 15 demo alerts
                demo_alerts.insert(0, {
                    'flow_id': f"{attack_type}_{i}",
                    'severity': demo_severities.get(attack_type, 'MEDIUM'),
                    'anomaly_score': float(result.avg_anomaly_score),
                    'timestamp': datetime.utcnow().isoformat()
                })
            # Keep only last 50 alerts
            demo_alerts[:] = demo_alerts[:50]
        
        # Broadcast result to WebSocket clients
        await broadcast_update({
            'type': 'test_completed',
            'test_result': result.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return result.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/testing/run-suite")
async def run_full_test_suite() -> Dict:
    """Run complete test suite for all attack types."""
    if not test_runner:
        raise HTTPException(status_code=503, detail="Test framework not initialized")
    
    try:
        summary = test_runner.run_full_test_suite()
        
        # In demo mode, create mock alerts for all test results
        if not detector:
            demo_severities = {
                'port_scan': 'MEDIUM',
                'dos_flood': 'CRITICAL',
                'brute_force': 'HIGH',
                'slow_exfiltration': 'CRITICAL',
                'command_injection': 'CRITICAL',
                'stealth_scanning': 'MEDIUM'
            }
            
            # Prepare alert data for all attack types
            attack_alerts = {}
            
            for attack_type, result in summary.get('results', {}).items():
                if isinstance(result, dict) and 'error' not in result:
                    n_flows = result.get('n_flows', 100)
                    detection_rate = result.get('detection_rate', 0)
                    n_detected = int(n_flows * detection_rate)
                    
                    # Create 3-5 alerts per attack type
                    alerts_to_create = min(max(3, n_detected // 20), 5)
                    attack_alerts[attack_type] = {
                        'alerts': [
                            {
                                'flow_id': f"{attack_type}_{i}",
                                'severity': demo_severities.get(attack_type, 'MEDIUM'),
                                'anomaly_score': float(result.get('avg_anomaly_score', 0.5)),
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            for i in range(alerts_to_create)
                        ]
                    }
            
            # Interleave alerts from all attack types for better visualization
            # This ensures the Real-time Alerts show variety from all 6 attacks
            max_alerts = max((len(a['alerts']) for a in attack_alerts.values()), default=0)
            
            for alert_index in range(max_alerts):
                for attack_type in sorted(attack_alerts.keys()):  # Process in sorted order for consistency
                    if alert_index < len(attack_alerts[attack_type]['alerts']):
                        alert = attack_alerts[attack_type]['alerts'][alert_index]
                        demo_alerts.insert(0, alert)
            
            # Keep only last 100 alerts
            demo_alerts[:] = demo_alerts[:100]
        
        # Broadcast results
        await broadcast_update({
            'type': 'suite_completed',
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return summary
        
    except Exception as e:
        logger.error(f"Suite error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/testing/results")
async def get_test_results(limit: int = Query(20)) -> Dict:
    """Get test results history."""
    if not test_runner:
        return {
            'total': 0,
            'results': [],
            'summary': {}
        }
    
    results = test_runner.get_all_results()
    return {
        'total': len(results),
        'results': results[-limit:] if results else [],
        'summary': test_runner.get_test_summary()
    }


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/v1/dashboard/overview")
async def get_dashboard_overview() -> Dict:
    """Get overall dashboard data."""
    overview = {
        "timestamp": datetime.utcnow().isoformat(),
        "pytorch_available": PYTORCH_AVAILABLE
    }
    
    if detector and test_runner:
        overview['detector'] = detector.get_stats()
        test_summary = test_runner.get_test_summary()
        overview['testing'] = {
            'total_tests': test_summary.get('total_tests', 0),
            'passed_tests': test_summary.get('passed_tests', 0),
            'failed_tests': test_summary.get('failed_tests', 0),
            'pass_rate': test_summary.get('passed_tests', 0) / max(test_summary.get('total_tests', 1), 1),
            'avg_detection_rate': test_summary.get('avg_detection_rate', 0)
        }
        overview['recent_alerts'] = detector.get_alerts(limit=10)
        overview['recent_tests'] = test_runner.get_all_results()[-5:] if test_runner.get_all_results() else []
    else:
        # Demo mode: return mock data with proper structure
        overview['mode'] = 'demo'
        overview['detector'] = {
            "status": "demo_mode",
            "alerts_emitted": len(demo_alerts),
            "flows_processed": len(demo_alerts),  # Count of alerts as proxy for flows
            "threshold": 0.95,
            "recent_alerts": demo_alerts[:10] if demo_alerts else []
        }
        
        # Get test summary for demo mode
        if test_runner:
            test_summary = test_runner.get_test_summary()
            total = test_summary.get('total_tests', 0)
            passed = test_summary.get('passed_tests', 0)
            failed = test_summary.get('failed_tests', 0)
            
            overview['testing'] = {
                'status': 'ready',
                'total_tests': total,
                'passed_tests': passed,
                'failed_tests': failed,
                'pass_rate': passed / max(total, 1) if total > 0 else 0,
                'avg_detection_rate': test_summary.get('avg_detection_rate', 0)
            }
        else:
            overview['testing'] = {
                'status': 'ready',
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'pass_rate': 0,
                'avg_detection_rate': 0
            }
        
        overview['recent_alerts'] = demo_alerts[:10] if demo_alerts else []
        overview['recent_tests'] = test_runner.get_all_results()[-5:] if test_runner and test_runner.get_all_results() else []
    
    return overview


@app.get("/api/v1/dashboard/threat-map")
async def get_threat_map() -> Dict:
    """Get data for threat map visualization."""
    if detector and demo_alerts:
        alerts = detector.get_alerts(limit=50)
    elif demo_alerts:
        # Demo mode: use demo alerts
        alerts = demo_alerts[:50]
    else:
        return {
            'mode': 'demo',
            'threats': [],
            'total': 0,
            'message': 'No threat data available (run tests to generate data)',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Group by source/destination for visualization
    threat_flows = {}
    for alert in alerts:
        flow_id = alert['flow_id']
        if flow_id not in threat_flows:
            threat_flows[flow_id] = {
                'flow_id': flow_id,
                'count': 0,
                'severity': alert['severity'],
                'latest': alert['timestamp']
            }
        threat_flows[flow_id]['count'] += 1
    
    return {
        'threats': list(threat_flows.values()),
        'total': len(threat_flows),
        'timestamp': datetime.utcnow().isoformat()
    }


@app.get("/api/v1/honeypot/alerts")
async def get_honeypot_alerts(limit: int = Query(50, ge=1, le=500)) -> Dict:
    """
    Get attacks captured by honeypot services.
    Reads from honeypot_logs directory: SSH, SQL, and Web attacks.
    """
    from pathlib import Path
    import json
    
    honeypot_alerts = []
    honeypot_dir = Path(__file__).parent.parent / "phase3_honeypot" / "honeypot_logs"
    
    # Map of honeypot services to their log files and severity multipliers
    honeypot_sources = {
        'SSH': ('ssh_attacks.json', 'HIGH'),
        'SQL': ('sql_attacks.json', 'CRITICAL'),
        'WEB': ('web_attacks.json', 'HIGH')
    }
    
    # Read attacks from all honeypot sources
    for source_name, (log_file, base_severity) in honeypot_sources.items():
        log_path = honeypot_dir / log_file
        
        try:
            if log_path.exists() and log_path.stat().st_size > 0:
                with open(log_path, 'r') as f:
                    for line in f:
                        try:
                            attack = json.loads(line.strip())
                            
                            # Normalize attack data to dashboard format
                            alert = {
                                'source': source_name,
                                'attack_type': attack.get('type', 'UNKNOWN'),
                                'source_ip': attack.get('source_ip', 'N/A'),
                                'severity': attack.get('severity', base_severity),
                                'timestamp': attack.get('timestamp', datetime.utcnow().isoformat()),
                                'description': attack.get('payload_sample', attack.get('query_sample', 'Attack detected')),
                                'payload': attack.get('payload_sample', attack.get('query_sample', '')),
                                'raw': attack
                            }
                            honeypot_alerts.append(alert)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Error reading {source_name} honeypot log: {e}")
            continue
    
    # Sort by timestamp (newest first) and limit
    honeypot_alerts.sort(
        key=lambda x: x['timestamp'],
        reverse=True
    )
    honeypot_alerts = honeypot_alerts[:limit]
    
    return {
        'alerts': honeypot_alerts,
        'total': len(honeypot_alerts),
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'honeypot'
    }


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

async def broadcast_update(message: Dict):
    """Broadcast update to all connected WebSocket clients."""
    if ws_clients:
        disconnected = set()
        for client in ws_clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected.add(client)
        
        # Clean up disconnected clients
        ws_clients.difference_update(disconnected)


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    Clients receive:
    - new_flow: When a flow is processed
    - test_completed: When a test finishes
    - suite_completed: When test suite finishes
    """
    await websocket.accept()
    ws_clients.add(websocket)
    
    logger.info(f"WebSocket client connected | Total clients: {len(ws_clients)}")
    
    try:
        # Keep connection alive and receive/process messages
        while True:
            data = await websocket.receive_text()
            
            # Process client messages (e.g., subscribe to specific updates)
            try:
                msg = json.loads(data)
                if msg.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong'})
            except json.JSONDecodeError:
                pass
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
    
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        ws_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected | Total clients: {len(ws_clients)}")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root() -> Dict:
    """Root endpoint with API documentation."""
    return {
        "name": "ChakraVyuh Testing & SOC Dashboard",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "detector": "/api/v1/detector/stats",
            "testing": "/api/v1/testing/attacks",
            "dashboard": "/api/v1/dashboard/overview",
            "websocket": "/ws/dashboard",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting ChakraVyuh Backend API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
