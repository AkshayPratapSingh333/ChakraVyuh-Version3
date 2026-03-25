"""
Aggregation Server: Central server that aggregates weight updates from nodes.
Implements multiple aggregation strategies (FedAvg, weighted averaging, etc.)
"""

import numpy as np
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AggregationServer:
    """
    Central aggregation server for federated learning.
    Collects weight deltas from nodes and aggregates them.
    """
    
    def __init__(
        self,
        model_name: str = "anomaly_detector",
        feature_dim: int = 20,
        checkpoint_dir: str = "./federated_checkpoints"
    ):
        """
        Initialize aggregation server.
        
        Args:
            model_name: Name of the model being trained
            feature_dim: Dimensionality of model features
            checkpoint_dir: Directory to save checkpoints
        """
        self.model_name = model_name
        self.feature_dim = feature_dim
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Global model
        self._init_global_model()
        
        # Aggregation state
        self.current_round = 0
        self.node_weights: Dict[str, float] = {}  # Node ID -> data weight
        self.collected_deltas: Dict[str, Dict[str, np.ndarray]] = {}
        
        # Metrics
        self.aggregation_times: List[float] = []
        self.round_metrics: List[Dict[str, Any]] = []
        
        logger.info(
            f"AggregationServer initialized: {model_name}, "
            f"checkpoint_dir={checkpoint_dir}"
        )
    
    def _init_global_model(self):
        """Initialize global model weights."""
        # Simulate model with layers
        self.global_weights = {
            'layer1': np.random.randn(self.feature_dim, 64) * 0.01,
            'bias1': np.random.randn(64) * 0.01,
            'layer2': np.random.randn(64, 32) * 0.01,
            'bias2': np.random.randn(32) * 0.01,
            'output': np.random.randn(32, 2) * 0.01,
            'bias_output': np.random.randn(2) * 0.01,
        }
        logger.info(
            f"Initialized global model: {list(self.global_weights.keys())}"
        )
    
    def register_node(
        self,
        node_id: str,
        num_samples: int
    ):
        """
        Register a node with the server.
        
        Args:
            node_id: Unique node identifier
            num_samples: Number of data samples on this node
        """
        self.node_weights[node_id] = num_samples
        logger.info(
            f"Registered node {node_id} with {num_samples} samples"
        )
    
    def receive_weight_delta(
        self,
        node_id: str,
        weight_delta: Dict[str, np.ndarray]
    ):
        """
        Receive weight delta from a node.
        
        Args:
            node_id: Node that sent the delta
            weight_delta: Weight update dictionary
        """
        self.collected_deltas[node_id] = weight_delta
        logger.info(
            f"Received weight delta from {node_id} "
            f"({len(weight_delta)} matrices)"
        )
    
    def aggregate_weights(
        self,
        strategy: str = "fedavg",
        min_nodes: int = 1
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Aggregate weight deltas from nodes using specified strategy.
        
        Args:
            strategy: Aggregation strategy (fedavg, weighted_avg, median, etc.)
            min_nodes: Minimum nodes required for aggregation
            
        Returns:
            Tuple of (updated_weights, metrics)
        """
        import time
        start_time = time.time()
        
        if len(self.collected_deltas) < min_nodes:
            logger.warning(
                f"Insufficient nodes: {len(self.collected_deltas)} < {min_nodes}"
            )
            return self.global_weights, {'status': 'insufficient_nodes'}
        
        logger.info(
            f"Aggregating {len(self.collected_deltas)} node updates using {strategy}"
        )
        
        if strategy == "fedavg":
            updated_weights = self._aggregate_fedavg()
        elif strategy == "weighted_avg":
            updated_weights = self._aggregate_weighted_avg()
        elif strategy == "median":
            updated_weights = self._aggregate_median()
        elif strategy == "trimmed_mean":
            updated_weights = self._aggregate_trimmed_mean()
        else:
            logger.warning(f"Unknown strategy {strategy}, using fedavg")
            updated_weights = self._aggregate_fedavg()
        
        # Update global weights
        self.global_weights = updated_weights
        
        elapsed_time = time.time() - start_time
        self.aggregation_times.append(elapsed_time)
        
        metrics = {
            'strategy': strategy,
            'num_nodes': len(self.collected_deltas),
            'aggregation_time': elapsed_time,
            'num_parameters': sum(w.size for w in self.global_weights.values()),
        }
        
        logger.info(
            f"Aggregation completed in {elapsed_time:.3f}s "
            f"({len(self.collected_deltas)} nodes)"
        )
        
        return updated_weights, metrics
    
    def _aggregate_fedavg(self) -> Dict[str, np.ndarray]:
        """
        FedAvg: Simple averaging of weight deltas.
        """
        n_nodes = len(self.collected_deltas)
        aggregated = {}
        
        # Get all keys from first delta
        first_node = list(self.collected_deltas.keys())[0]
        
        for key in self.collected_deltas[first_node].keys():
            # Collect all deltas for this key
            deltas = [
                self.collected_deltas[node_id][key]
                for node_id in self.collected_deltas.keys()
            ]
            
            # Average and apply to global weights
            avg_delta = np.mean(deltas, axis=0)
            aggregated[key] = self.global_weights[key] + avg_delta
        
        return aggregated
    
    def _aggregate_weighted_avg(self) -> Dict[str, np.ndarray]:
        """
        Weighted averaging: weight deltas by data volume.
        """
        total_samples = sum(self.node_weights.values())
        aggregated = {}
        
        first_node = list(self.collected_deltas.keys())[0]
        
        for key in self.collected_deltas[first_node].keys():
            weighted_delta = np.zeros_like(self.global_weights[key])
            
            for node_id, weight_delta in self.collected_deltas.items():
                weight = self.node_weights.get(node_id, 1) / total_samples
                weighted_delta += weight_delta[key] * weight
            
            aggregated[key] = self.global_weights[key] + weighted_delta
        
        return aggregated
    
    def _aggregate_median(self) -> Dict[str, np.ndarray]:
        """
        Median aggregation: robust to outliers.
        """
        aggregated = {}
        first_node = list(self.collected_deltas.keys())[0]
        
        for key in self.collected_deltas[first_node].keys():
            deltas = np.array([
                self.collected_deltas[node_id][key]
                for node_id in self.collected_deltas.keys()
            ])
            
            median_delta = np.median(deltas, axis=0)
            aggregated[key] = self.global_weights[key] + median_delta
        
        return aggregated
    
    def _aggregate_trimmed_mean(
        self,
        trim_fraction: float = 0.1
    ) -> Dict[str, np.ndarray]:
        """
        Trimmed mean aggregation: remove extreme values.
        
        Args:
            trim_fraction: Fraction of extreme values to trim
        """
        aggregated = {}
        first_node = list(self.collected_deltas.keys())[0]
        
        for key in self.collected_deltas[first_node].keys():
            deltas = np.array([
                self.collected_deltas[node_id][key]
                for node_id in self.collected_deltas.keys()
            ])
            
            trimmed = np.mean(
                np.ma.masked_where(
                    np.abs(deltas - np.mean(deltas, axis=0)) >
                    trim_fraction * np.std(deltas, axis=0),
                    deltas
                ),
                axis=0
            )
            aggregated[key] = self.global_weights[key] + trimmed
        
        return aggregated
    
    def clear_collected_deltas(self):
        """Clear collected deltas for next round."""
        self.collected_deltas = {}
        self.current_round += 1
        logger.info(f"Cleared deltas for round {self.current_round}")
    
    def save_checkpoint(self, tag: str = "latest"):
        """
        Save global model checkpoint.
        
        Args:
            tag: Checkpoint tag/name
        """
        checkpoint_path = self.checkpoint_dir / f"global_model_round{self.current_round}_{tag}.npy"
        
        np.save(checkpoint_path, self.global_weights)
        logger.info(f"Saved checkpoint: {checkpoint_path}")
        
        return str(checkpoint_path)
    
    def load_checkpoint(self, checkpoint_path: str):
        """
        Load global model checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file
        """
        self.global_weights = np.load(checkpoint_path, allow_pickle=True).item()
        logger.info(f"Loaded checkpoint: {checkpoint_path}")
    
    def get_global_model(self) -> Dict[str, np.ndarray]:
        """
        Get current global model weights (for distribution to nodes).
        
        Returns:
            Global weights dictionary
        """
        return {k: v.copy() for k, v in self.global_weights.items()}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            'current_round': self.current_round,
            'num_registered_nodes': len(self.node_weights),
            'num_collected_deltas': len(self.collected_deltas),
            'avg_aggregation_time': float(np.mean(self.aggregation_times)) if self.aggregation_times else 0.0,
            'total_aggregation_time': float(np.sum(self.aggregation_times)),
            'num_parameters': sum(w.size for w in self.global_weights.values()),
        }
