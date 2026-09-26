"""Geospatial coordinate validation package."""

from geo.validation.coordinate_validator import (
    CoordinateValidator,
    CoordinateValidationError,
)

__all__ = ["CoordinateValidator", "CoordinateValidationError"]
