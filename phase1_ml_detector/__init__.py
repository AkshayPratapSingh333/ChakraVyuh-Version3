"""
Phase 1: ML Detector Foundation
Autoencoder-based anomaly detection for network flows
"""

from .flow_preprocessor import FlowPreprocessor
from .network_autoencoder import NetworkAutoencoder
from .detector_trainer import DetectorTrainer
from .threat_detector import ThreatDetector, AlertEvent, ThreatDetectorAPI

__all__ = [
    'FlowPreprocessor',
    'NetworkAutoencoder',
    'DetectorTrainer',
    'ThreatDetector',
    'AlertEvent',
    'ThreatDetectorAPI'
]

__version__ = '1.0.0'
