"""Unit tests for CoordinateValidator."""

import numpy as np
import pandas as pd
import pytest

from geo.validation.coordinate_validator import (
    CoordinateValidationError,
    CoordinateValidator,
)


def test_valid_indian_coordinates():
    # New Delhi
    valid, err = CoordinateValidator.validate_point(28.6139, 77.2090, require_india=True)
    assert valid is True
    assert err is None

    # Mumbai
    valid, err = CoordinateValidator.validate_point(18.9220, 72.8347, require_india=True)
    assert valid is True
    assert err is None


def test_valid_global_coordinates():
    # London (outside India)
    valid, err = CoordinateValidator.validate_point(51.5074, -0.1278, require_india=False)
    assert valid is True
    assert err is None

    # Fails when require_india=True
    valid, err = CoordinateValidator.validate_point(51.5074, -0.1278, require_india=True)
    assert valid is False
    assert "outside Indian" in err


def test_out_of_bounds_coordinates():
    # Lat > 90
    valid, err = CoordinateValidator.validate_point(95.0, 77.0)
    assert valid is False
    assert "Latitude 95.0 outside" in err

    # Lng < -180
    valid, err = CoordinateValidator.validate_point(20.0, -190.0)
    assert valid is False
    assert "Longitude -190.0 outside" in err


def test_inverted_coordinates_detection_and_autoswap():
    # Swapped lat/lng for Delhi: lat=77.2090, lng=28.6139
    valid, err = CoordinateValidator.validate_point(77.2090, 28.6139)
    assert valid is False
    assert "inverted/swapped" in err

    # Autoswap normalizer
    norm_lat, norm_lng = CoordinateValidator.normalize_point(77.2090, 28.6139, auto_swap_if_inverted=True)
    assert norm_lat == 28.6139
    assert norm_lng == 77.2090


def test_non_numeric_and_null_coordinates():
    valid, err = CoordinateValidator.validate_point(None, 77.0)
    assert valid is False

    valid, err = CoordinateValidator.validate_point("abc", 77.0)
    assert valid is False

    valid, err = CoordinateValidator.validate_point(np.nan, 77.0)
    assert valid is False


def test_validate_dataframe():
    df = pd.DataFrame([
        {"id": 1, "latitude": 28.6139, "longitude": 77.2090},  # Valid Delhi
        {"id": 2, "latitude": 18.9220, "longitude": 72.8347},  # Valid Mumbai
        {"id": 3, "latitude": 105.0, "longitude": 77.0},       # Out of bounds lat
        {"id": 4, "latitude": None, "longitude": 77.0},        # None lat
    ])

    valid_df, invalid_df = CoordinateValidator.validate_dataframe(df)
    assert len(valid_df) == 2
    assert len(invalid_df) == 2
    assert "rejection_reason" in invalid_df.columns
