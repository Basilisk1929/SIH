"""Unit tests for RBIAtmRegistry."""

import pytest
from geo.datasets.rbi_atm_registry import RBIAtmRegistry


@pytest.fixture
def registry(tmp_path):
    csv_file = tmp_path / "rbi_atm_outlets.csv"
    return RBIAtmRegistry(csv_path=str(csv_file))


def test_registry_initialization_and_generation(registry):
    df = registry.get_all_outlets()
    assert not df.empty
    assert len(df) > 100
    assert "outlet_id" in df.columns
    assert "bank_name" in df.columns
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "outlet_type" in df.columns


def test_bank_categories_and_outlet_types(registry):
    df = registry.get_all_outlets()
    categories = set(df["bank_category"].unique())
    assert "PUBLIC_SECTOR" in categories
    assert "PRIVATE_SECTOR" in categories
    assert "WHITE_LABEL" in categories

    outlet_types = set(df["outlet_type"].unique())
    assert "ON_SITE_ATM" in outlet_types
    assert "OFF_SITE_ATM" in outlet_types
    assert "CASH_RECYCLER" in outlet_types


def test_get_atms_only(registry):
    atms_df = registry.get_atms_only()
    assert not atms_df.empty
    # Must only contain active cash dispensing machines
    assert atms_df["cash_dispenser_active"].all()
    assert (atms_df["outlet_type"] != "BANK_BRANCH").all()


def test_filtering_by_state(registry):
    delhi_outlets = registry.get_outlets_in_state("Delhi")
    assert not delhi_outlets.empty
    assert (delhi_outlets["state"].str.lower() == "delhi").all()


def test_find_nearest_atms(registry):
    # Query near Connaught Place, New Delhi
    lat, lng = 28.6315, 77.2167
    nearest = registry.find_nearest_atms(lat, lng, top_k=5, radius_km=10.0)
    assert len(nearest) == 5
    assert nearest[0]["distance_km"] <= nearest[1]["distance_km"]
    assert nearest[0]["city"] == "New Delhi - Connaught Place"
