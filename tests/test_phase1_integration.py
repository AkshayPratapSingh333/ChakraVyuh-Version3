"""Phase 1 Integration Tests - ML Detector Foundation"""
import pytest
import numpy as np
from pathlib import Path

from src.preprocessing.flow_preprocessor import FlowPreprocessor
from src.models.isolation_forest_detector import IsolationForestDetector
from src.training.detector_trainer import DetectorTrainer
from src.inference.threat_detector import ThreatDetector


class TestFlowPreprocessor:
    """Test FlowPreprocessor data pipeline"""

    def test_load_csv(self, sample_flow_data, test_data_dir):
        """Test loading CSV flow data"""
        # Save sample data to CSV
        csv_path = test_data_dir / "flows.csv"
        sample_flow_data.to_csv(csv_path, index=False)
        
        preprocessor = FlowPreprocessor()
        df = preprocessor.load_csv(str(csv_path))
        
        assert len(df) == 100
        assert list(df.columns) == [
            "src_port", "dst_port", "packet_count", "byte_count",
            "duration_seconds", "protocol", "flags", "window_size"
        ]

    def test_normalize_features(self, sample_flow_data):
        """Test numeric feature normalization"""
        preprocessor = FlowPreprocessor()
        numeric_features = ["src_port", "dst_port", "packet_count", "byte_count", "duration_seconds", "window_size"]
        
        normalized = preprocessor.normalize_features(
            sample_flow_data,
            numeric_features,
            fit=True
        )
        
        # Check shape
        assert normalized.shape == (100, 6)
        
        # Check normalization bounds
        assert normalized.min() >= 0
        assert normalized.max() <= 1.0
        
        # Check params saved
        assert len(preprocessor.normalization_params) > 0

    def test_encode_categoricals(self, sample_flow_data):
        """Test categorical feature encoding"""
        preprocessor = FlowPreprocessor()
        categorical_features = {
            "protocol": ["tcp", "udp", "icmp", "igmp"],
            "flags": ["syn", "ack", "fin", "rst", "psh", "urg"]
        }
        
        encoded = preprocessor.encode_categoricals(
            sample_flow_data,
            categorical_features,
            fit=True
        )
        
        # Check shape
        assert encoded.shape[0] == 100
        assert encoded.shape[1] == 2  # protocol + flags
        
        # Check label encoders created
        assert len(preprocessor.label_encoders) == 2

    def test_get_tensor_output(self, sample_flow_data):
        """Test end-to-end preprocessing to tensor"""
        preprocessor = FlowPreprocessor()
        numeric_features = ["src_port", "dst_port", "packet_count", "byte_count", "duration_seconds", "window_size"]
        categorical_features = {
            "protocol": ["tcp", "udp", "icmp", "igmp"],
            "flags": ["syn", "ack", "fin", "rst", "psh", "urg"]
        }
        
        tensor = preprocessor.get_tensor_output(
            sample_flow_data,
            numeric_features,
            categorical_features,
            fit=True
        )
        
        # Check output shape [num_samples, num_features]
        assert tensor.shape[0] == 100
        assert tensor.shape[1] == 8  # 6 numeric + 2 categorical


class TestIsolationForestDetector:
    """Test Isolation Forest anomaly detector"""

    def test_detector_initialization(self):
        """Test detector creation"""
        detector = IsolationForestDetector(
            n_estimators=100,
            contamination=0.1,
            random_state=42
        )
        
        assert detector.n_estimators == 100
        assert detector.contamination == 0.1
        assert detector.is_fitted == False

    def test_fit(self):
        """Test fitting on normal data"""
        detector = IsolationForestDetector(contamination=0.1)
        X_train = np.random.randn(100, 8)
        
        summary = detector.fit(X_train)
        
        assert detector.is_fitted == True
        assert summary["num_samples"] == 100
        assert summary["num_features"] == 8
        assert summary["threshold"] is not None

    def test_predict(self):
        """Test anomaly prediction"""
        detector = IsolationForestDetector(contamination=0.1)
        X_train = np.random.randn(100, 8)
        detector.fit(X_train)
        
        X_test = np.random.randn(10, 8)
        result = detector.predict(X_test)
        
        assert "anomaly_scores" in result
        assert "is_anomaly" in result
        assert "confidence" in result
        assert len(result["anomaly_scores"]) == 10
        assert len(result["is_anomaly"]) == 10

    def test_anomaly_score(self):
        """Test anomaly score computation"""
        detector = IsolationForestDetector()
        X_train = np.random.randn(100, 8)
        detector.fit(X_train)
        
        X_test = np.random.randn(5, 8)
        scores = detector.anomaly_score(X_test)
        
        assert len(scores) == 5
        assert scores.dtype == np.float64

    def test_calibrate_threshold(self):
        """Test threshold calibration"""
        detector = IsolationForestDetector()
        X_train = np.random.randn(100, 8)
        detector.fit(X_train)
        
        old_threshold = detector.threshold
        detector.calibrate_threshold(X_train, percentile=10)
        
        assert detector.threshold != old_threshold


