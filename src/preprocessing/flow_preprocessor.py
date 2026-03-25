"""
Flow Preprocessor: Parse PCAP/CSV flows, normalize features, encode categoricals, output tensors
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, LabelEncoder

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FlowPreprocessor:
    """Preprocess network flow data for ML model ingestion"""

    def __init__(self):
        """Initialize preprocessor with feature extraction and normalization."""
        self.features: List[str] = []
        self.numeric_features: List[str] = []
        self.categorical_features: Dict[str, List[str]] = {}
        
        self.scaler = MinMaxScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        
        self.normalization_params: Dict[str, any] = {}
        self.is_fitted = False

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load network flows from CSV file.
        
        Args:
            csv_path: Path to CSV file
        
        Returns:
            DataFrame with flow data
        """
        logger.info(f"Loading flows from CSV: {csv_path}")
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} flows from {csv_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise

    def normalize_features(
        self,
        data: pd.DataFrame,
        numeric_features: List[str],
        fit: bool = True
    ) -> np.ndarray:
        """
        Normalize numeric features using min-max scaling.
        
        Args:
            data: Input DataFrame
            numeric_features: List of numeric feature names
            fit: If True, fit scaler on data; else use existing fit
        
        Returns:
            Normalized numpy array
        """
        logger.info(f"Normalizing {len(numeric_features)} numeric features")
        
        X = data[numeric_features].values.astype(np.float32)
        
        if fit:
            X_normalized = self.scaler.fit_transform(X)
            self.normalization_params = {
                "min": self.scaler.data_min_.tolist(),
                "max": self.scaler.data_max_.tolist(),
                "scale": self.scaler.scale_.tolist(),
            }
        else:
            X_normalized = self.scaler.transform(X)
        
        logger.info(f"Normalization complete. Min={X_normalized.min():.4f}, Max={X_normalized.max():.4f}")
        return X_normalized

    def encode_categoricals(
        self,
        data: pd.DataFrame,
        categorical_features: Dict[str, List[str]],
        fit: bool = True
    ) -> np.ndarray:
        """
        Encode categorical features using label encoding.
        
        Args:
            data: Input DataFrame
            categorical_features: Dict mapping feature name to possible values
            fit: If True, fit encoders on data; else use existing fit
        
        Returns:
            Encoded numpy array
        """
        logger.info(f"Encoding {len(categorical_features)} categorical features")
        
        encoded_data = []
        
        for feature, values in categorical_features.items():
            if feature not in data.columns:
                logger.warning(f"Feature {feature} not found in data, skipping")
                continue
            
            if fit:
                encoder = LabelEncoder()
                encoder.fit(values)
                self.label_encoders[feature] = encoder
            else:
                encoder = self.label_encoders[feature]
            
            # Encode, handling unknown values as 0
            encoded = data[feature].map(lambda x: encoder.transform([x])[0] if x in values else 0)
            encoded_data.append(encoded.values.reshape(-1, 1))
        
        if encoded_data:
            result = np.concatenate(encoded_data, axis=1).astype(np.float32)
            logger.info(f"Encoding complete. Shape: {result.shape}")
            return result
        else:
            logger.warning("No categorical features encoded")
            return np.array([]).reshape(len(data), 0)

    def get_tensor_output(
        self,
        data: pd.DataFrame,
        numeric_features: List[str],
        categorical_features: Dict[str, List[str]],
        fit: bool = True
    ) -> np.ndarray:
        """
        Preprocess flow data and return as combined tensor.
        
        Args:
            data: Input DataFrame with flow features
            numeric_features: List of numeric feature columns
            categorical_features: Dict of categorical feature columns
            fit: If True, fit scalers/encoders; else use existing
        
        Returns:
            Combined normalized tensor [num_samples, num_features]
        """
        logger.info(f"Processing {len(data)} flows into tensor format")
        
        self.numeric_features = numeric_features
        self.categorical_features = categorical_features
        
        # Normalize numeric features
        numeric_normalized = self.normalize_features(data, numeric_features, fit=fit)
        
        # Encode categorical features
        categorical_encoded = self.encode_categoricals(data, categorical_features, fit=fit)
        
        # Concatenate
        if categorical_encoded.size > 0:
            tensor = np.concatenate([numeric_normalized, categorical_encoded], axis=1)
        else:
            tensor = numeric_normalized
        
        logger.info(f"Tensor output shape: {tensor.shape}")
        self.is_fitted = fit or self.is_fitted
        
        return tensor

    def save_params(self, filepath: str) -> None:
        """Save normalization/encoding parameters for later use."""
        params = {
            "normalization": self.normalization_params,
            "label_encoders": {
                name: dict(zip(encoder.classes_, encoder.transform(encoder.classes_)))
                for name, encoder in self.label_encoders.items()
            },
        }
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(params, f, indent=2)
        
        logger.info(f"Normalization parameters saved to {filepath}")

    def load_params(self, filepath: str) -> None:
        """Load normalization/encoding parameters from file."""
        with open(filepath, "r") as f:
            params = json.load(f)
        
        # Restore normalization params
        self.normalization_params = params.get("normalization", {})
        
        # Restore label encoders
        for name, mapping in params.get("label_encoders", {}).items():
            encoder = LabelEncoder()
            # Fit on the classes (keys of mapping)
            encoder.fit(list(mapping.keys()))
            self.label_encoders[name] = encoder
        
        logger.info(f"Normalization parameters loaded from {filepath}")
