"""Serialization utilities for model checkpoints and weight deltas"""
import pickle
from pathlib import Path
from typing import Any, Dict


def save_checkpoint(obj: Any, filepath: str) -> None:
    """
    Save object (model, weights, etc.) to disk using pickle.
    
    Args:
        obj: Object to serialize
        filepath: Path to save file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_checkpoint(filepath: str) -> Any:
    """
    Load pickled object from disk.
    
    Args:
        filepath: Path to checkpoint file
    
    Returns:
        Deserialized object
    """
    with open(filepath, "rb") as f:
        return pickle.load(f)


def compute_weight_delta(old_weights: Dict[str, Any], new_weights: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute weight delta (new - old) for federated learning.
    
    Args:
        old_weights: Previous weights dict
        new_weights: Updated weights dict
    
    Returns:
        Delta dict with same structure as input
    """
    delta = {}
    for key in new_weights.keys():
        if key in old_weights:
            delta[key] = new_weights[key] - old_weights[key]
        else:
            delta[key] = new_weights[key]
    return delta