class TestDetectorTrainer:
    """Test training loop and checkpointing"""

    def test_trainer_initialization(self):
        """Test trainer setup"""
        detector = IsolationForestDetector()
        trainer = DetectorTrainer(detector, checkpoint_dir="tests/checkpoints")
        
        assert trainer.model is not None
        assert len(trainer.training_history) > 0

    def test_train(self):
        """Test training"""
        detector = IsolationForestDetector()
        trainer = DetectorTrainer(detector, checkpoint_dir="tests/checkpoints")
        
        X_train = np.random.randn(100, 8)
        history = trainer.train(X_train, contamination=0.1)
        
        assert "model_info" in history
        assert "training_summary" in history

    def test_save_load_model(self):
        """Test model saving and loading"""
        detector = IsolationForestDetector()
        trainer = DetectorTrainer(detector, checkpoint_dir="tests/checkpoints")
        
        X_train = np.random.randn(100, 8)
        trainer.train(X_train)
        
        # Save
        model_path = trainer.save_model("tests/checkpoints/test_model.pkl")
        assert Path(model_path).exists()
        
        # Load
        trainer.load_model(model_path)
        assert trainer.model.is_fitted == True


class TestThreatDetector:
    """Test inference and alert generation"""

    def test_detector_initialization(self):
        """Test detector initialization"""
        # First train and save a model
        detector_to_train = IsolationForestDetector()
        trainer = DetectorTrainer(detector_to_train, checkpoint_dir="tests/checkpoints")
        X_train = np.random.randn(100, 8)
        trainer.train(X_train)
        model_path = trainer.save_model("tests/checkpoints/threat_test_model.pkl")
        
        # Now test loading
        threat_detector = ThreatDetector(model_path, threshold_percentile=95)
        assert threat_detector.model is not None

    def test_detector_prediction(self):
        """Test threat detection on flows"""
        # Train a model first
        detector_to_train = IsolationForestDetector()
        trainer = DetectorTrainer(detector_to_train, checkpoint_dir="tests/checkpoints")
        X_train = np.random.randn(200, 8)
        trainer.train(X_train, contamination=0.1)
        model_path = trainer.save_model("tests/checkpoints/threat_pred_model.pkl")
        
        # Load and test
        threat_detector = ThreatDetector(model_path, threshold_percentile=95)
        threat_detector.calibrate_threshold(X_train[:100])
        
        assert threat_detector.threshold is not None
        
        X_test = np.random.randn(10, 8)
        result = threat_detector.predict(X_test)
        
        assert "anomaly_scores" in result
        assert "is_anomaly" in result
        assert "confidence" in result
        assert len(result["anomaly_scores"]) == 10

    def test_emit_alert(self):
        """Test alert generation"""
        detector_to_train = IsolationForestDetector()
        trainer = DetectorTrainer(detector_to_train, checkpoint_dir="tests/checkpoints")
        X_train = np.random.randn(100, 8)
        trainer.train(X_train)
        model_path = trainer.save_model("tests/checkpoints/threat_alert_model.pkl")
        
        threat_detector = ThreatDetector(model_path)
        threat_detector.calibrate_threshold(X_train)
        
        alert = threat_detector.emit_alert(
            src_ip="192.168.1.10",
            dst_ip="10.0.0.5",
            anomaly_score=0.8,
            confidence=0.95,
            origin="prod"
        )
        
        assert alert["src_ip"] == "192.168.1.10"
        assert alert["dst_ip"] == "10.0.0.5"
        assert alert["anomaly_score"] == 0.8
        assert alert["origin"] == "prod"


class TestPhase1Integration:
    """End-to-end Phase 1 integration test"""

    def test_full_pipeline(self, sample_flow_data):
        """Test complete Phase 1 pipeline: preprocess → train → infer"""
        # Step 1: Preprocess
        preprocessor = FlowPreprocessor()
        numeric_features = ["src_port", "dst_port", "packet_count", "byte_count", "duration_seconds", "window_size"]
        categorical_features = {
            "protocol": ["tcp", "udp", "icmp", "igmp"],
            "flags": ["syn", "ack", "fin", "rst", "psh", "urg"]
        }
        
        tensor_data = preprocessor.get_tensor_output(
            sample_flow_data,
            numeric_features,
            categorical_features,
            fit=True
        )
        
        assert tensor_data.shape == (100, 8)
        
        # Step 2: Train
        detector = IsolationForestDetector(contamination=0.1)
        trainer = DetectorTrainer(detector, checkpoint_dir="tests/checkpoints")
        history = trainer.train(tensor_data, contamination=0.1)
        
        assert "model_info" in history
        assert "training_summary" in history
        
        # Step 3: Save
        model_path = trainer.save_model("tests/checkpoints/phase1_test_model.pkl")
        
        # Step 4: Infer
        threat_detector = ThreatDetector(model_path, threshold_percentile=95)
        threat_detector.calibrate_threshold(tensor_data[:80])
        
        result = threat_detector.predict(tensor_data[:10])
        assert len(result["anomaly_scores"]) == 10
        assert result["threshold"] is not None
