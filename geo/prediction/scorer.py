"""Multi-factor likelihood scoring and ranking for candidate cash-out ATMs."""

from typing import Any, Dict, List
from geo.prediction.constants import (
    WEIGHT_BURST_URGENCY,
    WEIGHT_DISTANCE,
    WEIGHT_H3_RISK,
    WEIGHT_HOTSPOT,
    WEIGHT_OUTLET_PROFILE,
    WEIGHT_TEMPORAL,
)


class CashoutLocationScorer:
    """Computes calibrated cash-out likelihood scores and ranks candidate ATMs."""

    @staticmethod
    def score_candidate(candidate_features: Dict[str, Any]) -> float:
        """Calculate single candidate's predictive likelihood score (0.0 to 100.0)."""
        dist_s = candidate_features["dist_score"]
        risk_s = candidate_features["h3_risk_score"]
        hotspot_s = candidate_features["hotspot_score"]
        outlet_s = candidate_features["atm_characteristics_score"]
        temporal_s = (candidate_features["time_of_day_score"] + candidate_features["day_of_week_score"]) / 2.0
        urgency_s = candidate_features["velocity_urgency"]

        # Base weighted composite
        raw_composite = (
            (WEIGHT_DISTANCE * dist_s)
            + (WEIGHT_H3_RISK * risk_s)
            + (WEIGHT_HOTSPOT * hotspot_s)
            + (WEIGHT_OUTLET_PROFILE * outlet_s)
            + (WEIGHT_TEMPORAL * temporal_s)
            + (WEIGHT_BURST_URGENCY * urgency_s)
        )

        score = raw_composite * 100.0

        # Behavioral & Contextual Interactivity Adjustments
        # 1. Proximity + Urgency interaction (immediate golden hour withdrawal)
        dist_km = candidate_features["distance_km"]
        velocity = candidate_features.get("transactions_last_1h", 0)
        if dist_km <= 1.5 and velocity >= 4:
            score += 5.5
        elif dist_km <= 3.0 and velocity >= 1:
            score += 2.5

        # 2. Historical ground familiarity
        prior_dist = candidate_features.get("prior_cashout_dist_km")
        if prior_dist is not None and prior_dist <= 2.0:
            score += 4.5

        # 3. Known Cybercrime corridor boost
        if candidate_features.get("is_hotspot_adjacent"):
            score += 3.5

        # Clamp to realistic tactical intelligence range [5.0, 98.5]
        calibrated_score = min(max(score, 5.0), 98.5)
        return round(float(calibrated_score), 1)

    @classmethod
    def rank_candidates(
        cls,
        candidate_feature_pairs: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Score all candidates, sort by prediction score descending, and assign ranks."""
        scored: List[Dict[str, Any]] = []

        for item in candidate_feature_pairs:
            cand = item["candidate"]
            features = item["features"]
            score = cls.score_candidate(features)

            enriched = dict(cand)
            enriched["prediction_score"] = score
            enriched["features"] = features
            scored.append(enriched)

        # Primary sort: prediction_score descending. Secondary sort: distance_km ascending
        scored.sort(key=lambda x: (-x["prediction_score"], x["distance_km"]))

        # Assign 1-indexed ranks
        ranked: List[Dict[str, Any]] = []
        for i, item in enumerate(scored[:top_k], start=1):
            item["rank"] = i
            ranked.append(item)

        return ranked
