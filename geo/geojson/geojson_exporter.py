"""RFC 7946 compliant GeoJSON visualizer and exporter for geospatial intelligence."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from geo.aggregation.cell_aggregator import H3CellRiskProfile
from geo.indexing.h3_indexer import H3Indexer


class GeoJSONExporter:
    """Exports spatial cells, DBSCAN clusters, and ATM layers into visualizable GeoJSON."""

    @classmethod
    def export_h3_cells(
        cls,
        profiles: List[H3CellRiskProfile],
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convert a list of H3CellRiskProfile into an RFC 7946 FeatureCollection of Polygon hexagons."""
        features: List[Dict[str, Any]] = []

        for p in profiles:
            # H3 boundary in [lng, lat] order, closed ring
            boundary_coords = H3Indexer.h3_to_boundary(p.h3_cell, geojson_order=True, close_ring=True)
            # GeoJSON coordinates format: [[[lng, lat], [lng, lat], ...]]
            geometry = {
                "type": "Polygon",
                "coordinates": [boundary_coords],
            }

            properties = {
                "h3_cell": p.h3_cell,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "transaction_count": p.transaction_count,
                "complaint_count": p.complaint_count,
                "fraud_count": p.fraud_count,
                "fraud_ratio": p.fraud_ratio,
                "total_transaction_amount": p.total_transaction_amount,
                "total_complaint_loss": p.total_complaint_loss,
                "risk_score": p.risk_score,
                "risk_band": p.risk_band,
                "hotspot_cluster": p.hotspot_cluster,
                "dominant_scam_type": p.dominant_scam_type,
                "nearest_cyber_hub": p.nearest_cyber_hub,
                "distance_to_cyber_hub_km": p.distance_to_cyber_hub_km,
                "nearest_atms_count": len(p.nearest_atms),
            }

            features.append({
                "type": "Feature",
                "id": p.h3_cell,
                "geometry": geometry,
                "properties": properties,
            })

        geojson = {
            "type": "FeatureCollection",
            "name": "h3_cybercrime_risk_cells",
            "features": features,
            "metadata": {
                "total_cells": len(features),
                "high_risk_cells_count": sum(1 for p in profiles if p.risk_score >= 60.0),
            },
        }

        if output_file:
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2)

        return geojson

    @classmethod
    def export_clusters(
        cls,
        cluster_summaries: List[Dict[str, Any]],
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export DBSCAN hotspot clusters as convex hull Polygons or centroid Points."""
        features: List[Dict[str, Any]] = []

        for c in cluster_summaries:
            cid = c.get("cluster_id")
            centroid_lat = c.get("centroid_lat")
            centroid_lng = c.get("centroid_lng")

            # Point Feature for Centroid
            features.append({
                "type": "Feature",
                "id": f"cluster_centroid_{cid}",
                "geometry": {
                    "type": "Point",
                    "coordinates": [centroid_lng, centroid_lat],
                },
                "properties": {
                    "feature_type": "cluster_centroid",
                    "cluster_id": cid,
                    "point_count": c.get("point_count"),
                    "fraud_count": c.get("fraud_count"),
                    "total_amount_inr": c.get("total_amount_inr"),
                    "dominant_pattern": c.get("dominant_pattern"),
                    "radius_km": c.get("radius_km"),
                    "nearest_reference_hub": c.get("nearest_reference_hub"),
                },
            })

            # Convex Hull Polygon Feature if available
            hull = c.get("convex_hull_geojson")
            if hull and "coordinates" in hull:
                features.append({
                    "type": "Feature",
                    "id": f"cluster_hull_{cid}",
                    "geometry": hull,
                    "properties": {
                        "feature_type": "cluster_convex_hull",
                        "cluster_id": cid,
                        "point_count": c.get("point_count"),
                        "radius_km": c.get("radius_km"),
                    },
                })

        geojson = {
            "type": "FeatureCollection",
            "name": "dbscan_hotspot_clusters",
            "features": features,
            "metadata": {
                "total_clusters": len(cluster_summaries),
            },
        }

        if output_file:
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2)

        return geojson

    @classmethod
    def export_atms(
        cls,
        atms_df: pd.DataFrame,
        output_file: Optional[str] = None,
        max_records: int = 1000,
    ) -> Dict[str, Any]:
        """Export ATM locations as GeoJSON Point features."""
        features: List[Dict[str, Any]] = []

        sub_df = atms_df.head(max_records)
        for _, row in sub_df.iterrows():
            lat = float(row.get("latitude", 0.0))
            lng = float(row.get("longitude", 0.0))

            features.append({
                "type": "Feature",
                "id": str(row.get("outlet_id")),
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(lng, 6), round(lat, 6)],
                },
                "properties": {
                    "outlet_id": row.get("outlet_id"),
                    "bank_name": row.get("bank_name"),
                    "bank_code": row.get("bank_code"),
                    "outlet_type": row.get("outlet_type"),
                    "bank_category": row.get("bank_category"),
                    "city": row.get("center_city"),
                    "district": row.get("district"),
                    "state": row.get("state"),
                    "population_group": row.get("population_group"),
                    "is_hotspot_adjacent": bool(row.get("is_hotspot_adjacent", False)),
                },
            })

        geojson = {
            "type": "FeatureCollection",
            "name": "rbi_banking_outlets",
            "features": features,
            "metadata": {
                "total_atms_exported": len(features),
            },
        }

        if output_file:
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2)

        return geojson
