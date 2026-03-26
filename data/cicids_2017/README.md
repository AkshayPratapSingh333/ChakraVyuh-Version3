# CICIDS 2017 Network Intrusion Dataset

## Dataset Files (Already Available ✓)

Your dataset has been split by day/attack type:

```
data/cicids_2017/raw/
├── Monday-WorkingHours.pcap_ISCX.csv              (Monday normal + attacks)
├── Tuesday-WorkingHours.pcap_ISCX.csv             (Tuesday normal + attacks)
├── Wednesday-workingHours.pcap_ISCX.csv           (Wednesday normal + attacks)
├── Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
├── Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
├── Friday-WorkingHours-Morning.pcap_ISCX.csv
├── Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
└── Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

**Total Size**: ~843 MB (split across 8 files)

---

## Dataset Structure

### Features
- **Total Features**: 83 engineered network flow statistics
- **Selected Features**: 20 optimized for autoencoder anomaly detection
- **Records**: ~2.8M network flows (combined)

### Labels
- **BENIGN**: Normal traffic (Monday, Tuesday, Wednesday)
- **DDoS**: Distributed Denial of Service (Friday afternoon)
- **PortScan**: Port scanning activity (Friday afternoon)
- **SSH-Bruteforce**: SSH brute force attacks
- **FTP-Bruteforce**: FTP brute force attacks
- **Web Attack**: Web-based attacks (Thursday morning)
- **Infiltration**: Internal infiltration (Thursday afternoon)

---

## Quick Start

### Option 1: Load All Files (Combine All Days)
```python
from src.preprocessing.cicids_loader import CICIDSLoader

loader = CICIDSLoader("data/cicids_2017/raw")

# Load normal traffic from all days
X_normal, y_normal = loader.load_dataset(attack_type='BENIGN', sample_size=100000)
print(f"Loaded: {X_normal.shape}")  # (100000, 20) features
```

### Option 2: Load Specific Day/Attack
```python
# Load only Friday DDoS attacks
X_ddos, y_ddos = loader.load_dataset(filename='Friday-DDoS')

# Load only Thursday Web Attacks
X_webattack, y_webattack = loader.load_dataset(filename='Thursday-WebAttacks')

# Load Monday only (mixed normal + attacks)
X_monday, y_monday = loader.load_dataset(filename='Monday')
```

### Option 3: Load by Attack Type (Across All Files)
```python
# DDoS attacks from all files
X_ddos_all, y_ddos_all = loader.load_dataset(attack_type='DDoS')

# All attacks (anything non-BENIGN)
X_attacks, y_attacks = loader.load_dataset(attack_type=None, sample_size=50000)
```

---

## Available Day Files

```python
loader = CICIDSLoader("data/cicids_2017/raw")
loader.get_available_days()

# Output:
# Available CICIDS files:
# ✓ Monday                  - Monday-WorkingHours.pcap_ISCX.csv (...)
# ✓ Tuesday                 - Tuesday-WorkingHours.pcap_ISCX.csv (...)
# ✓ Wednesday               - Wednesday-workingHours.pcap_ISCX.csv (...)
# ✓ Thursday-WebAttacks     - Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv (...)
# ✓ Thursday-Infiltration   - Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv (...)
# ✓ Friday-Morning          - Friday-WorkingHours-Morning.pcap_ISCX.csv (...)
# ✓ Friday-PortScan         - Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv (...)
# ✓ Friday-DDoS             - Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv (...)
```

---

## Integration with Autoencoder

```python
from src.preprocessing.cicids_loader import CICIDSLoader

loader = CICIDSLoader("data/cicids_2017/raw")

# Load normal traffic for training
X_normal, y_normal = loader.load_dataset(attack_type='BENIGN', sample_size=100000)

# Prepare sequences (5-frame windows)
X_seq = loader.prepare_for_autoencoder(X_normal, seq_length=5)

# Train model
from phase1_ml_detector.network_autoencoder import NetworkAutoencoder

model = NetworkAutoencoder(input_dim=20, seq_length=5, latent_dim=8)
model.train(X_seq, epochs=20, batch_size=32)

# Test on DDoS attacks
X_ddos, y_ddos = loader.load_dataset(filename='Friday-DDoS', sample_size=10000)
X_ddos_seq = loader.prepare_for_autoencoder(X_ddos, seq_length=5)

# Detect anomalies
detections = model.predict(X_ddos_seq)
```

---

## Performance Notes

- **First Load**: Processes CSV files (2-5 minutes for all files)
- **Cached Load**: Subsequent loads use numpy arrays (~1 second)
- **Memory**: Single file ~150-300 MB in RAM
- **Feature Scaling**: StandardScaler normalization (0-mean, unit-variance)

---

## Feature Mapping

**20 Selected Features** (from 83 total):
1. Total Fwd Packets
2. Total Backward Packets
3. Total Length of Fwd Packets
4. Total Length of Bwd Packets
5. Fwd Packet Length Mean
6. Bwd Packet Length Mean
7. Fwd Packet Length Std
8. Bwd Packet Length Std
9. Flow Bytes/s
10. Flow Packets/s
11. Fwd Packets/s
12. Bwd Packets/s
13. Fwd IAT Mean
14. Fwd IAT Std
15. Bwd IAT Mean
16. Bwd IAT Std
17. Packet Length Mean
18. Packet Length Std
19. Average Packet Size
20. Avg Fwd Segment Size

---

## Related Files
- **Loader**: `src/preprocessing/cicids_loader.py`
- **Training**: `phase1_ml_detector/detector_trainer.py`
- **Federated Config**: `phase2_federated/federated_config.py`

