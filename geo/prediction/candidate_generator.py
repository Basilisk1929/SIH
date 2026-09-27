"""Candidate ATM generation and spatial filtering for cash-out location prediction."""

import math
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from geo.constants import EARTH_RADIUS_KM
from geo.datasets.rbi_atm_registry import RBIAtmRegistry
from geo.proximity.atm_proximity import ATMProximityAnalyzer
from geo.validation.coordinate_validator import CoordinateValidator


class CandidateATMGenerator:
    """Generates and filters candidate RBI ATM outlets within proximity of an account's recent activity."""

    def __init__(
        self,
        registry: Optional[RBIAtmRegistry] = None,
        proximity_analyzer: Optional[ATMProximityAnalyzer] = None,
    ):
        self.registry = registry or RBIAtmRegistry()
        self.proximity_analyzer = proximity_analyzer or ATMProximityAnalyzer(registry=self.registry)

    def resolve_anchor_point(
        self,
        current_lat: Optional[float] = None,
        current_lng: Optional[float] = None,
        recent_transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Determine geographic anchor point from explicit coordinates or recent transaction activity.

        Resolution Priority:
        1. Explicit current coordinates if provided.
        2. Most recent transaction with coordinates in transaction history.
        3. Centroid of georeferenced transactions.

        Returns:
            Dict containing latitude, longitude, and origin source tag.
        """
        # 1. Explicit current coordinates
        if current_lat is not None and current_lng is not None:
            valid, err = CoordinateValidator.validate_point(current_lat, current_lng, require_india=True)
            if not valid:
                raise ValueError(f"Explicit anchor coordinates are invalid: {err}")
            return {
                "latitude": round(float(current_lat), 6),
                "longitude": round(float(current_lng), 6),
                "source": "explicit_current_location",
            }

        # 2. Extract from recent transactions
        if recent_transactions:
            valid_coords: List[Tuple[float, float, str]] = []
            for tx in recent_transactions:
                lat = tx.get("latitude")
                lng = tx.get("longitude")
                if lat is not None and lng is not None:
                    try:
                        f_lat = float(lat)
                        f_lng = float(lng)
                        valid, _ = CoordinateValidator.validate_point(f_lat, f_lng, require_india=True)
                        if valid:
                            timestamp = str(tx.get("timestamp", ""))
                            valid_coords.append((f_lat, f_lng, timestamp))
                    except (ValueError, TypeError):
                        continue

            if valid_coords:
                # Prefer the most recent transaction coordinate (assuming list is sorted or uses latest)
                latest_lat, latest_lng, _ = valid_coords[-1]
                return {
                    "latitude": round(latest_lat, 6),
                    "longitude": round(latest_lng, 6),
                    "source": "recent_transaction_latest",
                }

        raise ValueError(
            "Unable to resolve geographic anchor: neither valid current coordinates nor georeferenced "
            "transactions were provided."
        )

    def generate_candidate_atms(
        self,
        anchor_lat: float,
        anchor_lng: float,
        candidate_radius_km: float = 15.0,
        max_candidates: int = 50,
    ) -> List[Dict[str, Any]]:
        """Query and filter operational RBI ATM outlets within the search radius of the anchor coordinate.

        Filters applied:
        - Must be operational (`is_operational == True`).
        - Cash dispenser must be active (`cash_dispenser_active == True`).
        - Must lie within Republic of India geographic boundaries.
        - Distance must be strictly <= candidate_radius_km.

        Returns:
            List of filtered candidate ATM records sorted by distance ascending.
        """
        valid, err = CoordinateValidator.validate_point(anchor_lat, anchor_lng, require_india=True)
        if not valid:
            raise ValueError(f"Invalid anchor coordinates: {err}")

        # Retrieve operational ATMs from registry
        atms_df = self.registry.get_atms_only()
        if atms_df.empty:
            return []

        candidates: List[Dict[str, Any]] = []

        for _, row in atms_df.iterrows():
            atm_lat = float(row.get("latitude", 0.0))
            atm_lng = float(row.get("longitude", 0.0))

            # Validate ATM coordinates within India
            coord_valid, _ = CoordinateValidator.validate_point(atm_lat, atm_lng)
            if not coord_valid:
                continue

            # Check operational status
            if not bool(row.get("is_operational", True)) or not bool(row.get("cash_dispenser_active", True)):
                continue

            # Haversine distance from anchor
            dlat = math.radians(atm_lat - anchor_lat)
            dlng = math.radians(atm_lng - anchor_lng)
            a = (
                math.sin(dlat / 2.0) ** 2
                + math.cos(math.radians(anchor_lat))
                * math.cos(math.radians(atm_lat))
                * math.sin(dlng / 2.0) ** 2
            )
            dist_km = EARTH_RADIUS_KM * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

            if dist_km <= candidate_radius_km:
                cand = {
                    "atm_id": str(row.get("outlet_id")),
                    "bank_name": str(row.get("bank_name")),
                    "bank_code": str(row.get("bank_code", "")),
                    "outlet_type": str(row.get("outlet_type", "ON_SITE_ATM")),
                    "bank_category": str(row.get("bank_category", "PUBLIC_SECTOR")),
                    "latitude": round(atm_lat, 6),
                    "longitude": round(atm_lng, 6),
                    "distance_km": round(dist_km, 3),
                    "h3_cell": str(row.get("h3_cell_res7", "")),
                    "city": str(row.get("center_city", "")),
                    "district": str(row.get("district", "")),
                    "state": str(row.get("state", "")),
                    "is_hotspot_adjacent": bool(row.get("is_hotspot_adjacent", False)),
                }
                candidates.append(cand)

        # Sort by distance ascending
        candidates.sort(key=lambda c: c["distance_km"])
        return candidates[:max_candidates]
