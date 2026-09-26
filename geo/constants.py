"""Constants and spatial boundaries for Geospatial Intelligence subsystem."""

from typing import Dict, Tuple

# Earth radius in kilometers for spherical calculations
EARTH_RADIUS_KM: float = 6371.0088

# Geographical Bounding Box for the Republic of India (including islands)
INDIA_BOUNDS: Dict[str, float] = {
    "min_lat": 6.5546079,
    "max_lat": 37.0970000,
    "min_lng": 68.1113787,
    "max_lng": 97.3955610,
}

# Global Lat/Lng valid bounds
GLOBAL_BOUNDS: Dict[str, float] = {
    "min_lat": -90.0,
    "max_lat": 90.0,
    "min_lng": -180.0,
    "max_lng": 180.0,
}

# Standard H3 Spatial Index Resolutions
# Res 8: ~460m edge length, ~0.74 km2 area (urban ward/neighborhood level)
# Res 7: ~1.22 km edge length, ~5.16 km2 area (city zone/cluster level - DEFAULT)
# Res 6: ~3.23 km edge length, ~36.1 km2 area (sub-district/taluk level)
# Res 5: ~8.54 km edge length, ~252.9 km2 area (district/regional level)
DEFAULT_H3_RESOLUTION: int = 7
NEIGHBORHOOD_H3_RESOLUTION: int = 8
DISTRICT_H3_RESOLUTION: int = 6
REGIONAL_H3_RESOLUTION: int = 5

# DBSCAN Spatial Clustering Defaults
DEFAULT_DBSCAN_EPS_KM: float = 5.0
DEFAULT_DBSCAN_MIN_SAMPLES: int = 3

# Spatial Risk Band Thresholds
SPATIAL_RISK_BANDS: Dict[str, Tuple[float, float]] = {
    "LOW": (0.0, 29.99),
    "MEDIUM": (30.0, 59.99),
    "HIGH": (60.0, 84.99),
    "CRITICAL": (85.0, 100.0),
}

# Statutory and Evidentiary Notice
GEO_DISCLAIMER: str = (
    "Do not claim that a geospatial risk score or hotspot cluster proves criminal activity. "
    "It represents a model-generated spatial risk signal for tactical intelligence and investigation."
)
