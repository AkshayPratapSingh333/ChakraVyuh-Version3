"""
DetectorTrainer: Train Isolation Forest anomaly detector on normal network flows
"""
import json
import joblib
from pathlib import Path
from typing import Dict

import numpy as np

from ..models.isolation_forest_detector import IsolationForestDetector
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DetectorTrainer:
    """Train IsolationForestDetector on normal flows"""

    def __init__(
        self,
        model: IsolationForestDetector = None,
        checkpoint_dir: str = "models/checkpoints",
    ):
        """
        Initialize trainer.

        Args:
            model: IsolationForestDetector instance (optional, will create if None)
            checkpoint_dir: Directory to save checkpoints
        """
        self.model = model if model is not None else IsolationForestDetector()
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.training_history = {
            "model_info": {},
            "training_summary": {},
        }

        logger.info(f"DetectorTrainer initialized")

    def train(
        self,
        train_data: np.ndarray,
        contamination: float = 0.1,
    ) -> Dict:
        """
        Train Isolation Forest on normal network flows.

        Args:
            train_data: Training data [num_samples, input_dim]
            contamination: Expected fraction of anomalies [0, 0.5]

        Returns:
            Training summary dict
        """
        logger.info(
            f"Starting Isolation Forest training: num_samples={len(train_data)}, "
            f"num_features={train_data.shape[1]}, contamination={contamination}"
        )

        self.model.contamination = contamination
        
        # Train the model
        summary = self.model.fit(train_data)
        
        # Store history
        self.training_history["model_info"] = self.model.get_model_info()
        self.training_history["training_summary"] = summary

        logger.info(f"Training complete. Threshold: {summary['threshold']:.6f}")

        return self.training_history

    def save_history(self, filepath: str) -> None:
        """Save training history to JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(self.training_history, f, indent=2)
        
        logger.info(f"Training history saved to {filepath}")

    def save_model(self, filepath: str) -> str:
        """
        Save model to file using joblib.

        Args:
            filepath: Path to save model

        Returns:
            Path to saved model
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(self.model, filepath)
        logger.info(f"Model saved: {filepath}")
        return str(filepath)

    def load_model(self, filepath: str) -> None:
        """
        Load model from file using joblib.

        Args:
            filepath: Path to model file
        """
        self.model = joblib.load(filepath)
        logger.info(f"Model loaded: {filepath}")
