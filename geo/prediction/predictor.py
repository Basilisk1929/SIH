"""Master CashoutLocationPredictor orchestrating candidate generation, feature extraction, scoring, and explanations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from geo.datasets.rbi_atm_registry import RBIAtmRegistry
from geo.prediction.candidate_generator import CandidateATMGenerator
from geo.prediction.constants import (
    CASHOUT_DATA_LIMITATION_DISCLAIMER,
    DEFAULT_CANDIDATE_RADIUS_KM,
    DEFAULT_PREDICTION_TOP_K,
)
from geo.prediction.explainer import CashoutExplainer
from geo.prediction.feature_engineering import CashoutFeatureExtractor
from geo.prediction.schemas import (
    CashoutPredictionRequest,
    CashoutPredictionResponse,
    PredictedATM,
)
from geo.prediction.scorer import CashoutLocationScorer


class CashoutLocationPredictor:
    """Predictive ranking engine for likely ATM cash-out locations."""

    def __init__(
        self,
        rbi_registry: Optional[RBIAtmRegistry] = None,
        geo_engine: Optional[Any] = None,
    ):
        self.registry = rbi_registry or RBIAtmRegistry()
        self.geo_engine = geo_engine
        self.candidate_generator = CandidateATMGenerator(registry=self.registry)
        self.feature_extractor = CashoutFeatureExtractor(geo_engine=self.geo_engine)

    def predict(self, request: CashoutPredictionRequest) -> CashoutPredictionResponse:
        """Execute end-to-end predictive ranking of nearby candidate ATMs for an investigated account."""
        now_iso = datetime.now(timezone.utc).isoformat()
        now_dt = datetime.now(timezone.utc)

        # 1. Resolve Geographic Anchor Point
        anchor = self.candidate_generator.resolve_anchor_point(
            current_lat=request.current_latitude,
            current_lng=request.current_longitude,
            recent_transactions=request.recent_transactions,
        )
        anchor_lat = float(anchor["latitude"])
        anchor_lng = float(anchor["longitude"])

        # 2. Generate and Filter Candidate ATMs
        radius_km = float(request.candidate_radius_km or DEFAULT_CANDIDATE_RADIUS_KM)
        top_k = int(request.top_k or DEFAULT_PREDICTION_TOP_K)

        raw_candidates = self.candidate_generator.generate_candidate_atms(
            anchor_lat=anchor_lat,
            anchor_lng=anchor_lng,
            candidate_radius_km=radius_km,
            max_candidates=50,
        )

        total_evaluated = len(raw_candidates)

        if not raw_candidates:
            return CashoutPredictionResponse(
                account_id=request.account_id,
                prediction_timestamp=now_iso,
                anchor_location=anchor,
                candidate_radius_km=radius_km,
                total_candidates_evaluated=0,
                predicted_atms=[],
                urgency_level="STANDARD",
                disclaimer=CASHOUT_DATA_LIMITATION_DISCLAIMER,
            )

        # 3. Feature Engineering for Each Candidate
        candidate_feature_pairs: List[Dict[str, Any]] = []
        for cand in raw_candidates:
            feats = self.feature_extractor.extract_features(
                candidate=cand,
                anchor_lat=anchor_lat,
                anchor_lng=anchor_lng,
                recent_transactions=request.recent_transactions,
                account_risk_score=request.account_risk_score,
                cashout_ratio=request.cashout_ratio,
                transactions_last_1h=request.transactions_last_1h,
                prediction_dt=now_dt,
            )
            candidate_feature_pairs.append({"candidate": cand, "features": feats})

        # 4. Multi-Factor Scoring & Ranking
        ranked_candidates = CashoutLocationScorer.rank_candidates(
            candidate_feature_pairs=candidate_feature_pairs,
            top_k=top_k,
        )

        # 5. Natural Language Explanation Generation & Schema Mapping
        predicted_atms: List[PredictedATM] = []
        for item in ranked_candidates:
            reasons = CashoutExplainer.generate_explanations(item)
            predicted_atm = PredictedATM(
                atm_id=item["atm_id"],
                bank_name=item["bank_name"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                distance_km=item["distance_km"],
                prediction_score=item["prediction_score"],
                rank=item["rank"],
                explanations=reasons,
                outlet_type=item.get("outlet_type"),
                bank_category=item.get("bank_category"),
                h3_cell=item.get("h3_cell"),
                city=item.get("city"),
                district=item.get("district"),
                state=item.get("state"),
            )
            predicted_atms.append(predicted_atm)

        # Determine overall urgency
        urgency = "STANDARD"
        risk_val = request.account_risk_score or 0.0
        vel_val = request.transactions_last_1h or 0
        if risk_val >= 80.0 or vel_val >= 8:
            urgency = "CRITICAL"
        elif risk_val >= 60.0 or vel_val >= 4:
            urgency = "HIGH"
        elif risk_val >= 40.0:
            urgency = "ELEVATED"

        return CashoutPredictionResponse(
            account_id=request.account_id,
            prediction_timestamp=now_iso,
            anchor_location=anchor,
            candidate_radius_km=radius_km,
            total_candidates_evaluated=total_evaluated,
            predicted_atms=predicted_atms,
            urgency_level=urgency,
            disclaimer=CASHOUT_DATA_LIMITATION_DISCLAIMER,
        )
