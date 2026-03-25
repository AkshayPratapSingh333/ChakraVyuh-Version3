# Phase 2: Federated Learning System

**Privacy-preserving, distributed network anomaly detection model training.**

## Overview

Phase 2 implements a complete **Federated Learning** framework for ChakraVyuh, enabling multiple organizations (banks, ISPs, healthcare facilities) to collaboratively train an anomaly detection model **without sharing raw network traffic data**.

### Key Principles

✅ **Privacy-First**: Raw data never leaves local systems  
✅ **Collaborative**: Multiple nodes contribute to a shared global model  
✅ **Secure**: Weight updates only (no raw traffic)  
✅ **Scalable**: Works with any number of participating nodes  
✅ **Robust**: Multiple aggregation strategies (FedAvg, median, etc.)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│             FEDERATED LEARNING SYSTEM                       │
└─────────────────────────────────────────────────────────────┘

    Node 1 (Bank)           Node 2 (ISP)         Node 3 (Hospital)
    ┌──────────┐           ┌──────────┐         ┌──────────┐
    │Local Data│           │Local Data│         │Local Data│
    │ 1000 pts │           │ 1500 pts │         │ 800 pts  │
    └────┬─────┘           └────┬─────┘         └────┬─────┘
         │                      │                     │
         │ 1. Receive Global Model
         │ 2. Train Locally (2 epochs)
         │ 3. Compute Weight Delta
         │ 4. Send Delta (no data!)
         │                      │                     │
         └──────────────────────┼─────────────────────┘
                                │
                         ┌──────▼──────┐
                         │  Aggregation│
                         │   Server    │
                         └──────┬──────┘
                                │
                         5. Aggregate (FedAvg)
                         6. Update Global Model
                                │
                 ┌───────────────┼───────────────┐
                 │                               │
           Broadcast Global Model    Repeat (Next Round)
                 ▼

    Training Loop: Multiple Rounds
    ✓ Better model with each round
    ✓ All data stays private
```

---

## Components

### 1. **FederatedNode** (`federated_node.py`)
Local trainer that operates on a single organization's data.

**Features:**
- Local model training (SGD on local data)
- Weight delta computation
- Optional weight clipping
- Optional differential privacy
- Data statistics tracking

**Usage:**
```python
from phase2_federated.federated_node import FederatedNode

node = FederatedNode("bank_node", local_data_samples=1000)
node.receive_global_model(global_weights)
loss, accuracy = node.train_local_model(epochs=2)
delta = node.compute_weight_delta()
```

### 2. **AggregationServer** (`aggregation_server.py`)
Central server that aggregates weight updates from nodes.

**Aggregation Strategies:**
- **FedAvg**: Simple averaging (default)
- **Weighted Avg**: Weight by data volume
- **Median**: Robust to outliers
- **Trimmed Mean**: Remove extreme values

**Usage:**
```python
from phase2_federated.aggregation_server import AggregationServer

server = AggregationServer()
server.register_node("bank", 1000)
server.register_node("isp", 1500)

server.receive_weight_delta("bank", delta1)
server.receive_weight_delta("isp", delta2)

updated_weights, metrics = server.aggregate_weights(strategy="fedavg")
```

### 3. **FederatedTrainer** (`federated_trainer.py`)
Orchestrates the entire federated learning process.

**Responsibilities:**
- Initialize nodes and server
- Coordinate training rounds
- Distribute/collect model updates
- Track metrics and reports
- Save checkpoints

**Usage:**
```python
from phase2_federated.federated_config import FederatedConfig
from phase2_federated.federated_trainer import FederatedTrainer

config = FederatedConfig(
    num_rounds=5,
    num_nodes=3,
    local_epochs=2,
    aggregation_strategy="fedavg"
)

trainer = FederatedTrainer(config)
round_metrics = trainer.train()
summary = trainer.get_summary()
```

### 4. **FederatedConfig** (`federated_config.py`)
Configuration management for federated training.

**Key Parameters:**
- `num_rounds`: Total training rounds
- `num_nodes`: Number of participating nodes
- `local_epochs`: Local training epochs per node
- `aggregation_strategy`: Strategy for combining updates
- `differential_privacy`: Enable DP noise
- `clip_weights`: Enable weight clipping (outlier robustness)

---

## Training Flow

### Round-by-Round Process

1. **Distribution Phase**
   - Server sends current global model to all nodes
   
2. **Local Training Phase**
   - Each node trains locally on its data
   - Computes weight updates
   
3. **Aggregation Phase**
   - Nodes send weight deltas to server (no raw data)
   - Server aggregates using configured strategy
   - Server updates global model
   
4. **Next Round**
   - Repeat with updated global model

### Privacy Mechanisms

**Weight Clipping**
```python
# Limit L2 norm of weight updates to prevent poisoning
config.clip_weights = True
config.weight_clip_norm = 1.0
```

**Differential Privacy**
```python
# Add Laplace noise to weight updates
config.differential_privacy = True
config.dp_epsilon = 1.0  # Privacy budget
config.dp_delta = 0.01   # Failure probability
```

---

## Running the System

### 1. Basic Federated Training

```bash
cd phase2_federated
python -c "from demo_federated import demo_basic_federated_learning; demo_basic_federated_learning()"
```

### 2. Compare Aggregation Strategies

```bash
python -c "from demo_federated import demo_aggregation_strategies; demo_aggregation_strategies()"
```

### 3. With Differential Privacy

```bash
python -c "from demo_federated import demo_differential_privacy; demo_differential_privacy()"
```

### 4. Run All Demos

```bash
python demo_federated.py
```

### 5. Run Unit Tests

```bash
pytest test_federated.py -v
```

---

## Configuration Examples

### Example 1: Basic Setup (3 nodes, 5 rounds)
```python
from phase2_federated.federated_config import FederatedConfig

