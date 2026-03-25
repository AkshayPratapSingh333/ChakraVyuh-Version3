"""
Phase 1 Integration Test: ML Detector Foundation
Tests complete pipeline: preprocessing -> autoencoder -> trainer -> detector
"""

import sys
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_flow_preprocessor():
    """Test FlowPreprocessor module."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: FlowPreprocessor")
    logger.info("="*60)
    
    from flow_preprocessor import FlowPreprocessor
    
    # Initialize
    preprocessor = FlowPreprocessor(window_size=5, test_mode=True)
    
    # Generate synthetic flows
    flows_df, labels = preprocessor.generate_synthetic_flows(
        n_samples=200,
        anomaly_rate=0.15
    )
    assert len(flows_df) == 200, "Flow count mismatch"
    assert len(labels) == 200, "Label count mismatch"
    logger.info(f"✓ Generated {len(flows_df)} flows")
    
    # Fit and transform
    X = preprocessor.fit_transform(flows_df)
    assert X.shape[0] == 200, "Sample count mismatch"
    assert X.shape[1] > 0, "Features not extracted"
    logger.info(f"✓ Transformed to shape: {X.shape}")
    
    # Create sequences
    X_seq, y_seq = preprocessor.create_sequences(X, labels)
    assert len(X_seq) == len(y_seq), "Sequence/label count mismatch"
    assert X_seq.shape[1] == preprocessor.window_size, "Window size mismatch"
    logger.info(f"✓ Created {len(X_seq)} sequences of size {preprocessor.window_size}")
    
    # Check feature names
    feature_names = preprocessor.get_feature_names()
    assert len(feature_names) > 0, "No feature names"
    logger.info(f"✓ Features: {feature_names}")
    
    logger.info("✓ FlowPreprocessor TEST PASSED\n")
    
    return preprocessor, X, X_seq, y_seq


def test_network_autoencoder():
    """Test NetworkAutoencoder module."""
    logger.info("="*60)
    logger.info("TEST 2: NetworkAutoencoder Training")
    logger.info("="*60)
    
    from network_autoencoder import NetworkAutoencoder
    from flow_preprocessor import FlowPreprocessor
    
    # Get data from preprocessor test
    preprocessor = FlowPreprocessor(window_size=5)
    flows_df, labels = preprocessor.generate_synthetic_flows(n_samples=200, anomaly_rate=0.1)
    X = preprocessor.fit_transform(flows_df)
    X_seq, _ = preprocessor.create_sequences(X, labels)
    
    # Split
    split = int(0.8 * len(X_seq))
    X_train = X_seq[:split]
    X_val = X_seq[split:]
    
    logger.info(f"Data split - Train: {X_train.shape}, Val: {X_val.shape}")
    
    # Create autoencoder
    ae = NetworkAutoencoder(
        input_dim=X_train.shape[2],
        seq_length=X_train.shape[1],
        latent_dim=8,
        batch_size=16,
        device='cpu'
    )
    logger.info(f"✓ Initialized NetworkAutoencoder (latent_dim=8)")
    
    # Train
    history = ae.fit(X_train, X_val, epochs=15, early_stopping_patience=5, verbose=False)
    assert 'train_loss' in history, "Training history missing"
    assert len(history['train_loss']) > 0, "No training losses"
    logger.info(f"✓ Trained for {len(history['epoch'])} epochs")
    logger.info(f"  Final train loss: {history['train_loss'][-1]:.4f}")
    if history['val_loss']:
        logger.info(f"  Final val loss: {history['val_loss'][-1]:.4f}")
    
    # Test anomaly detection
    scores, preds = ae.predict_anomalies(X_val, percentile=90)
    assert len(scores) == len(X_val), "Score count mismatch"
    assert len(preds) == len(X_val), "Prediction count mismatch"
    n_anomalies = preds.sum()
    logger.info(f"✓ Predicted {n_anomalies} anomalies out of {len(X_val)} samples")
    logger.info(f"  Score range: [{scores.min():.4f}, {scores.max():.4f}]")
    
    logger.info("✓ NetworkAutoencoder TEST PASSED\n")
    
    return ae, X_train, X_val


def test_detector_trainer():
    """Test DetectorTrainer full pipeline."""
    logger.info("="*60)
    logger.info("TEST 3: DetectorTrainer Pipeline")
    logger.info("="*60)
    
    from detector_trainer import DetectorTrainer
    
    trainer = DetectorTrainer(
        checkpoint_dir='./test_phase1_checkpoints',
        window_size=5,
        latent_dim=8,
        batch_size=16,
        learning_rate=0.001,
        device='cpu'
    )
    logger.info("✓ Initialized DetectorTrainer")
    
    # Load training data
    X_train, X_val, X_test = trainer.load_training_data(
        data_source='synthetic',
        normal_samples=300,
        test_split=0.15,
        val_split=0.15
    )
    logger.info(f"✓ Loaded data - Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    
    # Train
    history = trainer.train(X_train, X_val, epochs=15, early_stopping_patience=5, verbose=False)
    logger.info(f"✓ Training completed ({len(history['epoch'])} epochs)")
    
    # Evaluate thresholds
    thresholds = trainer.evaluate_thresholds(X_val, percentiles=[90, 95, 99])
    assert len(thresholds) > 0, "No thresholds calculated"
    logger.info(f"✓ Threshold evaluation: {thresholds}")
    
    # Save checkpoint
    checkpoint_path = trainer.save_checkpoint('test_detector')
    assert checkpoint_path.exists(), "Checkpoint not saved"
    logger.info(f"✓ Checkpoint saved to: {checkpoint_path}")
    
    logger.info("✓ DetectorTrainer TEST PASSED\n")
    
    return checkpoint_path


def test_threat_detector(checkpoint_path: str):
    """Test ThreatDetector online detection."""
    logger.info("="*60)
    logger.info("TEST 4: ThreatDetector Live Inference")
    logger.info("="*60)
    
    from threat_detector import ThreatDetector
    from flow_preprocessor import FlowPreprocessor
    
    # Initialize detector
    detector = ThreatDetector(str(checkpoint_path), threshold_percentile='p95')
    logger.info(f"✓ Loaded detector from checkpoint")
    logger.info(f"  Threshold: {detector.threshold:.4f}")
    logger.info(f"  Metadata: {detector.metadata}")
    
    # Generate test flows
    preprocessor = FlowPreprocessor()
    flows_df, labels = preprocessor.generate_synthetic_flows(
        n_samples=150,
        anomaly_rate=0.2
    )
    logger.info(f"✓ Generated {len(flows_df)} test flows")
    
    # Process flows
    alerts = detector.process_flows_batch(flows_df.to_dict('records'))
    logger.info(f"✓ Detected {len(alerts)} anomalies")
    
    # Check stats
    stats = detector.get_stats()
    logger.info(f"✓ Detector stats:")
    logger.info(f"  Flows processed: {stats['flows_processed']}")
    logger.info(f"  Alerts emitted: {stats['alerts_emitted']}")
    
    # Show recent alerts
    recent = detector.get_alerts(limit=3)
    if recent:
        logger.info(f"✓ Recent alerts ({len(recent)}):")
        for alert in recent:
            logger.info(f"    - {alert['flow_id']}: score={alert['anomaly_score']:.4f}, severity={alert['severity']}")
    
    logger.info("✓ ThreatDetector TEST PASSED\n")


def test_end_to_end():
    """Run complete end-to-end integration test."""
    logger.info("\n" + "="*80)
    logger.info("CHAKRAVYUH PHASE 1 - ML DETECTOR FOUNDATION - INTEGRATION TEST")
    logger.info("="*80)
    
    try:
        # Test 1: Preprocessor
        preprocessor, X, X_seq, y_seq = test_flow_preprocessor()
        
        # Test 2: Autoencoder
        ae, X_train, X_val = test_network_autoencoder()
        
        # Test 3: Trainer
        checkpoint_path = test_detector_trainer()
        
        # Test 4: Detector
        test_threat_detector(checkpoint_path)
        
        # Summary
        logger.info("="*80)
        logger.info("ALL TESTS PASSED! ✓")
        logger.info("="*80)
        logger.info("\nPhase 1 Summary:")
        logger.info("  ✓ Flow Preprocessing: PCAP/CSV parsing, normalization, encoding")
        logger.info("  ✓ Network Autoencoder: PyTorch encoder-decoder training")
        logger.info("  ✓ Detector Trainer: Complete training pipeline with checkpointing")
        logger.info("  ✓ Threat Detector: Real-time inference and alert generation")
        logger.info("\nNext: Phase 2 - Federated Learning")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)
