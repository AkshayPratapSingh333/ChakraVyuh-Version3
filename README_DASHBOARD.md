# ChakraVyuh Dashboard - Setup & Usage Guide

## Overview

ChakraVyuh is a comprehensive network anomaly detection system with:
- **Phase 1**: ML-based autoencoder detector
- **Testing Dashboard**: Simulate attacks and test detector accuracy
- **SOC Dashboard**: Real-time alert monitoring and threat intelligence

## System Requirements

- Python 3.8+
- Node.js 14+ (for React dashboard)
- CUDA 11.0+ (optional, for GPU acceleration)
- RAM: 4GB minimum, 8GB+ recommended for training

## Quick Start

### 1. Backend Setup (Python)

```bash
# Navigate to project root
cd d:\ComputerScienceProject\ChakraVyuh-Version3

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Train the Detector (First Time Only)

```bash
cd phase1_ml_detector

# Run training pipeline
python detector_trainer.py
```

Expected output:
```
INFO - Training detector...
INFO - Starting training for 50 epochs...
INFO - Training completed!
INFO - Checkpoint saved to: ./phase1_checkpoints/detector_v1_20240325_120000
```

### 3. Start Backend API Server

```bash
cd backend_api

# Start FastAPI server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will:
1. Load pre-trained detector
2. Initialize test framework
3. Start listening on `http://localhost:8000`

Check health: `curl http://localhost:8000/health`

### 4. Frontend Setup (React)

In a new terminal:

```bash
cd frontend_dashboard

# Install dependencies
npm install

# Start development server
npm start
```

The dashboard will open at `http://localhost:3000`

## Usage Guide

### Testing Dashboard

1. **Select Attack Type**: Choose from:
   - Port Scan: Rapid port probing
   - DoS/DDoS Flood: Massive volume attack
   - Brute Force: Password guessing
   - Data Exfiltration: Stealthy data theft
   - Command Injection: Web attack
   - Stealth Scanning: Fragmented probes

2. **Configure Test**:
   - Set number of flows (10-1000)
   - View attack indicators and severity

3. **Run Test**:
   - Click "Run Test" to simulate single attack
   - Click "Full Suite" for all 6 attack types
   - View detection rate and anomaly scores

4. **Analyze Results**:
   - Real-time progress display
   - Detection rate tracking
   - Historical performance chart
   - Result storage in test_results/

### SOC Dashboard

1. **Key Metrics**:
   - Total alerts emitted
   - Flows processed
   - Detection threshold
   - Tests executed

2. **Real-time Alerts**:
   - Live alert stream
   - Severity indicators (CRITICAL/HIGH/MEDIUM/LOW)
   - Flow identification
   - Timestamps

3. **Threat Map**:
   - Critical threats visualization
   - Threat frequency tracking
   - Severity distribution pie chart

4. **Testing Status**:
   - Overall test pass rate
   - Detection performance metrics
   - Test history

## API Endpoints

### Health & Status
- `GET /health` - Check backend health
- `GET /api/v1/status` - Get system status

### Detector
- `GET /api/v1/detector/alerts?limit=20` - Get recent alerts
- `GET /api/v1/detector/stats` - Get detector statistics
- `POST /api/v1/detector/process-flow` - Process single flow

### Testing
- `GET /api/v1/testing/attacks` - List attack types
- `POST /api/v1/testing/run-test?attack_type=port_scan&n_flows=100` - Run test
- `POST /api/v1/testing/run-suite` - Run full suite
- `GET /api/v1/testing/results?limit=20` - Get test results

### Dashboard
- `GET /api/v1/dashboard/overview` - Get complete dashboard data
- `GET /api/v1/dashboard/threat-map` - Get threat visualization data
- `WS /ws/dashboard` - WebSocket for real-time updates

## Directory Structure

```
ChakraVyuh-Version3/
├── requirements.txt                    # Python dependencies
├── venv/                               # Virtual environment
│
├── phase1_ml_detector/                 # Phase 1: ML Detector
│   ├── flow_preprocessor.py            # PCAP parsing & feature extraction
│   ├── network_autoencoder.py          # PyTorch autoencoder
│   ├── detector_trainer.py             # Training pipeline
│   ├── threat_detector.py              # Inference engine
│   ├── test_integration.py             # Integration tests
│   │
│   └── test_framework/
│       ├── payload_generator.py        # Attack payload generation
│       └── test_runner.py              # Test execution & tracking
│
├── backend_api/                        # FastAPI backend
│   └── main.py                         # REST API server
│
├── frontend_dashboard/                 # React frontend
│   ├── Dashboard.jsx                   # Main dashboard component
│   ├── Dashboard.css                   # Styling
│   ├── App.js                          # App wrapper
│   ├── index.js                        # React entry point
│   └── package.json                    # Dependencies
│
└── data/                               # Data directory
```

