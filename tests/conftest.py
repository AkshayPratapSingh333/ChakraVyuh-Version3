"""conftest.py - Pytest fixtures for Phase 1-4 tests"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path


@pytest.fixture
def sample_flow_data():
    """Generate synthetic network flow data for testing"""
    np.random.seed(42)
    
    num_samples = 100
    
    data = {
        "src_port": np.random.randint(1024, 65535, num_samples),
        "dst_port": np.random.randint(1, 1024, num_samples),
        "packet_count": np.random.randint(1, 1000, num_samples),
        "byte_count": np.random.randint(100, 100000, num_samples),
        "duration_seconds": np.random.uniform(0.1, 100, num_samples),
        "protocol": np.random.choice(["tcp", "udp", "icmp"], num_samples),
        "flags": np.random.choice(["syn", "ack", "fin", "rst"], num_samples),
        "window_size": np.random.randint(512, 65535, num_samples),
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def synthetic_anomaly_data(sample_flow_data):
    """Generate anomalous flow data (synthetic attacks)"""
    anomalous = sample_flow_data.copy()
    
    # Mutate to create anomaly: extreme values
    anomalous.loc[0, "packet_count"] = 50000
    anomalous.loc[1, "byte_count"] = 900000
    anomalous.loc[2, "protocol"] = "igmp"  # Rare protocol
    
    return anomalous


@pytest.fixture
def preprocessor():
    """Initialize FlowPreprocessor"""
    from src.preprocessing.flow_preprocessor import FlowPreprocessor
    return FlowPreprocessor()


@pytest.fixture
def autoencoder():
    """Initialize NetworkAutoencoder"""
    from src.models.network_autoencoder import NetworkAutoencoder
    return NetworkAutoencoder(input_dim=8, hidden_dims=[128, 64, 32], latent_dim=16)


@pytest.fixture
def trainer(autoencoder):
    """Initialize DetectorTrainer"""
    from src.training.detector_trainer import DetectorTrainer
    return DetectorTrainer(autoencoder, device="cpu", checkpoint_dir="tests/checkpoints")


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary test data directory"""
    test_dir = Path("tests/test_data")
    test_dir.mkdir(exist_ok=True)
    return test_dir
