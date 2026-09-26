"""Unit tests for GeoJSONExporter."""

from geo.aggregation.cell_aggregator import H3CellRiskProfile
from geo.datasets.rbi_atm_registry import RBIAtmRegistry
from geo.geojson.geojson_exporter import GeoJSONExporter
from geo.indexing.h3_indexer import H3Indexer


def test_export_h3_cells_geojson(tmp_path):
    cell = H3Indexer.point_to_h3(28.6139, 77.2090, resolution=7)
    profile = H3CellRiskProfile(
        h3_cell=cell,
        latitude=28.6139,
        longitude=77.2090,
        transaction_count=15,
        complaint_count=3,
        fraud_count=5,
        fraud_ratio=0.333,
        total_transaction_amount=120000.0,
        total_complaint_loss=60000.0,
        risk_score=72.5,
        risk_band="HIGH",
        hotspot_cluster=1,
        nearest_atms=[],
    )

    out_file = tmp_path / "test_cells.geojson"
    geojson = GeoJSONExporter.export_h3_cells([profile], output_file=str(out_file))

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1

    feature = geojson["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Polygon"
    # RFC 7946: polygon coords is a list of rings
    coords = feature["geometry"]["coordinates"][0]
    assert len(coords) == 7
    # First and last coordinate match (closed ring)
    assert coords[0] == coords[-1]
    # Coordinate order: [longitude, latitude]
    assert coords[0][0] > coords[0][1]  # lng ~77 > lat ~28

    assert feature["properties"]["h3_cell"] == cell
    assert feature["properties"]["risk_score"] == 72.5
    assert out_file.exists()


def test_export_atms_geojson():
    registry = RBIAtmRegistry()
    atms_df = registry.get_atms_only().head(10)
    geojson = GeoJSONExporter.export_atms(atms_df)

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 10
    feature = geojson["features"][0]
    assert feature["geometry"]["type"] == "Point"
    # RFC 7946: [lng, lat]
    assert len(feature["geometry"]["coordinates"]) == 2
    assert "outlet_id" in feature["properties"]
