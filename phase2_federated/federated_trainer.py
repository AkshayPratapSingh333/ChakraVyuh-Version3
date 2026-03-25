"""
Federated Trainer: Orchestrates federated learning training cycles.
Manages communication between nodes and aggregation server.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np

from .federated_node import FederatedNode
from .aggregation_server import AggregationServer
from .federated_config import FederatedConfig, AggregationStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FederatedTrainer:
    """
    Orchestrator for federated learning training.
    Manages nodes, server, and coordinates training rounds.
    """
    
    def __init__(self, config: FederatedConfig):
        """
        Initialize federated trainer.
        
        Args:
            config: FederatedConfig instance
        """
        self.config = config
        
        # Initialize server
        self.server = AggregationServer(
            checkpoint_dir=config.checkpoint_dir
        )
        
        # Initialize nodes
        self.nodes: Dict[str, FederatedNode] = {}
        self._init_nodes()
        
        # Training metrics
        self.round_metrics: List[Dict[str, Any]] = []
        self.best_accuracy = 0.0
        self.best_round = 0
        
        logger.info(
            f"FederatedTrainer initialized: {len(self.nodes)} nodes, "
            f"{config.num_rounds} rounds"
        )
    
    def _init_nodes(self):
        """Initialize federated nodes."""
        for i in range(self.config.num_nodes):
            node_id = f"node_{i}"
            num_samples = 1000 + np.random.randint(0, 1000)
            
            node = FederatedNode(
                node_id=node_id,
                local_data_samples=num_samples,
                feature_dim=20
            )
            
            self.nodes[node_id] = node
            self.server.register_node(node_id, num_samples)
        
        logger.info(f"Initialized {len(self.nodes)} nodes")
    
    def distribute_global_model(self):
        """Send global model to all nodes."""
        global_weights = self.server.get_global_model()
        
        for node in self.nodes.values():
            node.receive_global_model(global_weights)
        
        logger.info(f"Distributed global model to {len(self.nodes)} nodes")
    
    def train_round(self) -> Dict[str, Any]:
        """
        Execute one federated training round.
        
        Returns:
            Round metrics dictionary
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"FEDERATED TRAINING ROUND {self.config.num_rounds}")
        logger.info(f"{'='*60}\n")
        
        # Step 1: Distribute global model
        logger.info("Step 1: Distributing global model to nodes...")
        self.distribute_global_model()
        
        # Step 2: Local training on each node
        logger.info("\nStep 2: Nodes training locally...")
        node_metrics = {}
        
        for node_id, node in self.nodes.items():
            loss, accuracy = node.train_local_model(
                epochs=self.config.local_epochs
            )
            node_metrics[node_id] = {
                'loss': loss,
                'accuracy': accuracy,
                'num_samples': node.local_data_samples
            }
        
        # Step 3: Compute weight deltas
        logger.info("\nStep 3: Nodes computing weight deltas...")
        for node in self.nodes.values():
            delta = node.compute_weight_delta()
            
            # Apply privacy mechanisms
            if self.config.clip_weights:
                node.clip_weight_delta(self.config.weight_clip_norm)
            
            if self.config.differential_privacy:
                node.add_differential_privacy(
                    epsilon=self.config.dp_epsilon,
                    delta=self.config.dp_delta
                )
        
        # Step 4: Send deltas to server
        logger.info("\nStep 4: Nodes sending weight deltas to server...")
        for node_id, node in self.nodes.items():
            self.server.receive_weight_delta(node_id, node.weight_delta)
        
        # Step 5: Server aggregation
        logger.info("\nStep 5: Server aggregating weight updates...")
        strategy = self.config.aggregation_strategy.value
        aggregated_weights, agg_metrics = self.server.aggregate_weights(
            strategy=strategy,
            min_nodes=self.config.min_nodes_for_round
        )
        
        # Step 6: Reset for next round
        logger.info("\nStep 6: Resetting for next round...")
        self.server.clear_collected_deltas()
        for node in self.nodes.values():
            node.reset_for_next_round()
        
        # Compile round metrics
        round_metrics = {
            'round': self.config.num_rounds,
            'timestamp': datetime.now().isoformat(),
            'node_metrics': node_metrics,
            'aggregation_metrics': agg_metrics,
            'server_stats': self.server.get_statistics(),
        }
        
        # Calculate averages
        avg_loss = np.mean([m['loss'] for m in node_metrics.values()])
        avg_accuracy = np.mean([m['accuracy'] for m in node_metrics.values()])
        
        round_metrics['avg_loss'] = avg_loss
        round_metrics['avg_accuracy'] = avg_accuracy
        
        # Track best accuracy
        if avg_accuracy > self.best_accuracy:
            self.best_accuracy = avg_accuracy
            self.best_round = self.config.num_rounds
            round_metrics['is_best'] = True
            
            # Save checkpoint
            if self.config.num_rounds % self.config.save_every_n_rounds == 0:
                self.server.save_checkpoint("best")
        
        self.round_metrics.append(round_metrics)
        
        logger.info(f"\nRound {self.config.num_rounds} Summary:")
        logger.info(f"  Avg Loss:     {avg_loss:.4f}")
        logger.info(f"  Avg Accuracy: {avg_accuracy:.4%}")
        logger.info(f"  Best Accuracy: {self.best_accuracy:.4%} (round {self.best_round})")
        
        return round_metrics
    
    def train(self) -> List[Dict[str, Any]]:
        """
        Execute full federated training loop.
        
        Returns:
            List of round metrics
        """
        logger.info(
            f"\nStarting federated training: "
            f"{self.config.num_rounds} rounds, "
            f"{self.config.num_nodes} nodes, "
            f"{self.config.local_epochs} local epochs"
        )
        
        for round_num in range(self.config.num_rounds):
            self.config.num_rounds = round_num + 1
            round_metrics = self.train_round()
        
        logger.info(f"\n{'='*60}")
        logger.info("FEDERATED TRAINING COMPLETED")
        logger.info(f"{'='*60}")
        logger.info(f"Best Accuracy: {self.best_accuracy:.4%} (round {self.best_round})")
        
        return self.round_metrics
    
    def get_final_model(self) -> Dict[str, np.ndarray]:
        """
        Get final trained global model.
        
        Returns:
            Global model weights
        """
        return self.server.get_global_model()
    
    def save_training_report(self, output_file: str = "federated_training_report.json"):
        """
        Save training report to JSON file.
        
        Args:
            output_file: Output filename
        """
        report = {
            'config': self.config.to_dict(),
            'total_rounds': len(self.round_metrics),
            'best_accuracy': float(self.best_accuracy),
            'best_round': self.best_round,
            'final_server_stats': self.server.get_statistics(),
            'round_metrics': [
                {
                    **m,
                    # Convert numpy arrays to lists for JSON serialization
                    'node_metrics': {
                        node_id: {
                            **node_m,
                            'loss': float(node_m['loss']),
                            'accuracy': float(node_m['accuracy'])
                        }
                        for node_id, node_m in m['node_metrics'].items()
                    },
                    'avg_loss': float(m['avg_loss']),
                    'avg_accuracy': float(m['avg_accuracy']),
                }
                for m in self.round_metrics
            ]
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Saved training report to {output_path}")
        
        return str(output_path)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get training summary."""
        if not self.round_metrics:
            return {}
        
        all_accuracies = [m['avg_accuracy'] for m in self.round_metrics]
        all_losses = [m['avg_loss'] for m in self.round_metrics]
        
        return {
            'num_rounds': len(self.round_metrics),
            'num_nodes': len(self.nodes),
            'best_accuracy': float(self.best_accuracy),
            'best_round': self.best_round,
            'final_accuracy': float(all_accuracies[-1] if all_accuracies else 0),
            'final_loss': float(all_losses[-1] if all_losses else 0),
            'avg_accuracy_improvement': float(
                (self.best_accuracy - all_accuracies[0]) / all_accuracies[0] * 100
                if all_accuracies and all_accuracies[0] > 0
                else 0
            ),
            'aggregation_strategy': self.config.aggregation_strategy.value,
        }