config = FederatedConfig(
    num_rounds=5,
    num_nodes=3,
    local_epochs=2,
    learning_rate=0.01,
)
```

### Example 2: Privacy-Focused
```python
config = FederatedConfig(
    num_rounds=5,
    num_nodes=3,
    local_epochs=2,
    differential_privacy=True,
    dp_epsilon=1.0,
    dp_delta=0.01,
    clip_weights=True,
    weight_clip_norm=1.0,
    aggregation_strategy=AggregationStrategy.MEDIAN,  # Also robust
)
```

### Example 3: Large-Scale Deployment
```python
config = FederatedConfig(
    num_rounds=10,
    num_nodes=20,
    local_epochs=5,
    aggregation_strategy=AggregationStrategy.WEIGHTED_AVG,  # Account for data imbalance
    min_nodes_for_round=15,  # Require 15+ nodes
    save_every_n_rounds=2,
)
```

---

## Output & Metrics

### Training Report (`federated_training_report.json`)

```json
{
  "config": {
    "num_rounds": 5,
    "num_nodes": 3,
    "local_epochs": 2,
    "aggregation_strategy": "fedavg"
  },
  "best_accuracy": 0.92,
  "best_round": 5,
  "round_metrics": [
    {
      "round": 1,
      "avg_loss": 0.45,
      "avg_accuracy": 0.78,
      "node_metrics": {...},
      "aggregation_metrics": {...}
    },
    ...
  ]
}
```

### Key Metrics

- **Local Loss/Accuracy**: Per-node training metrics
- **Aggregation Time**: Time to aggregate updates
- **Accuracy Improvement**: % improvement over rounds
- **Best Accuracy**: Highest accuracy achieved
- **Parameter Count**: Total model parameters

---

## Integration with Phase 1 & 3

### Phase 1 Integration
- Use **FederatedTrainer** to train Phase 1 ML detector across organizations
- Each organization contributes local network flows
- Final global model detects anomalies for all participants

### Phase 3 Integration  
- Honeypots generate attack data locally
- Federated training improves detector with real attacks
- No honeypot data shared between organizations

### Backend API Integration
```python
# Planned endpoints:
POST /api/v1/federated/start-training
GET  /api/v1/federated/trainer-status
GET  /api/v1/federated/round-metrics/{round}
POST /api/v1/federated/node-register
```

---

## Performance Considerations

### Computational Cost
- **Per Round**: ~O(n_nodes × local_epochs × data_size)
- **Aggregation**: ~O(n_nodes × parameter_count)
- **Network**: Single weight delta per node per round

### Convergence
- Typically converges in 5-20 rounds depending on:
  - Data distribution across nodes
  - Local training epochs
  - Learning rate
  - Model complexity

### Scalability
- ✅ Tested with up to 20 nodes
- ✅ Works with varying data sizes
- ✅ Robust to node dropout (via aggregation strategies)

---

## Troubleshooting

### 1. Training Not Converging
- Increase `local_epochs`
- Reduce `learning_rate`
- Increase `num_rounds`

### 2. High Variance Between Nodes
- Use `aggregation_strategy=MEDIAN` for robustness
- Use `weighted_avg` if data is imbalanced
- Increase `min_nodes_for_round`

### 3. Privacy Concerns
- Enable `differential_privacy=True`
- Adjust `dp_epsilon` (lower = more private, noisier)
- Enable `clip_weights=True`

---

## Files

```
phase2_federated/
├── __init__.py                 # Package init
├── federated_config.py         # Configuration classes
├── federated_node.py           # Local trainer node
├── aggregation_server.py       # Central aggregation server
├── federated_trainer.py        # Training orchestrator
├── demo_federated.py           # Demo simulations
├── test_federated.py           # Unit tests
├── README.md                   # This file
└── demo_results/               # Generated reports
    ├── federated_training_basic.json
    └── strategy_comparison.json
```

---

## Next Steps

1. ✅ **Phase 2 Core**: Federated learning framework (DONE)
2. 🔄 **Backend Integration**: REST API for nodes
3. 🔄 **Dashboard UI**: Monitor federated training
4. 🔄 **Real Network Data**: Connect to Phase 1 detector
5. 🔄 **Production Deployment**: Multi-org cluster

---

## References

- **FedAvg**: [Communication-Efficient Learning of Deep Networks from Decentralized Data](https://arxiv.org/abs/1602.05629)
- **Differential Privacy**: [The Algorithmic Foundations of Differential Privacy](https://arxiv.org/pdf/1407.2638.pdf)
- **Federated Learning**: [Federated Machine Learning: Concept and Applications](https://arxiv.org/abs/1902.04885)

---

## License

Part of ChakraVyuh - Network Anomaly Detection System (March 2026)
