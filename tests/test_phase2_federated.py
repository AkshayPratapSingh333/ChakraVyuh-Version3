"""
Unit Tests for Phase 2: Federated Learning
Tests for nodes, server, trainer, and aggregation strategies.
"""

import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase2_federated.federated_node import FederatedNode
from phase2_federated.aggregation_server import AggregationServer
from phase2_federated.federated_trainer import FederatedTrainer
from phase2_federated.federated_config import FederatedConfig, AggregationStrategy


class TestFederatedNode:
    """Tests for FederatedNode."""
    
    def test_node_initialization(self):
        """Test node initialization."""
        node = FederatedNode("test_node", local_data_samples=100)
        
        assert node.node_id == "test_node"
        assert node.local_data_samples == 100
        assert node.local_X.shape == (100, 20)
        assert node.local_y.shape == (100,)
    
    def test_receive_global_model(self):
        """Test receiving global model."""
        node = FederatedNode("test_node")
        
        global_weights = {
            'weight1': np.random.randn(3, 3),
            'weight2': np.random.randn(3,)
        }
        
        node.receive_global_model(global_weights)
        
        assert 'weight1' in node.global_weights
        assert 'weight2' in node.global_weights
        assert np.array_equal(node.global_weights['weight1'], global_weights['weight1'])
    
    def test_train_local_model(self):
        """Test local training."""
        node = FederatedNode("test_node")
        node.global_weights = {
            'w1': np.random.randn(5, 5),
            'w2': np.random.randn(5,)
        }
        node.local_weights = {k: v.copy() for k, v in node.global_weights.items()}
        
        loss, accuracy = node.train_local_model(epochs=1)
        
        assert isinstance(loss, (float, np.floating))
        assert isinstance(accuracy, (float, np.floating))
        assert 0 <= accuracy <= 1
    
    def test_compute_weight_delta(self):
        """Test weight delta computation."""
        node = FederatedNode("test_node")
        node.global_weights = {
            'w1': np.ones((3, 3)),
            'w2': np.ones((3,))
        }
        node.local_weights = {
            'w1': np.ones((3, 3)) * 2,
            'w2': np.ones((3,)) * 2
        }
        
        delta = node.compute_weight_delta()
        
        assert np.allclose(delta['w1'], np.ones((3, 3)))
        assert np.allclose(delta['w2'], np.ones(3))
    
    def test_weight_clipping(self):
        """Test weight delta clipping."""
        node = FederatedNode("test_node")
        node.weight_delta = {
            'w1': np.ones((3, 3)) * 10,  # Will be clipped
        }
        
        node.clip_weight_delta(max_norm=1.0)
        
        clipped = np.linalg.norm(node.weight_delta['w1'])
        assert clipped <= 1.1  # Allow small numerical error


class TestAggregationServer:
    """Tests for AggregationServer."""
    
    def test_server_initialization(self):
        """Test server initialization."""
        server = AggregationServer()
        
        assert len(server.global_weights) > 0
        assert server.current_round == 0
    
    def test_register_nodes(self):
        """Test node registration."""
        server = AggregationServer()
        
        server.register_node("node_0", 1000)
        server.register_node("node_1", 1500)
        
        assert len(server.node_weights) == 2
        assert server.node_weights["node_0"] == 1000
        assert server.node_weights["node_1"] == 1500
    
    def test_receive_weight_delta(self):
        """Test receiving weight delta."""
        server = AggregationServer()
        
        delta = {'w1': np.random.randn(5, 5), 'w2': np.random.randn(5,)}
        server.receive_weight_delta("node_0", delta)
        
        assert "node_0" in server.collected_deltas
        assert np.array_equal(server.collected_deltas["node_0"]['w1'], delta['w1'])
    
    def test_fedavg_aggregation(self):
        """Test FedAvg aggregation."""
        server = AggregationServer()
        initial_w = server.global_weights.copy()
        
        # Create deltas
        delta1 = {k: np.ones_like(v) * 0.1 for k, v in initial_w.items()}
        delta2 = {k: np.ones_like(v) * 0.2 for k, v in initial_w.items()}
        
        server.receive_weight_delta("node_0", delta1)
        server.receive_weight_delta("node_1", delta2)
        
        updated, metrics = server.aggregate_weights(strategy="fedavg")
        
        assert metrics['strategy'] == 'fedavg'
        assert metrics['num_nodes'] == 2
        assert len(updated) == len(initial_w)
    
    def test_weighted_avg_aggregation(self):
        """Test weighted average aggregation."""
        server = AggregationServer()
        server.register_node("node_0", 1000)
        server.register_node("node_1", 2000)
        
        initial_w = server.global_weights.copy()
        
        delta1 = {k: np.ones_like(v) * 0.1 for k, v in initial_w.items()}
        delta2 = {k: np.ones_like(v) * 0.2 for k, v in initial_w.items()}
        
        server.receive_weight_delta("node_0", delta1)
        server.receive_weight_delta("node_1", delta2)
        
        updated, metrics = server.aggregate_weights(strategy="weighted_avg")
        
        assert metrics['strategy'] == 'weighted_avg'
    
    def test_clear_deltas(self):
        """Test clearing collected deltas."""
        server = AggregationServer()
        
        delta = {'w1': np.random.randn(5, 5)}
        server.receive_weight_delta("node_0", delta)
        
        assert len(server.collected_deltas) == 1
        
        server.clear_collected_deltas()
        
        assert len(server.collected_deltas) == 0
        assert server.current_round == 1


