"""ATM proximity and spatial cashout corridor analysis."""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

from geo.constants import EARTH_RADIUS_KM
from geo.datasets.rbi_atm_registry import RBIAtmRegistry
from geo.indexing.h3_indexer import H3Indexer
from geo.validation.coordinate_validator import CoordinateValidator


class ATMProximityAnalyzer:
    """Analyzes spatial proximity between transactions/incidents and bank ATMs."""

    def __init__(self, registry: Optional[RBIAtmRegistry] = None):
        self.registry = registry or RBIAtmRegistry()
        self._tree: Optional[BallTree] = None
        self._atms_df: Optional[pd.DataFrame] = None
        self._build_spatial_index()

    def _build_spatial_index(self) -> None:
        """Construct a BallTree with haversine distance over operational ATM coordinates."""
        df = self.registry.get_atms_only()
        if df.empty:
            self._tree = None
            self._atms_df = pd.DataFrame()
            return

        self._atms_df = df.reset_index(drop=True)
        # Convert lat, lng to radians for haversine
        coords_rad = np.radians(self._atms_df[["latitude", "longitude"]].values)
        self._tree = BallTree(coords_rad, metric="haversine")

    def find_nearest_atms(
        self,
        lat: float,
        lng: float,
        top_k: int = 5,
        max_radius_km: float = 25.0,
    ) -> List[Dict[str, Any]]:
        """Find the nearest operational ATMs to a geographic coordinate.

        Args:
            lat: Latitude of query point.
            lng: Longitude of query point.
            top_k: Maximum number of closest ATMs to return.
            max_radius_km: Distance cutoff in kilometers.

        Returns:
            List of closest ATM records with distance in km and meters.
        """
        valid, err = CoordinateValidator.validate_point(lat, lng)
        if not valid:
            raise ValueError(f"Invalid query coordinates: {err}")

        if self._tree is None or self._atms_df is None or self._atms_df.empty:
            return []

        k = min(top_k, len(self._atms_df))
        query_rad = np.radians([[float(lat), float(lng)]])

        distances_rad, indices = self._tree.query(query_rad, k=k)
        distances_km = distances_rad[0] * EARTH_RADIUS_KM
        idx_array = indices[0]

        results: List[Dict[str, Any]] = []
        for dist_km, idx in zip(distances_km, idx_array):
            if dist_km > max_radius_km:
                continue

            atm_row = self._atms_df.iloc[idx].to_dict()
            results.append({
                "outlet_id": atm_row.get("outlet_id"),
                "bank_name": atm_row.get("bank_name"),
                "bank_code": atm_row.get("bank_code"),
                "outlet_type": atm_row.get("outlet_type"),
                "bank_category": atm_row.get("bank_category"),
                "city": atm_row.get("center_city"),
                "district": atm_row.get("district"),
                "state": atm_row.get("state"),
                "latitude": float(atm_row.get("latitude", 0.0)),
                "longitude": float(atm_row.get("longitude", 0.0)),
                "distance_km": round(float(dist_km), 3),
                "distance_meters": round(float(dist_km * 1000.0), 1),
                "is_hotspot_adjacent": bool(atm_row.get("is_hotspot_adjacent", False)),
            })

        return results

    def find_nearest_atms_for_cell(
        self,
        h3_cell: str,
        top_k: int = 5,
        max_radius_km: float = 25.0,
    ) -> List[Dict[str, Any]]:
        """Find the nearest ATMs to the centroid of an H3 cell."""
        centroid_lat, centroid_lng = H3Indexer.h3_to_point(h3_cell)
        return self.find_nearest_atms(
            centroid_lat,
            centroid_lng,
            top_k=top_k,
            max_radius_km=max_radius_km,
        )

    @staticmethod
    def calculate_atm_proximity_score(
        distance_km: float,
        is_cashout: bool = False,
        is_nighttime: bool = False,
    ) -> float:
        """Calculate spatial ATM proximity risk modifier [0.0, 1.0].

        Higher risk when cash withdrawal or rapid cashout occurs within immediate walking
        proximity (<300m) of an ATM, especially during nocturnal hours.
        """
        # Distance decay: 1.0 at 0km, 0.5 at 1km, ~0.1 at 3km
        base_proximity = math.exp(-1.2 * distance_km)

        multiplier = 1.0
        if is_cashout:
            multiplier += 0.3
        if is_nighttime:
            multiplier += 0.2

        score = min(1.0, base_proximity * multiplier)
        return round(score, 3)
