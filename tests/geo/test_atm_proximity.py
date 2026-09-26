"""Unit tests for ATMProximityAnalyzer."""

import pytest
from geo.datasets.rbi_atm_registry import RBIAtmRegistry
from geo.indexing.h3_indexer import H3Indexer
from geo.proximity.atm_proximity import ATMProximityAnalyzer


@pytest.fixture
def atm_analyzer():
    registry = RBIAtmRegistry()
    return ATMProximityAnalyzer(registry=registry)


def test_find_nearest_atms(atm_analyzer):
    # Query point in Mumbai
    lat, lng = 18.9220, 72.8347
    results = atm_analyzer.find_nearest_atms(lat, lng, top_k=3, max_radius_km=15.0)
    assert len(results) == 3
    # Sorted by distance
    assert results[0]["distance_km"] <= results[1]["distance_km"]
    assert "outlet_id" in results[0]
    assert "bank_name" in results[0]
    assert "distance_meters" in results[0]
    assert results[0]["distance_meters"] > 0


def test_find_nearest_atms_for_cell(atm_analyzer):
    # Cell in Connaught Place, New Delhi
    cell = H3Indexer.point_to_h3(28.6315, 77.2167, resolution=7)
    results = atm_analyzer.find_nearest_atms_for_cell(cell, top_k=3)
    assert len(results) == 3
    assert results[0]["distance_km"] < 5.0


def test_calculate_atm_proximity_score():
    # Immediate vicinity (< 100m)
    score_immediate = ATMProximityAnalyzer.calculate_atm_proximity_score(0.05, is_cashout=True, is_nighttime=True)
    # Far distance (10km)
    score_far = ATMProximityAnalyzer.calculate_atm_proximity_score(10.0, is_cashout=False, is_nighttime=False)

    assert score_immediate > 0.8
    assert score_far < 0.05
    assert score_immediate > score_far
