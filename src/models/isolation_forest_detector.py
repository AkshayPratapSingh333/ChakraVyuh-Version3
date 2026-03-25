"""
IsolationForestDetector: Sklearn-based anomaly detection using Isolation Forest
No DLL dependencies, pure Python, works on Windows without issues
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class IsolationForestDetector:
    """
    Isolation Forest anomaly detector for network flows.
    Detects anomalies by isolating outliers in the feature space.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.1,
        random_state: int = 42,
        n_jobs: int = -1,
    ):
        """
        Initialize Isolation Forest detector.

        Args:
            n_estimators: Number of isolation trees
            contamination: Expected fraction of anomalies in dataset [0, 0.5]
            random_state: Random seed for reproducibility
            n_jobs: Number of parallel jobs (-1 = use all cores)
        """
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.n_jobs = n_jobs
        
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=n_jobs,
            verbose=0,
        )
        
        self.is_fitted = False
        self.threshold = None
        
        logger.info(
            f"Initialized IsolationForestDetector: n_estimators={n_estimators}, "
            f"contamination={contamination}, random_state={random_state}"
        )

    def fit(self, train_data: np.ndarray) -> Dict[str, Any]:
        """
        Fit Isolation Forest on normal/benign network flows.

        Args:
            train_data: Training data [num_samples, num_features]

        Returns:
            Training summary dict
        """
        logger.info(f"Fitting IsolationForest on {len(train_data)} normal flows")
        
        self.model.fit(train_data)
        self.is_fitted = True
        
        # Compute anomaly scores on training data
        scores = self.model.score_samples(train_data)
        
        # Set threshold at 95th percentile (scores are negative offset_)
        self.threshold = np.percentile(scores, 5)  # 5th percentile = 95% normal
        
        summary = {
            "num_samples": len(train_data),
            "num_features": train_data.shape[1],
            "threshold": float(self.threshold),
            "mean_score": float(np.mean(scores)),
            "std_score": float(np.std(scores)),
            "min_score": float(np.min(scores)),
            "max_score": float(np.max(scores)),
        }
        
        logger.info(f"Training complete. Threshold: {self.threshold:.6f}, "
                   f"Mean score: {summary['mean_score']:.6f}")
        
        return summary

    def predict(self, flow_data: np.ndarray) -> Dict[str, Any]:
        """
        Predict anomaly status and compute scores.

        Args:
            flow_data: Flow data [num_samples, num_features] or [num_features]

        Returns:
            Dict with anomaly_scores, is_anomaly, confidence, threshold
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Handle single sample
        if flow_data.ndim == 1:
            flow_data = flow_data.reshape(1, -1)
        
        # Get anomaly scores (lower = more anomalous)
        scores = self.model.score_samples(flow_data)
        
        # Get binary predictions (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(flow_data)
        is_anomaly = predictions == -1
        
        # Compute confidence as normalized distance from threshold
        distances = np.abs(scores - self.threshold)
        confidence = np.clip(distances / (np.abs(self.threshold) + 1e-6), 0, 1)
        
        return {
            "anomaly_scores": scores,
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "threshold": self.threshold,
        }

    def anomaly_score(self, flow_data: np.ndarray) -> np.ndarray:
        """
        Compute anomaly scores for flows.

        Args:
            flow_data: Flow data [num_samples, num_features]

        Returns:
            Anomaly scores [num_samples] (lower = more anomalous)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        return self.model.score_samples(flow_data)

    def calibrate_threshold(self, normal_data: np.ndarray, percentile: float = 5.0) -> float:
        """
        Calibrate anomaly threshold on normal data.

        Args:
            normal_data: Normal flow data [num_samples, num_features]
            percentile: Percentile to use as threshold (lower = stricter)

        Returns:
            New threshold value
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        scores = self.model.score_samples(normal_data)
        self.threshold = np.percentile(scores, percentile)
        
        logger.info(f"Threshold recalibrated to {self.threshold:.6f} "
                   f"(using {percentile}th percentile)")
        
        return self.threshold

    def get_model_info(self) -> Dict[str, Any]:
        """Get model configuration and stats."""
        return {
            "model_type": "IsolationForest",
            "n_estimators": self.n_estimators,
            "contamination": self.contamination,
            "random_state": self.random_state,
            "is_fitted": self.is_fitted,
            "threshold": float(self.threshold) if self.threshold is not None else None,
        }
