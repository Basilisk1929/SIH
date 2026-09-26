"""DBSCAN spatial density clustering and cybercrime threat hotspot detector."""

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from shapely.geometry import MultiPoint, Polygon
from sklearn.cluster import DBSCAN

from geo.constants import DEFAULT_DBSCAN_EPS_KM, DEFAULT_DBSCAN_MIN_SAMPLES, EARTH_RADIUS_KM
from geo.mappings.cyber_hotspots import INDIAN_CYBER_REFERENCE_HUBS


@dataclass
class HotspotClusterSummary:
    cluster_id: int
    centroid_lat: float
    centroid_lng: float
    point_count: int
    fraud_count: int
    total_amount_inr: float
    dominant_pattern: str
    radius_km: float
    nearest_reference_hub: Optional[str] = None
    distance_to_ref_hub_km: Optional[float] = None
    convex_hull_geojson: Optional[Dict[str, Any]] = None


class DBSCANHotspotDetector:
    """Detects geospatial incident and cashout hotspots using Haversine DBSCAN."""

    def __init__(
        self,
        eps_km: float = DEFAULT_DBSCAN_EPS_KM,
        min_samples: int = DEFAULT_DBSCAN_MIN_SAMPLES,
    ):
        self.eps_km = float(eps_km)
        self.min_samples = int(min_samples)
        self.eps_rad = self.eps_km / EARTH_RADIUS_KM
        self._model = DBSCAN(eps=self.eps_rad, min_samples=self.min_samples, metric="haversine")
        self.cluster_summaries_: List[HotspotClusterSummary] = []

    def fit_predict(
        self,
        df: pd.DataFrame,
        lat_col: str = "latitude",
        lng_col: str = "longitude",
        fraud_col: str = "is_fraud",
        amount_col: str = "amount",
        pattern_col: str = "scam_category",
    ) -> pd.DataFrame:
        """Fit DBSCAN on dataframe coordinates and return copy with 'cluster_id' and 'is_hotspot'."""
        if df.empty or lat_col not in df.columns or lng_col not in df.columns:
            result = df.copy()
            result["cluster_id"] = -1
            result["is_hotspot"] = False
            self.cluster_summaries_ = []
            return result

        result = df.copy()
        valid_mask = result[lat_col].notna() & result[lng_col].notna()
        result["cluster_id"] = -1
        result["is_hotspot"] = False

        valid_df = result[valid_mask]
        if len(valid_df) < self.min_samples:
            return result

        coords_deg = valid_df[[lat_col, lng_col]].values
        coords_rad = np.radians(coords_deg)

        labels = self._model.fit_predict(coords_rad)
        result.loc[valid_mask, "cluster_id"] = labels
        result.loc[valid_mask, "is_hotspot"] = labels >= 0

        # Calculate cluster summaries
        self.cluster_summaries_ = self._compute_cluster_summaries(
            result,
            lat_col=lat_col,
            lng_col=lng_col,
            fraud_col=fraud_col,
            amount_col=amount_col,
            pattern_col=pattern_col,
        )

        return result

    def _compute_cluster_summaries(
        self,
        df: pd.DataFrame,
        lat_col: str,
        lng_col: str,
        fraud_col: str,
        amount_col: str,
        pattern_col: str,
    ) -> List[HotspotClusterSummary]:
        """Compute aggregated statistics, radius, convex hull, and closest reference hub."""
        summaries: List[HotspotClusterSummary] = []
        cluster_ids = sorted([cid for cid in df["cluster_id"].unique() if cid >= 0])

        for cid in cluster_ids:
            c_df = df[df["cluster_id"] == cid]
            n_pts = len(c_df)
            centroid_lat = round(float(c_df[lat_col].mean()), 6)
            centroid_lng = round(float(c_df[lng_col].mean()), 6)

            # Fraud count & amount
            fraud_count = int(c_df[fraud_col].sum()) if fraud_col in c_df.columns else 0
            total_amt = float(c_df[amount_col].sum()) if amount_col in c_df.columns else 0.0

            # Dominant pattern
            if pattern_col in c_df.columns and not c_df[pattern_col].dropna().empty:
                dominant = str(c_df[pattern_col].mode().iloc[0])
            else:
                dominant = "UNKNOWN"

            # Radius km from centroid to farthest point
            max_dist_km = 0.0
            pts_geo: List[Tuple[float, float]] = []
            for _, row in c_df.iterrows():
                plat = row[lat_col]
                plng = row[lng_col]
                pts_geo.append((plng, plat))  # GeoJSON order: lng, lat

                dlat = math.radians(plat - centroid_lat)
                dlng = math.radians(plng - centroid_lng)
                a = (
                    math.sin(dlat / 2) ** 2
                    + math.cos(math.radians(centroid_lat))
                    * math.cos(math.radians(plat))
                    * math.sin(dlng / 2) ** 2
                )
                d = EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                if d > max_dist_km:
                    max_dist_km = d

            # Convex hull geometry
            convex_hull_geojson = None
            if len(pts_geo) >= 3:
                try:
                    mp = MultiPoint(pts_geo)
                    hull = mp.convex_hull
                    if isinstance(hull, Polygon):
                        convex_hull_geojson = {
                            "type": "Polygon",
                            "coordinates": [list(hull.exterior.coords)],
                        }
                except Exception:
                    convex_hull_geojson = None

            # Proximity to reference Indian cyber hubs
            closest_hub_name = None
            min_hub_dist = float("inf")
            for hub in INDIAN_CYBER_REFERENCE_HUBS:
                dlat = math.radians(hub["lat"] - centroid_lat)
                dlng = math.radians(hub["lng"] - centroid_lng)
                a = (
                    math.sin(dlat / 2) ** 2
                    + math.cos(math.radians(centroid_lat))
                    * math.cos(math.radians(hub["lat"]))
                    * math.sin(dlng / 2) ** 2
                )
                hub_dist = EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                if hub_dist < min_hub_dist:
                    min_hub_dist = hub_dist
                    closest_hub_name = hub["name"]

            summaries.append(
                HotspotClusterSummary(
                    cluster_id=int(cid),
                    centroid_lat=centroid_lat,
                    centroid_lng=centroid_lng,
                    point_count=n_pts,
                    fraud_count=fraud_count,
                    total_amount_inr=round(total_amt, 2),
                    dominant_pattern=dominant,
                    radius_km=round(max_dist_km, 3),
                    nearest_reference_hub=closest_hub_name if min_hub_dist <= 100.0 else None,
                    distance_to_ref_hub_km=round(min_hub_dist, 2) if min_hub_dist <= 100.0 else None,
                    convex_hull_geojson=convex_hull_geojson,
                )
            )

        return summaries

    def get_cluster_summaries(self) -> List[Dict[str, Any]]:
        """Return list of cluster summary dictionaries."""
        return [asdict(s) for s in self.cluster_summaries_]

    def assign_point_to_nearest_cluster(
        self,
        lat: float,
        lng: float,
        buffer_multiplier: float = 1.25,
    ) -> Optional[int]:
        """Find if a given point falls within the spatial envelope of an existing cluster."""
        for s in self.cluster_summaries_:
            dlat = math.radians(s.centroid_lat - lat)
            dlng = math.radians(s.centroid_lng - lng)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat))
                * math.cos(math.radians(s.centroid_lat))
                * math.sin(dlng / 2) ** 2
            )
            dist_km = EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            effective_radius = max(s.radius_km * buffer_multiplier, self.eps_km)
            if dist_km <= effective_radius:
                return s.cluster_id
        return None
