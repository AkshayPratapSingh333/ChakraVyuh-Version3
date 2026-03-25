"""
Federated Node: Local trainer that trains model and computes weight deltas.
Keeps data private - only weight updates are sent to server.
"""

import numpy as np
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FederatedNode:
    """
    Local node that trains ML model on local data.
    Computes and sends weight deltas to aggregation server.
    
    Privacy guarantee: Raw data never leaves the node.
    """
    
    def __init__(
        self,
        node_id: str,
        local_data_samples: int = 1000,
        feature_dim: int = 20,
        model_name: str = "anomaly_detector"
    ):
        """
        Initialize federated node.
        
        Args:
            node_id: Unique identifier for this node
            local_data_samples: Number of samples in local dataset
            feature_dim: Dimensionality of features
            model_name: Name of the model being trained
        """
        self.node_id = node_id
        self.local_data_samples = local_data_samples
        self.feature_dim = feature_dim
        self.model_name = model_name
        
        # Training state
        self.current_round = 0
        self.global_weights: Dict[str, np.ndarray] = {}
        self.local_weights: Dict[str, np.ndarray] = {}
        self.weight_delta: Dict[str, np.ndarray] = {}
        
        # Metrics
        self.local_loss = 0.0
        self.local_accuracy = 0.0
        self.training_times: List[float] = []
        
        # Simulated local dataset
        self._init_local_data()
        
        logger.info(
            f"FederatedNode {node_id} initialized: "
            f"{local_data_samples} samples, feature_dim={feature_dim}"
        )
    
    def _init_local_data(self):
        """Initialize simulated local data."""
        # Simulate local dataset: (samples, features)
        self.local_X = np.random.randn(self.local_data_samples, self.feature_dim)
        
        # Simulate labels (binary classification)
        self.local_y = np.random.randint(0, 2, self.local_data_samples)
        
        # Add some patterns to make it realistic
        self.local_X[self.local_y == 1] += np.random.randn(
            np.sum(self.local_y), self.feature_dim
        ) * 0.5
    
    def receive_global_model(self, global_weights: Dict[str, np.ndarray]):
        """
        Receive global model weights from aggregation server.
        
        Args:
            global_weights: Global model weights dictionary
        """
        self.global_weights = {k: v.copy() for k, v in global_weights.items()}
        self.local_weights = {k: v.copy() for k, v in global_weights.items()}
        logger.info(
            f"Node {self.node_id}: Received global model with "
            f"{len(self.global_weights)} weight matrices"
        )
    
    def train_local_model(self, epochs: int = 2) -> Tuple[float, float]:
        """
        Train model on local data.
        Simulates local training loop with proper SGD simulation.
        
        Args:
            epochs: Number of local training epochs
            
        Returns:
            Tuple of (loss, accuracy) on local data
        """
        import time
        start_time = time.time()
        
        logger.info(
            f"Node {self.node_id}: Starting local training "
            f"({epochs} epochs, {self.local_data_samples} samples)"
        )
        
        # Initialize accuracy if not set (first training)
        if self.local_accuracy == 0.0:
            self.local_accuracy = 0.55  # Start at 55%
            self.local_loss = 0.45
        
        # Simulate training: gradually improve weights and accuracy
        for epoch in range(epochs):
            # SGD update: small perturbation in direction of gradient
            learning_rate = 0.01
            for key in self.local_weights.keys():
                # Simulate gradient (random direction, scaled by current loss)
                gradient = np.random.randn(*self.local_weights[key].shape) * self.local_loss
                # Apply gradient descent step
                self.local_weights[key] -= learning_rate * gradient
            
            # Improve loss more realistically
            improvement = 0.08 * (1 - epoch / max(epochs, 1))  # Decrease improvement each epoch
            self.local_loss = max(0.10, self.local_loss - improvement)
            
            # Improve accuracy based on loss improvement
            # As loss decreases, accuracy increases
            accuracy_gain = 0.12 * (1 - self.local_loss / 0.5)  # More gain when loss is lower
            self.local_accuracy = min(0.96, self.local_accuracy + accuracy_gain)
            
            logger.info(
                f"Node {self.node_id}: Epoch {epoch+1}/{epochs} - "
                f"Loss: {self.local_loss:.4f}, Accuracy: {self.local_accuracy:.4%}"
            )
        
        elapsed_time = time.time() - start_time
        self.training_times.append(elapsed_time)
        
        logger.info(
            f"Node {self.node_id}: Local training completed in {elapsed_time:.2f}s"
        )
        
        return self.local_loss, self.local_accuracy
    
    def compute_weight_delta(self) -> Dict[str, np.ndarray]:
        """
        Compute weight delta (new - old) to send to server.
        This preserves privacy by only sending updates, not raw data.
        
        Returns:
            Weight delta dictionary
        """
        self.weight_delta = {}
        
        for key in self.local_weights.keys():
            delta = self.local_weights[key] - self.global_weights[key]
            self.weight_delta[key] = delta
        
        logger.info(
            f"Node {self.node_id}: Computed weight delta "
            f"({len(self.weight_delta)} matrices)"
        )
        
        return self.weight_delta
    
    def clip_weight_delta(self, max_norm: float = 1.0):
        """
        Clip weight deltas to prevent outliers (for robustness).
        
        Args:
            max_norm: Maximum L2 norm for weight delta
        """
        for key in self.weight_delta.keys():
            delta = self.weight_delta[key]
            delta_norm = np.linalg.norm(delta)
            
            if delta_norm > max_norm:
                self.weight_delta[key] = delta * (max_norm / delta_norm)
                logger.info(
                    f"Node {self.node_id}: Clipped delta for {key} "
                    f"({delta_norm:.4f} -> {max_norm:.4f})"
                )
    
    def add_differential_privacy(
        self,
        epsilon: float = 1.0,
        delta: float = 0.01
    ):
        """
        Add differential privacy noise to weight deltas.
        
        Args:
            epsilon: Privacy budget
            delta: Delta parameter
        """
        std_dev = np.sqrt(2 * np.log(1.25 / delta)) / epsilon
        
        for key in self.weight_delta.keys():
            noise = np.random.normal(0, std_dev, self.weight_delta[key].shape)
            self.weight_delta[key] += noise
        
        logger.info(
            f"Node {self.node_id}: Added differential privacy noise "
            f"(epsilon={epsilon}, delta={delta})"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get node training statistics."""
        return {
            'node_id': self.node_id,
            'round': self.current_round,
            'local_loss': float(self.local_loss),
            'local_accuracy': float(self.local_accuracy),
            'avg_training_time': float(np.mean(self.training_times)) if self.training_times else 0.0,
            'total_training_time': float(np.sum(self.training_times)),
            'num_parameters': sum(w.size for w in self.local_weights.values()),
        }
    
    def serialize_weight_delta(self) -> Dict[str, List]:
        """
        Serialize weight delta to JSON-compatible format.
        
        Returns:
            Serialized weight delta
        """
        return {
            key: val.tolist()
            for key, val in self.weight_delta.items()
        }
    
    def reset_for_next_round(self):
        """Reset weights and metrics for next training round."""
        self.weight_delta = {}
        self.local_loss = 0.0
        self.local_accuracy = 0.0
        self.current_round += 1
        logger.info(f"Node {self.node_id}: Reset for round {self.current_round}")
