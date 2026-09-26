"""Production financial transaction risk engine wrapping trained gradient boosted model."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import xgboost as xgb

from ml.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MODEL_PATH,
    DISCLAIMER_TEXT,
    FEATURE_COLUMNS,
    RISK_BANDS,
)
from ml.pipeline.explainer import FeatureExplanation, RiskFeatureExplainer


class TransactionRiskEngine:
    """Evaluates transaction risk signals with calibrated scoring, risk bands, and explanations."""

    RISK_BANDS = [
        ("CRITICAL", 85.0),
        ("HIGH", 60.0),
        ("MEDIUM", 30.0),
        ("LOW", 0.0),
    ]

    def __init__(
        self,
        model: Optional[xgb.XGBClassifier] = None,
        model_path: Path = DEFAULT_MODEL_PATH,
        config_path: Path = DEFAULT_CONFIG_PATH,
    ):
        self.model_path = model_path
        self.config_path = config_path
        self.feature_names = FEATURE_COLUMNS
        self.model = model
        self.config: Dict[str, Any] = {}
        self.explainer: Optional[RiskFeatureExplainer] = None

        if self.model is None and self.model_path.exists():
            self.load()

    def _determine_risk_band(self, score: float) -> str:
        """Map 0-100 continuous risk score to categorical risk band."""
        for band, threshold in self.RISK_BANDS:
            if score >= threshold:
                return band
        return "LOW"

    def predict_risk(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """Compute calibrated risk score (0-100), risk band, and feature explanations."""
        # Align features to expected vector order
        feature_vector = np.array([
            float(feature_dict.get(col, 0.0)) for col in self.feature_names
        ]).reshape(1, -1)

        if self.model is not None:
            raw_prob = float(self.model.predict_proba(feature_vector)[0, 1])
        else:
            # Fallback heuristic scoring if model artifact not yet trained
            amt = float(feature_dict.get("transaction_amount", 0.0))
            burst = float(feature_dict.get("transactions_last_1h", 0.0))
            cashout = float(feature_dict.get("cashout_ratio", 0.0))
            complaints = float(feature_dict.get("complaint_link_count", 0.0))

            raw_prob = min(
                0.99,
                (0.15 * min(1.0, amt / 50000.0))
                + (0.35 * min(1.0, burst / 4.0))
                + (0.25 * cashout)
                + (0.25 * min(1.0, complaints / 2.0)),
            )

        # Scale to 0-100 range
        risk_score = round(raw_prob * 100.0, 2)
        risk_band = self._determine_risk_band(risk_score)

        # Generate feature explanations
        explanations: List[Dict[str, Any]] = []
        if self.explainer:
            exp_objs = self.explainer.explain_instance(feature_dict, top_k=4)
            explanations = [e.to_dict() for e in exp_objs]
        else:
            # Fallback top contributors
            sorted_feats = sorted(
                feature_dict.items(),
                key=lambda x: abs(float(x[1])),
                reverse=True,
            )
            for f_name, f_val in sorted_feats[:4]:
                explanations.append(
                    {
                        "feature": f_name,
                        "value": round(float(f_val), 2),
                        "contribution": 0.25,
                        "description": f"{f_name} observed value: {f_val}",
                    }
                )

        return {
            "risk_score": risk_score,
            "risk_band": risk_band,
            "is_suspicious": risk_score >= 60.0,
            "feature_explanations": explanations,
            "disclaimer": DISCLAIMER_TEXT,
        }

    def save(self, model_path: Optional[Path] = None, config_path: Optional[Path] = None) -> None:
        """Serialize trained model artifact and feature configuration to disk."""
        target_model = model_path or self.model_path
        target_config = config_path or self.config_path

        target_model.parent.mkdir(parents=True, exist_ok=True)
        target_config.parent.mkdir(parents=True, exist_ok=True)

        if self.model is not None:
            self.model.save_model(str(target_model))

        with open(target_config, mode="w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def load(self, model_path: Optional[Path] = None, config_path: Optional[Path] = None) -> None:
        """Load trained XGBoost model and feature configuration from disk."""
        src_model = model_path or self.model_path
        src_config = config_path or self.config_path

        if src_config.exists():
            with open(src_config, mode="r", encoding="utf-8") as f:
                self.config = json.load(f)

        if src_model.exists():
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(src_model))

        self.explainer = RiskFeatureExplainer(
            feature_names=self.config.get("feature_names", self.feature_names),
            feature_importances=self.config.get("feature_importances"),
            feature_medians=self.config.get("feature_medians"),
            feature_stds=self.config.get("feature_stds"),
        )
