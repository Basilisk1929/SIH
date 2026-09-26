"""Pydantic schemas for Geospatial Intelligence REST API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CoordinateAnalysisRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of query point")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of query point")
    resolution: Optional[int] = Field(7, ge=3, le=12, description="H3 hexagon resolution")


class CellAnalysisRequest(BaseModel):
    h3_cell: str = Field(..., min_length=15, max_length=16, description="H3 hexagon cell index")


class NearestATMsQuery(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    top_k: int = Field(5, ge=1, le=50)
    max_radius_km: float = Field(25.0, gt=0.0, le=100.0)


class HotspotDBSCANQuery(BaseModel):
    eps_km: float = Field(5.0, gt=0.1, le=50.0)
    min_samples: int = Field(3, ge=2, le=50)


class SpatialRiskResponse(BaseModel):
    h3_cell: str
    latitude: float
    longitude: float
    transaction_count: int
    complaint_count: int
    fraud_count: int
    fraud_ratio: float
    total_transaction_amount: float
    total_complaint_loss: float
    risk_score: float
    risk_band: str
    hotspot_cluster: int
    nearest_atms: List[Dict[str, Any]]
    dominant_scam_type: Optional[str] = None
    nearest_cyber_hub: Optional[str] = None
    distance_to_cyber_hub_km: Optional[float] = None
    disclaimer: str
