"""Real-time transaction risk inference service."""

import datetime
import logging
from typing import Any, Dict, Optional
from ml.models.risk_engine import TransactionRiskEngine

logger = logging.getLogger(__name__)


class RiskInferenceService:
    """Production inference wrapper providing real-time risk scoring, banding, and explanations."""

    def __init__(self, engine: Optional[TransactionRiskEngine] = None):
        self.engine = engine or TransactionRiskEngine()

    def predict(self, transaction_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Predict risk score, risk band, and feature explanations for an incoming transaction."""
        txn_id = transaction_payload.get("transaction_id", "TXN_LIVE")

        # Extract or construct features dictionary
        if "features" in transaction_payload and isinstance(transaction_payload["features"], dict):
            features = transaction_payload["features"]
        else:
            # Direct mapping from payload fields if features dictionary not explicitly nested
            features = {
                "transaction_amount": float(transaction_payload.get("amount", transaction_payload.get("transaction_amount", 0.0))),
                "transaction_frequency": float(transaction_payload.get("transaction_frequency", 0.1)),
                "transactions_last_1h": float(transaction_payload.get("transactions_last_1h", 0.0)),
                "transactions_last_24h": float(transaction_payload.get("transactions_last_24h", 0.0)),
                "unique_receivers": float(transaction_payload.get("unique_receivers", 1.0)),
                "unique_senders": float(transaction_payload.get("unique_senders", 1.0)),
                "cashout_ratio": float(transaction_payload.get("cashout_ratio", 0.0)),
                "account_age": float(transaction_payload.get("account_age", 180.0)),
                "graph_degree": float(transaction_payload.get("graph_degree", 2.0)),
                "graph_centrality": float(transaction_payload.get("graph_centrality", 0.01)),
                "complaint_link_count": float(transaction_payload.get("complaint_link_count", 0.0)),
                "geographic_distance": float(transaction_payload.get("geographic_distance", 0.0)),
            }

        prediction = self.engine.predict_risk(features)

        return {
            "transaction_id": txn_id,
            "sender_account_number": transaction_payload.get("sender_account_number"),
            "receiver_account_number": transaction_payload.get("receiver_account_number"),
            "amount": features.get("transaction_amount", 0.0),
            "risk_score": prediction["risk_score"],
            "risk_band": prediction["risk_band"],
            "is_suspicious": prediction["is_suspicious"],
            "feature_explanations": prediction["feature_explanations"],
            "disclaimer": prediction["disclaimer"],
            "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