## Testing Attack Types

### 1. Port Scan (MEDIUM severity)
- **Signature**: Many flows, sequential ports, short duration
- **Detection**: Rapid port probing pattern
- **Expected rate**: 85-95%

### 2. DoS/DDoS Flood (CRITICAL severity)
- **Signature**: Huge packet counts, large byte volumes, fast pace
- **Detection**: Volumetric anomaly
- **Expected rate**: 95-99%

### 3. Brute Force (HIGH severity)
- **Signature**: Many flows same port, rapid attempts
- **Detection**: Connection rate anomaly
- **Expected rate**: 80-90%

### 4. Data Exfiltration (CRITICAL severity)
- **Signature**: Long duration, medium-large bytes, regular pattern
- **Detection**: Behavioral anomaly
- **Expected rate**: 70-85%

### 5. Command Injection (CRITICAL severity)
- **Signature**: Variable payload sizes, malformed requests
- **Detection**: Protocol anomaly
- **Expected rate**: 75-85%

### 6. Stealth Scanning (MEDIUM severity)
- **Signature**: Single-packet flows, fragmentation attempts
- **Detection**: Reconnaissance pattern
- **Expected rate**: 65-75%

## Performance Tuning

### For Detection Training:
```python
# In detector_trainer.py - adjust hyperparameters
trainer = DetectorTrainer(
    window_size=5,           # Flow window size
    latent_dim=16,           # Compress to 16D latent
    batch_size=32,           # Increase for speed
    learning_rate=0.001      # Adjust convergence
)
```

### For API Server:
- Increase Uvicorn workers: `--workers 4`
- Enable production mode: Remove `--reload`
- Use Gunicorn: `gunicorn -w 4 -b 0.0.0.0:8000 main:app`

### For Detector Threshold:
Modify in `threat_detector.py`:
```python
detector = ThreatDetector(
    checkpoint_path,
    threshold_percentile='p95'  # Change to p90, p99 as needed
)
```

## Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000
# Kill process if needed
taskkill /PID <pid> /F
```

### No Alerts Generated
```bash
# Verify detector loaded correctly
curl http://localhost:8000/api/v1/detector/stats

# Check test framework initialized
curl http://localhost:8000/api/v1/testing/attacks
```

### Dashboard Shows "Disconnected"
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check WebSocket connection
# Open browser DevTools -> Network -> WS tab
```

### Tests Show 0% Detection
1. Check detector threshold:
   ```bash
   curl http://localhost:8000/api/v1/detector/stats
   # Look for "threshold" value
   ```
2. Increase n_flows to 500+ for better statistics
3. Retrain detector with more epochs

## Advanced Features

### Export Test Results
```python
from backend_api.main import test_runner

results = test_runner.get_all_results()
test_runner.save_results(results)
```

### Custom Attack Patterns
```python
from phase1_ml_detector.test_framework.payload_generator import TestPayloadGenerator

gen = TestPayloadGenerator()
flows_df, name = gen.generate_port_scan(n_flows=500)
```

### Real-time Processing
```python
from phase1_ml_detector.threat_detector import ThreatDetector

detector = ThreatDetector('./checkpoints/detector_prod')

# Process flows one-by-one
alert = detector.process_flow({
    'src_ip': '192.168.1.100',
    'dst_ip': '10.0.0.50',
    # ... other fields ...
})

if alert:
    print(f"ALERT: {alert}")
```

## Next Steps

### Phase 2: Federated Learning
- Multi-node distributed training
- Privacy-preserving model updates
- Aggregation server

### Phase 3: Honeypot Deployment
- SSH honeypot on port 2222
- Trap controller with Docker
- Command execution simulation

### Phase 4: Auto-SOC
- MITRE ATT&CK mapping
- Threat intelligence reports
- Full end-to-end integration

## Support & Documentation

- Detector metrics: Check dashboard stats
- API documentation: Visit `http://localhost:8000/docs`
- Component docs: See individual module docstrings
- Test logs: Check `test_results/` directory

## License

ChakraVyuh v3.0 - Network Anomaly Detection System
