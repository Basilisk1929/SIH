"""Integration tests for GeospatialIntelligenceEngine and FastAPI REST microservice."""

from fastapi.testclient import TestClient
import pytest

from geo.api.service import app
from geo.indexing.h3_indexer import H3Indexer
from geo.intelligence import GeospatialIntelligenceEngine

client = TestClient(app)


@pytest.fixture(scope="module")
def engine():
    eng = GeospatialIntelligenceEngine()
    eng.load_synthetic_data()
    return eng


def test_engine_analyze_cell_and_disclaimer(engine):
    all_profiles = engine.get_all_cell_profiles()
    assert len(all_profiles) > 0

    sample_cell = all_profiles[0]["h3_cell"]
    res = engine.analyze_cell(sample_cell)

    assert "h3_cell" in res
    assert "transaction_count" in res
    assert "complaint_count" in res
    assert "fraud_count" in res
    assert "risk_score" in res
    assert "hotspot_cluster" in res
    assert "nearest_atms" in res
    assert "disclaimer" in res
    assert "Do not claim that a geospatial risk score" in res["disclaimer"]


def test_engine_analyze_coordinate(engine):
    # Jamtara coordinates
    lat, lng = 23.9614, 86.8016
    res = engine.analyze_coordinate(lat, lng)

    assert "h3_cell" in res
    assert res["risk_score"] >= 0.0
    assert len(res["nearest_atms"]) > 0


def test_api_cell_analysis():
    cell = H3Indexer.point_to_h3(28.6139, 77.2090, resolution=7)
    response = client.post("/geo/cell-analysis", json={"h3_cell": cell})
    assert response.status_code == 200
    data = response.json()
    assert data["h3_cell"] == cell
    assert "risk_score" in data
    assert "nearest_atms" in data
    assert "disclaimer" in data


def test_api_coordinate_analysis():
    response = client.post(
        "/geo/coordinate-analysis",
        json={"latitude": 28.6139, "longitude": 77.2090, "resolution": 7},
    )
    assert response.status_code == 200
    data = response.json()
    assert "h3_cell" in data
    assert "risk_score" in data
    assert "nearest_atms" in data


def test_api_nearest_atms():
    response = client.get("/geo/nearest-atms?lat=18.9220&lng=72.8347&top_k=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] == 3
    assert len(data["nearest_atms"]) == 3
    assert data["nearest_atms"][0]["distance_km"] <= data["nearest_atms"][1]["distance_km"]


def test_api_hotspots():
    response = client.get("/geo/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert "clusters" in data
    assert data["total_clusters"] > 0


def test_api_temporal():
    response = client.get("/geo/temporal")
    assert response.status_code == 200
    data = response.json()
    assert "transactions_temporal" in data
    assert "complaints_temporal" in data


def test_api_geojson_h3_cells():
    response = client.get("/geo/geojson/h3-cells")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    assert data["features"][0]["geometry"]["type"] == "Polygon"


def test_api_chicago_validation_benchmark():
    response = client.get("/geo/validation/chicago-benchmark")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALIDATED"
    assert data["is_indian_cybercrime"] is False


def test_api_health():
    response = client.get("/geo/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
