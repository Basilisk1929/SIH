"""Machine Learning models for cybercrime anomaly detection and mule identification."""

from typing import Dict, List
import numpy as np


class MuleDetectorModel:
    """Heuristic and ensemble anomaly detection model for financial mule accounts.

    Evaluates:
    - Inflow-to-outflow time delta (Rapid pass-through velocity)
    - Balance retention ratio (Mule accounts retain near-zero balance)
    - Fan-out ratio (Single credit split into multiple downstream debits)
    - Device and IP sharing entropy
    """

    def __init__(self, risk_threshold: float = 0.75):
        self.risk_threshold = risk_threshold

    def extract_features(self, account_metrics: Dict[str, float]) -> np.ndarray:
        """Extract standardized feature vector for ML model inference."""
        drain_velocity_mins = account_metrics.get("drain_velocity_mins", 60.0)
        retention_ratio = account_metrics.get("retention_ratio", 0.5)
        fan_out_degree = account_metrics.get("fan_out_degree", 1.0)
        complaint_count = account_metrics.get("complaint_count", 0.0)

        # Normalized feature array
        features = np.array([
            min(1.0, 10.0 / max(1.0, drain_velocity_mins)),  # Velocity spike
            1.0 - min(1.0, retention_ratio),                  # Rapid depletion
            min(1.0, fan_out_degree / 10.0),                  # Layering dispersion
            min(1.0, complaint_count / 5.0),                  # Direct complaint linkages
        ])
        return features

    def predict_risk_score(self, account_metrics: Dict[str, float]) -> float:
        """Calculate mule risk probability score [0.0, 1.0]."""
        features = self.extract_features(account_metrics)
        # Baseline weighted ensemble weights
        weights = np.array([0.35, 0.25, 0.20, 0.20])
        score = float(np.dot(features, weights))
        return round(min(1.0, max(0.0, score)), 4)

    def is_mule_ring_candidate(self, account_metrics: Dict[str, float]) -> bool:
        """Boolean decision boundary for automated freezing recommendations."""
        return self.predict_risk_score(account_metrics) >= self.risk_threshold
