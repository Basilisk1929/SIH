"""Geospatial clustering and spatial density analyzer for synthetic incident coordinates."""

import math
from typing import Dict, List, Tuple
from geo.mappings.cyber_hotspots import INDIAN_CYBER_REFERENCE_HUBS, HotspotInfo


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth in kilometers."""
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


class GeoHotspotAnalyzer:
    """Groups synthetic complaints and IP origins into geographic threat hotspots."""

    @staticmethod
    def map_incident_to_closest_hub(
        lat: float, lng: float, threshold_km: float = 75.0
    ) -> Tuple[HotspotInfo | None, float]:
        """Find the closest reference cybercrime cluster within threshold."""
        closest_hub = None
        min_distance = float("inf")

        for hub in INDIAN_CYBER_REFERENCE_HUBS:
            dist = haversine_km(lat, lng, hub["lat"], hub["lng"])
            if dist < min_distance:
                min_distance = dist
                closest_hub = hub

        if min_distance <= threshold_km:
            return closest_hub, round(min_distance, 2)
        return None, round(min_distance, 2)