class TestFederatedTrainer:
    """Tests for FederatedTrainer."""
    
    def test_trainer_initialization(self):
        """Test trainer initialization."""
        config = FederatedConfig(num_rounds=2, num_nodes=2)
        trainer = FederatedTrainer(config)
        
        assert len(trainer.nodes) == 2
        assert trainer.best_accuracy >= 0
    
    def test_distribute_global_model(self):
        """Test model distribution."""
        config = FederatedConfig(num_rounds=1, num_nodes=2)
        trainer = FederatedTrainer(config)
        
        trainer.distribute_global_model()
        
        # Check all nodes have global weights
        for node in trainer.nodes.values():
            assert len(node.global_weights) > 0
    
    def test_train_round(self):
        """Test single training round."""
        config = FederatedConfig(num_rounds=1, num_nodes=2, local_epochs=1)
        trainer = FederatedTrainer(config)
        
        metrics = trainer.train_round()
        
        assert 'round' in metrics
        assert 'avg_loss' in metrics
        assert 'avg_accuracy' in metrics
        assert 'node_metrics' in metrics
    
    def test_full_training(self):
        """Test full training loop."""
        config = FederatedConfig(
            num_rounds=2,
            num_nodes=2,
            local_epochs=1,
            aggregation_strategy=AggregationStrategy.FED_AVG
        )
        trainer = FederatedTrainer(config)
        
        round_metrics = trainer.train()
        
        assert len(round_metrics) == 2
        assert all('avg_accuracy' in m for m in round_metrics)
    
    def test_get_summary(self):
        """Test training summary."""
        config = FederatedConfig(num_rounds=2, num_nodes=2, local_epochs=1)
        trainer = FederatedTrainer(config)
        
        trainer.train()
        summary = trainer.get_summary()
        
        assert 'num_rounds' in summary
        assert 'best_accuracy' in summary
        assert 'best_round' in summary
        assert summary['num_rounds'] == 2


class TestFederatedConfig:
    """Tests for FederatedConfig."""
    
    def test_config_initialization(self):
        """Test config initialization."""
        config = FederatedConfig(
            num_rounds=5,
            num_nodes=3,
            aggregation_strategy=AggregationStrategy.MEDIAN
        )
        
        assert config.num_rounds == 5
        assert config.num_nodes == 3
        assert config.aggregation_strategy == AggregationStrategy.MEDIAN
    
    def test_config_validation(self):
        """Test config validation."""
        with pytest.raises(ValueError):
            FederatedConfig(num_rounds=0)
        
        with pytest.raises(ValueError):
            FederatedConfig(learning_rate=-0.1)
    
    def test_config_to_dict(self):
        """Test config serialization."""
        config = FederatedConfig(num_rounds=3, num_nodes=2)
        config_dict = config.to_dict()
        
        assert config_dict['num_rounds'] == 3
        assert config_dict['num_nodes'] == 2
        assert isinstance(config_dict['aggregation_strategy'], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
