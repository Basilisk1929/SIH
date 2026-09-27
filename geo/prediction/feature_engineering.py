"""Feature engineering for ATM cash-out location likelihood prediction."""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
import pandas as pd

from geo.constants import EARTH_RADIUS_KM
from geo.indexing.h3_indexer import H3Indexer
from geo.prediction.constants import (
    BANK_CATEGORY_WEIGHTS,
    DISTANCE_DECAY_SCALE_KM,
    OUTLET_FEASIBILITY_WEIGHTS,
)


class CashoutFeatureExtractor:
    """Extracts spatial, behavioral, temporal, and infrastructure features for candidate ATMs."""

    def __init__(self, geo_engine: Optional[Any] = None):
        self.geo_engine = geo_engine

    def extract_features(
        self,
        candidate: Dict[str, Any],
        anchor_lat: float,
        anchor_lng: float,
        recent_transactions: Optional[List[Dict[str, Any]]] = None,
        account_risk_score: Optional[float] = None,
        cashout_ratio: Optional[float] = None,
        transactions_last_1h: Optional[int] = None,
        prediction_dt: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Extract multi-dimensional predictive features for a single candidate ATM."""
        dt = prediction_dt or datetime.now(timezone.utc)
        hour = dt.hour
        weekday = dt.weekday()  # 0=Monday, 6=Sunday

        # 1. Distance from Recent Activity
        dist_km = float(candidate.get("distance_km", 0.0))
        # Exponential proximity decay score [0, 1]
        dist_score = math.exp(-dist_km / DISTANCE_DECAY_SCALE_KM)

        # 2. Distance from Prior Cash-Out Locations
        prior_cashout_dist_km: Optional[float] = None
        prior_cashout_score = 0.5  # Neutral default when no prior cashout history

        if recent_transactions:
            prior_cashouts: List[Dict[str, Any]] = []
            for tx in recent_transactions:
                is_co = (
                    tx.get("is_cashout") is True
                    or str(tx.get("transaction_type", "")).upper() in ["CASH_OUT", "ATM_WITHDRAWAL"]
                    or str(tx.get("payment_channel", "")).upper() == "ATM"
                )
                if is_co and tx.get("latitude") is not None and tx.get("longitude") is not None:
                    prior_cashouts.append(tx)

            if prior_cashouts:
                min_d = float("inf")
                cand_lat = float(candidate["latitude"])
                cand_lng = float(candidate["longitude"])
                for co in prior_cashouts:
                    co_lat = float(co["latitude"])
                    co_lng = float(co["longitude"])
                    dlat = math.radians(cand_lat - co_lat)
                    dlng = math.radians(cand_lng - co_lng)
                    a = (
                        math.sin(dlat / 2.0) ** 2
                        + math.cos(math.radians(co_lat))
                        * math.cos(math.radians(cand_lat))
                        * math.sin(dlng / 2.0) ** 2
                    )
                    d = EARTH_RADIUS_KM * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
                    if d < min_d:
                        min_d = d
                prior_cashout_dist_km = round(min_d, 2)
                # Strong fit if ATM is close to account's historical cashout grounds
                prior_cashout_score = math.exp(-min_d / 5.0)

        # 3. H3 Cell Spatial Cybercrime Risk
        h3_cell = candidate.get("h3_cell")
        if not h3_cell:
            h3_cell = H3Indexer.point_to_h3(candidate["latitude"], candidate["longitude"], resolution=7)

        cell_risk = 20.0
        local_cashout_freq = 0
        if self.geo_engine is not None:
            try:
                cell_profile = self.geo_engine.analyze_cell(h3_cell)
                cell_risk = float(cell_profile.get("risk_score", 20.0))
                local_cashout_freq = int(cell_profile.get("fraud_count", 0))
            except Exception:
                pass
        h3_risk_score = min(max(cell_risk / 100.0, 0.0), 1.0)

        # 4. Hotspot Cluster & Cybercrime Corridor Proximity
        is_hotspot_adj = bool(candidate.get("is_hotspot_adjacent", False))
        hotspot_score = 0.90 if is_hotspot_adj else 0.35

        # 5. ATM / Bank Infrastructure Characteristics
        outlet_type = str(candidate.get("outlet_type", "ON_SITE_ATM"))
        bank_cat = str(candidate.get("bank_category", "PUBLIC_SECTOR"))

        outlet_weight = OUTLET_FEASIBILITY_WEIGHTS.get(outlet_type, 0.70)
        bank_weight = BANK_CATEGORY_WEIGHTS.get(bank_cat, 0.90)
        atm_characteristics_score = (outlet_weight * 0.75) + (bank_weight * 0.25)

        # 6. Time-of-Day Pattern
        # Nocturnal (22:00 - 05:00 UTC+5.5 approx) favors 24/7 off-site ATMs & cash recyclers
        if 22 <= hour or hour < 5:
            # Nocturnal: off-site ATMs / CRMs are ideal for mules; branches are closed
            time_of_day_score = 0.95 if outlet_type in ["OFF_SITE_ATM", "CASH_RECYCLER", "WHITE_LABEL_ATM"] else 0.30
        elif 18 <= hour < 22:
            time_of_day_score = 0.85
        elif 10 <= hour < 18:
            time_of_day_score = 0.75
        else:
            time_of_day_score = 0.65

        # 7. Day-of-Week Pattern
        # Weekends (Saturday=5, Sunday=6) have higher cashout dissipation ratios due to branch closures
        day_of_week_score = 0.90 if weekday in [5, 6] else 0.70

        # 8. Transaction Velocity & Urgency Multiplier
        velocity = int(transactions_last_1h or 0)
        ratio = float(cashout_ratio if cashout_ratio is not None else 0.5)
        risk = float(account_risk_score if account_risk_score is not None else 50.0)

        # High burst velocity (e.g. > 5 txns/hr) indicates immediate physical cashout urgency
        velocity_urgency = 0.5
        if velocity >= 8:
            velocity_urgency = 1.0
        elif velocity >= 4:
            velocity_urgency = 0.85
        elif velocity >= 1:
            velocity_urgency = 0.65

        current_cashout_risk = (risk / 100.0 * 0.6) + (ratio * 0.4)

        return {
            "distance_km": dist_km,
            "dist_score": dist_score,
            "prior_cashout_dist_km": prior_cashout_dist_km,
            "prior_cashout_score": prior_cashout_score,
            "h3_cell": h3_cell,
            "h3_cell_risk": round(cell_risk, 1),
            "h3_risk_score": h3_risk_score,
            "local_cashout_frequency": local_cashout_freq,
            "hotspot_score": hotspot_score,
            "is_hotspot_adjacent": is_hotspot_adj,
            "atm_characteristics_score": atm_characteristics_score,
            "outlet_type": outlet_type,
            "bank_category": bank_cat,
            "time_of_day_score": time_of_day_score,
            "day_of_week_score": day_of_week_score,
            "velocity_urgency": velocity_urgency,
            "current_cashout_risk": current_cashout_risk,
            "transactions_last_1h": velocity,
            "account_risk_score": risk,
            "cashout_ratio": ratio,
        }
