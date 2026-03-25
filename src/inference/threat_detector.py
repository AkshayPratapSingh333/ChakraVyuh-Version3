"""
ThreatDetector: Load model, perform inference, compute anomaly scores, emit alerts
"""
import json
import joblib
from pathlib import Path
from typing import Optional, Dict, Any
import time

import numpy as np

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ThreatDetector:
    """Perform inference on flows and emit anomaly alerts"""

    def __init__(
        self,
        model_path: str,
        threshold_percentile: float = 95.0,
        min_confidence: float = 0.5,
    ):
        """
        Initialize threat detector.

        Args:
            model_path: Path to trained Isolation Forest model
            threshold_percentile: Percentile to use for threshold calibration
            min_confidence: Minimum confidence to emit alert [0, 1]
        """
        self.threshold_percentile = threshold_percentile
        self.min_confidence = min_confidence
        
        self.model = None
        self.threshold = None
        self.kafka_producer = None
        
        self.load_model(model_path)
        logger.info(f"ThreatDetector initialized: threshold_percentile={threshold_percentile}, "
                   f"min_confidence={min_confidence}")

    def load_model(self, model_path: str) -> None:
        """
        Load trained Isolation Forest model.

        Args:
            model_path: Path to model file (.pkl or .joblib)
        """
        logger.info(f"Loading model from {model_path}")
        
        self.model = joblib.load(model_path)
        self.threshold = self.model.threshold
        
        logger.info(f"Model loaded successfully. Threshold: {self.threshold:.6f}")

    def calibrate_threshold(self, normal_data: np.ndarray) -> None:
        """
        Calibrate anomaly threshold on normal traffic data.

        Args:
            normal_data: Normal flow data [num_samples, input_dim]
        """
        logger.info(f"Calibrating threshold on {len(normal_data)} normal flows")
        
        self.model.calibrate_threshold(normal_data, percentile=self.threshold_percentile)
        self.threshold = self.model.threshold
        
        logger.info(f"Threshold calibrated: {self.threshold:.6f} "
                   f"(using {self.threshold_percentile}th percentile)")

    def predict(self, flow_data: np.ndarray) -> Dict[str, Any]:
        """
        Perform inference on a single flow or batch of flows.

        Args:
            flow_data: Flow features [num_samples, input_dim] or [input_dim]

        Returns:
            Dict with anomaly scores, labels, and confidence
        """
        # Handle single sample
        if flow_data.ndim == 1:
            flow_data = flow_data.reshape(1, -1)

        result = self.model.predict(flow_data)
        
        return {
            "anomaly_scores": result["anomaly_scores"],
            "is_anomaly": result["is_anomaly"],
            "confidence": result["confidence"],
            "threshold": result["threshold"],
        }

    def compute_anomaly_score(self, flow_data: np.ndarray) -> np.ndarray:
        """
        Compute anomaly score for flows.

        Args:
            flow_data: Flow data [num_samples, input_dim]

        Returns:
            Anomaly scores [num_samples] (lower = more anomalous)
        """
        return self.model.anomaly_score(flow_data)

    def emit_alert(
        self,
        src_ip: str,
        dst_ip: str,
        anomaly_score: float,
        confidence: float,
        flow_data: Optional[np.ndarray] = None,
        alert_id: Optional[str] = None,
        origin: str = "prod",
    ) -> Dict[str, Any]:
        """
        Create alert event for anomalous flow.

        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address
            anomaly_score: Computed anomaly score
            confidence: Confidence level [0, 1]
            flow_data: Raw flow features (optional)
            alert_id: Unique alert ID (optional, will generate if not provided)
            origin: Alert origin ("prod" or "test")

        Returns:
            Alert event dict
        """
        alert_id = alert_id or f"{int(time.time() * 1000)}"
        
        alert = {
            "id": alert_id,
            "timestamp": time.time(),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "anomaly_score": float(anomaly_score),
            "confidence": float(confidence),
            "threshold": float(self.threshold) if self.threshold else None,
            "is_anomaly": bool(anomaly_score > self.threshold) if self.threshold else False,
            "origin": origin,
        }
        
        logger.info(f"Alert emitted: {src_ip} -> {dst_ip}, score={anomaly_score:.6f}, "
                   f"conf={confidence:.2f}, origin={origin}")
        
        return alert

    def save_predictions(self, predictions: list, filepath: str) -> None:
        """
        Save predictions to JSON file for debugging.

        Args:
            predictions: List of prediction dicts
            filepath: Path to save file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(predictions, f, indent=2)
        
        logger.info(f"Predictions saved to {filepath}")
