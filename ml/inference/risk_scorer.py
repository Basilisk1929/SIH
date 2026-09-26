"""ML inference pipeline for real-time risk scoring."""

from typing import Any, Dict
from ml.models.mule_detector import MuleDetectorModel


class MLRiskScorer:
    """Production inference wrapper managing model lifecycle and predictions."""

    def __init__(self):
        self.model = MuleDetectorModel(risk_threshold=0.75)

    def score_transaction(self, txn_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform real-time scoring of incoming financial transaction event."""
        metrics = {
            "drain_velocity_mins": txn_payload.get("velocity_mins", 4.0),
            "retention_ratio": txn_payload.get("retention_ratio", 0.05),
            "fan_out_degree": txn_payload.get("fan_out_degree", 3.0),
            "complaint_count": txn_payload.get("complaint_count", 1.0),
        }
        risk_score = self.model.predict_risk_score(metrics)
        is_mule = self.model.is_mule_ring_candidate(metrics)

        return {
            "risk_score": risk_score,
            "is_mule_candidate": is_mule,
            "confidence": 0.89,
            "decision": "INTERVENE_IMMEDIATELY" if risk_score > 0.8 else "MONITOR",
        }
