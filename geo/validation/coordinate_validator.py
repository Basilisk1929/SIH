"""Coordinate validation and bounds verification for geospatial operations."""

import math
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from geo.constants import GLOBAL_BOUNDS, INDIA_BOUNDS


class CoordinateValidationError(ValueError):
    """Raised when geographic coordinates fail validation checks."""
    pass


class CoordinateValidator:
    """Validates geographic latitude and longitude points and dataframes."""

    @classmethod
    def is_valid_float(cls, val: Any) -> bool:
        """Check if value is a valid finite float."""
        if val is None:
            return False
        try:
            f = float(val)
            return not (math.isnan(f) or math.isinf(f))
        except (ValueError, TypeError):
            return False

    @classmethod
    def validate_point(
        cls,
        lat: Any,
        lng: Any,
        require_india: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Validate an individual (lat, lng) coordinate pair.

        Returns (is_valid, error_message).
        """
        if not cls.is_valid_float(lat) or not cls.is_valid_float(lng):
            return False, f"Non-numeric or infinite coordinates: lat={lat}, lng={lng}"

        flat = float(lat)
        flng = float(lng)

        # Global range check
        if not (GLOBAL_BOUNDS["min_lat"] <= flat <= GLOBAL_BOUNDS["max_lat"]):
            return False, f"Latitude {flat} outside global range [-90, 90]"
        if not (GLOBAL_BOUNDS["min_lng"] <= flng <= GLOBAL_BOUNDS["max_lng"]):
            return False, f"Longitude {flng} outside global range [-180, 180]"

        # Inverted coordinate detection (e.g. lng, lat accidentally swapped)
        if (
            INDIA_BOUNDS["min_lng"] <= flat <= INDIA_BOUNDS["max_lng"]
            and INDIA_BOUNDS["min_lat"] <= flng <= INDIA_BOUNDS["max_lat"]
        ):
            return (
                False,
                f"Coordinates appear inverted/swapped: lat={flat} (in India lng range), lng={flng} (in India lat range)",
            )

        # Indian territorial bounds check if requested
        if require_india:
            in_lat = INDIA_BOUNDS["min_lat"] <= flat <= INDIA_BOUNDS["max_lat"]
            in_lng = INDIA_BOUNDS["min_lng"] <= flng <= INDIA_BOUNDS["max_lng"]
            if not (in_lat and in_lng):
                return (
                    False,
                    f"Coordinates ({flat}, {flng}) outside Indian geographical territory",
                )

        return True, None

    @classmethod
    def normalize_point(
        cls,
        lat: Any,
        lng: Any,
        auto_swap_if_inverted: bool = True,
        require_india: bool = False,
    ) -> Tuple[float, float]:
        """Validate, normalize, and optionally auto-correct swapped coordinates."""
        if not cls.is_valid_float(lat) or not cls.is_valid_float(lng):
            raise CoordinateValidationError(
                f"Cannot normalize invalid coordinates: lat={lat}, lng={lng}"
            )

        flat = float(lat)
        flng = float(lng)

        # Check for swapped coordinates in Indian context
        is_swapped = (
            INDIA_BOUNDS["min_lng"] <= flat <= INDIA_BOUNDS["max_lng"]
            and INDIA_BOUNDS["min_lat"] <= flng <= INDIA_BOUNDS["max_lat"]
        )

        if is_swapped and auto_swap_if_inverted:
            flat, flng = flng, flat

        valid, err = cls.validate_point(flat, flng, require_india=require_india)
        if not valid:
            raise CoordinateValidationError(err)

        return round(flat, 6), round(flng, 6)

    @classmethod
    def validate_dataframe(
        cls,
        df: pd.DataFrame,
        lat_col: str = "latitude",
        lng_col: str = "longitude",
        require_india: bool = False,
        auto_swap: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Validate a pandas DataFrame containing coordinate columns.

        Returns:
            valid_df: DataFrame of rows with valid (and normalized) coordinates.
            invalid_df: DataFrame of rejected rows with a 'rejection_reason' column.
        """
        if lat_col not in df.columns or lng_col not in df.columns:
            raise CoordinateValidationError(
                f"Missing coordinate columns '{lat_col}' and/or '{lng_col}' in DataFrame"
            )

        valid_rows: List[Dict[str, Any]] = []
        invalid_rows: List[Dict[str, Any]] = []

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            lat_val = row_dict.get(lat_col)
            lng_val = row_dict.get(lng_col)

            try:
                norm_lat, norm_lng = cls.normalize_point(
                    lat_val,
                    lng_val,
                    auto_swap_if_inverted=auto_swap,
                    require_india=require_india,
                )
                row_dict[lat_col] = norm_lat
                row_dict[lng_col] = norm_lng
                valid_rows.append(row_dict)
            except Exception as e:
                row_dict["rejection_reason"] = str(e)
                invalid_rows.append(row_dict)

        valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
        invalid_cols = list(df.columns) + ["rejection_reason"]
        invalid_df = (
            pd.DataFrame(invalid_rows) if invalid_rows else pd.DataFrame(columns=invalid_cols)
        )

        return valid_df, invalid_df
