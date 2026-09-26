"""H3 discrete global grid system indexing and hexagonal spatial operations."""

from typing import Any, Dict, List, Optional, Set, Tuple
import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Polygon

from geo.constants import DEFAULT_H3_RESOLUTION
from geo.validation.coordinate_validator import CoordinateValidator


class H3Indexer:
    """Manages Uber H3 hierarchical hexagonal spatial indexing."""

    @classmethod
    def point_to_h3(
        cls,
        lat: float,
        lng: float,
        resolution: int = DEFAULT_H3_RESOLUTION,
        validate: bool = True,
    ) -> str:
        """Convert a (lat, lng) coordinate pair into an H3 hexagonal cell index."""
        if validate:
            valid, err = CoordinateValidator.validate_point(lat, lng)
            if not valid:
                raise ValueError(f"Invalid coordinate for H3 indexing: {err}")

        return h3.latlng_to_cell(float(lat), float(lng), int(resolution))

    @classmethod
    def h3_to_point(cls, h3_cell: str) -> Tuple[float, float]:
        """Get the latitude and longitude centroid of an H3 cell."""
        lat, lng = h3.cell_to_latlng(str(h3_cell).strip())
        return round(lat, 6), round(lng, 6)

    @classmethod
    def h3_to_boundary(
        cls,
        h3_cell: str,
        geojson_order: bool = True,
        close_ring: bool = True,
    ) -> List[Tuple[float, float]]:
        """Return the polygon boundary vertices of an H3 hexagon.

        Args:
            h3_cell: H3 index string.
            geojson_order: If True, returns (lng, lat) for RFC 7946 GeoJSON.
                           If False, returns (lat, lng).
            close_ring: If True, appends the first coordinate to the end.
        """
        raw_boundary = h3.cell_to_boundary(str(h3_cell).strip())
        coords: List[Tuple[float, float]] = []

        for lat, lng in raw_boundary:
            if geojson_order:
                coords.append((round(lng, 6), round(lat, 6)))
            else:
                coords.append((round(lat, 6), round(lng, 6)))

        if close_ring and coords and coords[0] != coords[-1]:
            coords.append(coords[0])

        return coords

    @classmethod
    def h3_to_shapely_polygon(cls, h3_cell: str) -> Polygon:
        """Convert H3 cell boundary into a Shapely Polygon (in GeoJSON [lng, lat] coordinate order)."""
        boundary = cls.h3_to_boundary(h3_cell, geojson_order=True, close_ring=True)
        return Polygon(boundary)

    @classmethod
    def get_neighbors(cls, h3_cell: str, k: int = 1) -> Set[str]:
        """Return all neighboring H3 cells within grid distance k (grid disk)."""
        return set(h3.grid_disk(str(h3_cell).strip(), int(k)))

    @classmethod
    def cell_distance(cls, cell1: str, cell2: str) -> int:
        """Calculate grid distance (number of cell steps) between two H3 cells."""
        return int(h3.grid_distance(str(cell1).strip(), str(cell2).strip()))

    @classmethod
    def to_parent(cls, h3_cell: str, parent_resolution: int) -> str:
        """Get the coarser parent H3 cell at parent_resolution."""
        return h3.cell_to_parent(str(h3_cell).strip(), int(parent_resolution))

    @classmethod
    def to_children(cls, h3_cell: str, child_resolution: int) -> Set[str]:
        """Get all finer children H3 cells at child_resolution."""
        return set(h3.cell_to_children(str(h3_cell).strip(), int(child_resolution)))

    @classmethod
    def is_valid_cell(cls, h3_cell: str) -> bool:
        """Check whether a string represents a valid H3 cell index."""
        try:
            return h3.is_valid_cell(str(h3_cell).strip())
        except Exception:
            return False

    @classmethod
    def add_h3_column(
        cls,
        df: pd.DataFrame,
        lat_col: str = "latitude",
        lng_col: str = "longitude",
        resolution: int = DEFAULT_H3_RESOLUTION,
        output_col: str = "h3_cell",
    ) -> pd.DataFrame:
        """Add an H3 index column to a pandas DataFrame."""
        result_df = df.copy()

        def _to_h3(row: pd.Series) -> Optional[str]:
            lat = row.get(lat_col)
            lng = row.get(lng_col)
            if lat is None or lng is None or pd.isna(lat) or pd.isna(lng):
                return None
            try:
                return cls.point_to_h3(lat, lng, resolution=resolution, validate=False)
            except Exception:
                return None

        result_df[output_col] = result_df.apply(_to_h3, axis=1)
        return result_df

    @classmethod
    def to_geodataframe(
        cls,
        df_with_h3: pd.DataFrame,
        h3_col: str = "h3_cell",
    ) -> gpd.GeoDataFrame:
        """Convert a DataFrame containing an H3 column to a GeoPandas GeoDataFrame with Polygon geometries."""
        if h3_col not in df_with_h3.columns:
            raise ValueError(f"Column '{h3_col}' not found in DataFrame")

        valid_df = df_with_h3[df_with_h3[h3_col].notna()].copy()
        geometries = [cls.h3_to_shapely_polygon(cell) for cell in valid_df[h3_col]]

        gdf = gpd.GeoDataFrame(valid_df, geometry=geometries, crs="EPSG:4326")
        return gdf
