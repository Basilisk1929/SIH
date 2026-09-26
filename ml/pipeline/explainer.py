"""Feature explanation engine generating interpretable rationale for risk scores."""

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FeatureExplanation:
    """Explains a single feature's contribution to the transaction risk signal."""
    feature: str
    value: float
    contribution: float  # Normalized contribution weight [-1.0, 1.0]
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            "value": round(self.value, 2) if isinstance(self.value, float) else self.value,
            "contribution": round(self.contribution, 3),
            "description": self.description,
        }


class RiskFeatureExplainer:
    """Interprets model risk scores into human-readable forensic evidence factors."""

    DESCRIPTIONS: Dict[str, str] = {
        "transactions_last_1h": "High transaction burst velocity in last 1 hour ({val:.0f} txns)",
        "transactions_last_24h": "Elevated 24-hour transaction frequency ({val:.0f} txns)",
        "cashout_ratio": "High ATM cash-out ratio ({val:.1%})",
        "complaint_link_count": "Associated with {val:.0f} citizen cybercrime complaint(s)",
        "graph_degree": "Elevated graph connectivity degree ({val:.0f} edges)",
        "graph_centrality": "High hub network centrality score ({val:.2f})",
        "geographic_distance": "Anomalous geographic distance between counterparties ({val:.1f} km)",
        "transaction_amount": "Significant transaction amount (₹{val:,.2f})",
        "transaction_frequency": "High daily activity frequency ({val:.1f} txns/day)",
        "unique_receivers": "Dispersing funds across {val:.0f} unique receivers",
        "unique_senders": "Funneling funds from {val:.0f} unique senders",
        "account_age": "New/immature account ({val:.0f} days active)",
    }

    def __init__(
        self,
        feature_names: List[str],
        feature_importances: Optional[Dict[str, float]] = None,
        feature_medians: Optional[Dict[str, float]] = None,
        feature_stds: Optional[Dict[str, float]] = None,
    ):
        self.feature_names = feature_names
        self.feature_importances = feature_importances or {f: 1.0 / len(feature_names) for f in feature_names}
        self.feature_medians = feature_medians or {f: 0.0 for f in feature_names}
        self.feature_stds = feature_stds or {f: 1.0 for f in feature_names}

    def explain_instance(
        self,
        features: Dict[str, float],
        top_k: int = 4,
    ) -> List[FeatureExplanation]:
        """Explain the top-k driving risk factors for a specific transaction."""
        contributions: List[Tuple[str, float, float]] = []

        for feat in self.feature_names:
            val = float(features.get(feat, 0.0))
            med = self.feature_medians.get(feat, 0.0)
            std = max(1e-4, self.feature_stds.get(feat, 1.0))
            imp = self.feature_importances.get(feat, 0.05)

            # Z-score deviation scaled by model feature importance
            z_score = (val - med) / std
            raw_contrib = imp * z_score
            contributions.append((feat, val, raw_contrib))

        # Sort by highest positive risk contribution
        contributions.sort(key=lambda x: x[2], reverse=True)

        explanations: List[FeatureExplanation] = []
        for feat, val, contrib in contributions[:top_k]:
            tmpl = self.DESCRIPTIONS.get(feat, "{feat}: {val}")
            try:
                desc = tmpl.format(val=val)
            except Exception:
                desc = f"{feat} value is {val}"

            norm_contrib = min(1.0, max(-1.0, float(contrib)))
            explanations.append(
                FeatureExplanation(
                    feature=feat,
                    value=val,
                    contribution=norm_contrib,
                    description=desc,
                )
            )

        return explanations
