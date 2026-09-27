"""FastAPI routes for Geospatial Intelligence subsystem."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from geo.api.schemas import (
    CellAnalysisRequest,
    CoordinateAnalysisRequest,
    SpatialRiskResponse,
)
from geo.intelligence import GeospatialIntelligenceEngine
from geo.prediction.predictor import CashoutLocationPredictor
from geo.prediction.schemas import (
    CashoutPredictionRequest,
    CashoutPredictionResponse,
)

router = APIRouter(prefix="/geo", tags=["Geospatial Intelligence"])
_engine: Optional[GeospatialIntelligenceEngine] = None


def get_engine() -> GeospatialIntelligenceEngine:
    """Singleton getter for GeospatialIntelligenceEngine."""
    global _engine
    if _engine is None:
        _engine = GeospatialIntelligenceEngine()
        _engine.load_synthetic_data()
    return _engine


@router.post("/cell-analysis", response_model=SpatialRiskResponse)
def analyze_h3_cell(request: CellAnalysisRequest):
    """Analyze cyber risk, fraud volume, and nearest ATMs for an H3 cell."""
    engine = get_engine()
    try:
        result = engine.analyze_cell(request.h3_cell)
        return SpatialRiskResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/coordinate-analysis", response_model=SpatialRiskResponse)
def analyze_coordinate(request: CoordinateAnalysisRequest):
    """Convert (lat, lng) to H3 cell and evaluate spatial cyber risk and ATM proximity."""
    engine = get_engine()
    try:
        result = engine.analyze_coordinate(
            lat=request.latitude,
            lng=request.longitude,
            resolution=request.resolution,
        )
        return SpatialRiskResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/nearest-atms")
def get_nearest_atms(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lng: float = Query(..., ge=-180.0, le=180.0),
    top_k: int = Query(5, ge=1, le=25),
    max_radius_km: float = Query(25.0, gt=0.0, le=100.0),
):
    """Find closest operational RBI ATMs and cash recyclers."""
    engine = get_engine()
    try:
        atms = engine.get_nearest_atms(
            lat=lat,
            lng=lng,
            top_k=top_k,
            max_radius_km=max_radius_km,
        )
        return {
            "query_point": {"latitude": lat, "longitude": lng},
            "total_found": len(atms),
            "nearest_atms": atms,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hotspots")
def get_dbscan_hotspots():
    """Retrieve all detected DBSCAN cybercrime complaint/cashout hotspot clusters."""
    engine = get_engine()
    clusters = engine.get_hotspot_clusters()
    return {
        "total_clusters": len(clusters),
        "clusters": clusters,
    }


@router.get("/temporal")
def get_temporal_analysis():
    """Analyze time-of-day and day-of-week patterns for transactions and cyber complaints."""
    engine = get_engine()
    return engine.analyze_temporal()


@router.get("/geojson/h3-cells")
def get_h3_geojson(min_risk_score: float = Query(0.0, ge=0.0, le=100.0)):
    """Return RFC 7946 visualizable GeoJSON FeatureCollection of hexagonal risk cells."""
    engine = get_engine()
    return engine.export_h3_geojson(min_risk_score=min_risk_score)


@router.get("/geojson/hotspots")
def get_hotspots_geojson():
    """Return RFC 7946 GeoJSON of DBSCAN cluster centroids and convex hulls."""
    engine = get_engine()
    return engine.export_hotspots_geojson()


@router.get("/geojson/atms")
def get_atms_geojson(max_records: int = Query(300, ge=1, le=2000)):
    """Return RFC 7946 GeoJSON Point features for RBI ATM network."""
    engine = get_engine()
    return engine.export_atms_geojson(max_records=max_records)


@router.get("/validation/chicago-benchmark")
def run_chicago_validation_benchmark():
    """Execute spatial algorithm validation against Chicago open crime benchmark dataset."""
    engine = get_engine()
    return engine.run_chicago_benchmark()


@router.post("/predict-cashout-location", response_model=CashoutPredictionResponse)
def predict_cashout_location(request: CashoutPredictionRequest):
    """Predict and rank nearby operational RBI ATMs by likelihood of future cash-out activity."""
    engine = get_engine()
    predictor = CashoutLocationPredictor(rbi_registry=engine.rbi_registry, geo_engine=engine)
    try:
        return predictor.predict(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cashout prediction failure: {str(e)}")


@router.get("/prediction/linkage-metadata")
def get_synthetic_cashout_linkage_metadata():
    """Retrieve explicit statutory data limitation metadata regarding synthetic PaySim-RBI ATM linkage."""
    from geo.prediction.synthetic_linkage import SyntheticCashoutLinkage
    engine = get_engine()
    linkage = SyntheticCashoutLinkage(rbi_registry=engine.rbi_registry)
    return linkage.get_metadata()


@router.get("/health")
def health_check():
    """Geospatial Intelligence service health verification."""
    return {
        "status": "HEALTHY",
        "service": "Geospatial Intelligence Engine",
        "spatial_indexing": "H3 v4",
        "clustering_algorithm": "scikit-learn DBSCAN (haversine)",
        "prediction_subsystem": "Cash-Out Location Prediction Engine (RBI-linked)",
    }
