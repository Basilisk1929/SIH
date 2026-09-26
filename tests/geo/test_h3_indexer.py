"""Unit tests for H3Indexer."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from geo.indexing.h3_indexer import H3Indexer


def test_point_to_h3_and_centroid():
    lat, lng = 28.6139, 77.2090
    cell = H3Indexer.point_to_h3(lat, lng, resolution=7)
    assert isinstance(cell, str)
    assert len(cell) == 15
    assert H3Indexer.is_valid_cell(cell) is True

    c_lat, c_lng = H3Indexer.h3_to_point(cell)
    # Centroid should be within 1.5 km of original coordinate
    assert abs(c_lat - lat) < 0.02
    assert abs(c_lng - lng) < 0.02


def test_h3_to_boundary():
    lat, lng = 19.0760, 72.8777  # Mumbai
    cell = H3Indexer.point_to_h3(lat, lng, resolution=7)

    # GeoJSON order: (lng, lat), closed ring (7 coords for hexagon)
    boundary = H3Indexer.h3_to_boundary(cell, geojson_order=True, close_ring=True)
    assert len(boundary) == 7
    assert boundary[0] == boundary[-1]
    # First element is longitude
    assert 72.0 < boundary[0][0] < 74.0
    # Second element is latitude
    assert 18.0 < boundary[0][1] < 20.0


def test_h3_to_shapely_polygon():
    cell = H3Indexer.point_to_h3(12.9716, 77.5946, resolution=7)  # Bengaluru
    poly = H3Indexer.h3_to_shapely_polygon(cell)
    assert isinstance(poly, Polygon)
    assert poly.is_valid
    assert poly.area > 0.0


def test_get_neighbors_and_distance():
    cell = H3Indexer.point_to_h3(28.6139, 77.2090, resolution=7)
    neighbors = H3Indexer.get_neighbors(cell, k=1)
    # k=1 disk contains center cell + 6 ring neighbors = 7 cells
    assert len(neighbors) == 7
    assert cell in neighbors

    # Distance to self is 0
    assert H3Indexer.cell_distance(cell, cell) == 0

    # Distance to direct neighbor is 1
    direct_neighbor = [c for c in neighbors if c != cell][0]
    assert H3Indexer.cell_distance(cell, direct_neighbor) == 1


def test_parent_and_children():
    cell = H3Indexer.point_to_h3(28.6139, 77.2090, resolution=7)
    parent = H3Indexer.to_parent(cell, parent_resolution=6)
    assert H3Indexer.is_valid_cell(parent)

    children = H3Indexer.to_children(cell, child_resolution=8)
    assert len(children) == 7
    for child in children:
        assert H3Indexer.to_parent(child, 7) == cell


def test_add_h3_column_and_geodataframe():
    df = pd.DataFrame([
        {"city": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
        {"city": "Mumbai", "latitude": 18.9220, "longitude": 72.8347},
    ])

    df_h3 = H3Indexer.add_h3_column(df, resolution=7)
    assert "h3_cell" in df_h3.columns
    assert df_h3["h3_cell"].nunique() == 2

    gdf = H3Indexer.to_geodataframe(df_h3)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs == "EPSG:4326"
    assert "geometry" in gdf.columns
