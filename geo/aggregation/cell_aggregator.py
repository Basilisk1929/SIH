"""H3 hexagonal cell aggregation of financial transactions, complaints, and spatial risk scoring."""

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from geo.constants import DEFAULT_H3_RESOLUTION, SPATIAL_RISK_BANDS
from geo.indexing.h3_indexer import H3Indexer
from geo.mappings.cyber_hotspots import INDIAN_CYBER_REFERENCE_HUBS
from geo.proximity.atm_proximity import ATMProximityAnalyzer


@dataclass
class H3CellRiskProfile:
    h3_cell: str
    latitude: float
    longitude: float
    transaction_count: int
    complaint_count: int
    fraud_count: int
    fraud_ratio: float
    total_transaction_amount: float
    total_complaint_loss: float
    risk_score: float
    risk_band: str
    hotspot_cluster: int
    nearest_atms: List[Dict[str, Any]]
    dominant_scam_type: Optional[str] = None
    nearest_cyber_hub: Optional[str] = None
    distance_to_cyber_hub_km: Optional[float] = None


class H3CellAggregator:
    """Aggregates transactional and investigative complaint events into H3 hexagonal cells."""

    def __init__(self, resolution: int = DEFAULT_H3_RESOLUTION):
        self.resolution = int(resolution)

    def aggregate_transactions(
        self,
        transactions_df: pd.DataFrame,
        locations_df: Optional[pd.DataFrame] = None,
        lat_col: str = "latitude",
        lng_col: str = "longitude",
    ) -> pd.DataFrame:
        """Aggregate transaction records into H3 cells."""
        if transactions_df.empty:
            return pd.DataFrame(columns=[
                "h3_cell", "transaction_count", "fraud_count", "fraud_ratio",
                "total_transaction_amount", "avg_transaction_amount",
                "unique_senders", "unique_receivers",
            ])

        df = transactions_df.copy()

        # Join locations if lat/lng are not already in transactions_df
        if lat_col not in df.columns or lng_col not in df.columns:
            if locations_df is not None and "sender_location_id" in df.columns:
                loc_map = locations_df.set_index("location_id")[[lat_col, lng_col]].to_dict("index")
                df[lat_col] = df["sender_location_id"].map(lambda x: loc_map.get(x, {}).get(lat_col))
                df[lng_col] = df["sender_location_id"].map(lambda x: loc_map.get(x, {}).get(lng_col))
            else:
                raise ValueError("Transactions dataframe missing coordinate columns or location mapping")

        df = df[df[lat_col].notna() & df[lng_col].notna()].copy()
        if df.empty:
            return pd.DataFrame()

        # Compute H3 cells
        df["h3_cell"] = df.apply(
            lambda r: H3Indexer.point_to_h3(r[lat_col], r[lng_col], resolution=self.resolution, validate=False),
            axis=1,
        )

        # Boolean fraud normalization
        if "is_fraud" in df.columns:
            df["is_fraud_numeric"] = df["is_fraud"].astype(int)
        else:
            df["is_fraud_numeric"] = 0

        amount_col = "amount" if "amount" in df.columns else "amount_inr" if "amount_inr" in df.columns else None

        grouped = df.groupby("h3_cell").agg(
            transaction_count=("h3_cell", "count"),
            fraud_count=("is_fraud_numeric", "sum"),
            total_transaction_amount=(amount_col, "sum") if amount_col else ("h3_cell", lambda x: 0.0),
            avg_transaction_amount=(amount_col, "mean") if amount_col else ("h3_cell", lambda x: 0.0),
            unique_senders=("sender_account_number", "nunique") if "sender_account_number" in df.columns else ("h3_cell", lambda x: 0),
            unique_receivers=("receiver_account_number", "nunique") if "receiver_account_number" in df.columns else ("h3_cell", lambda x: 0),
        ).reset_index()

        grouped["fraud_ratio"] = (grouped["fraud_count"] / grouped["transaction_count"]).round(4)
        grouped["total_transaction_amount"] = grouped["total_transaction_amount"].round(2)
        grouped["avg_transaction_amount"] = grouped["avg_transaction_amount"].round(2)

        return grouped

    def aggregate_complaints(
        self,
        complaints_df: pd.DataFrame,
        locations_df: Optional[pd.DataFrame] = None,
        lat_col: str = "latitude",
        lng_col: str = "longitude",
    ) -> pd.DataFrame:
        """Aggregate cybercrime complaint incident reports into H3 cells."""
        if complaints_df.empty:
            return pd.DataFrame(columns=[
                "h3_cell", "complaint_count", "total_complaint_loss",
                "avg_complaint_loss", "dominant_scam_type",
            ])

        df = complaints_df.copy()

        # If lat/lng missing, attempt to map from locations_df by city/state
        if lat_col not in df.columns or lng_col not in df.columns:
            if locations_df is not None:
                city_loc_map = {}
                for _, r in locations_df.iterrows():
                    c_name = str(r["city"]).strip().lower()
                    if c_name not in city_loc_map:
                        city_loc_map[c_name] = (r[lat_col], r[lng_col])

                def _get_coords(row: pd.Series) -> Tuple[Optional[float], Optional[float]]:
                    # Check suspect_state, suspect_city, victim_state, victim_city
                    for candidate_col in ["suspect_state", "suspect_city", "victim_state", "victim_city"]:
                        val = str(row.get(candidate_col, "")).strip().lower()
                        if val in city_loc_map:
                            return city_loc_map[val]
                    return None, None

                coords_series = df.apply(_get_coords, axis=1)
                df[lat_col] = [c[0] for c in coords_series]
                df[lng_col] = [c[1] for c in coords_series]
            else:
                raise ValueError("Complaints dataframe missing coordinates or location mapping")

        df = df[df[lat_col].notna() & df[lng_col].notna()].copy()
        if df.empty:
            return pd.DataFrame()

        df["h3_cell"] = df.apply(
            lambda r: H3Indexer.point_to_h3(r[lat_col], r[lng_col], resolution=self.resolution, validate=False),
            axis=1,
        )

        loss_col = None
        for candidate_loss in ["reported_loss_amount", "amount_lost", "amount"]:
            if candidate_loss in df.columns:
                loss_col = candidate_loss
                break

        scam_col = None
        for candidate_scam in ["category", "ground_truth_category", "scam_category", "scam_type"]:
            if candidate_scam in df.columns:
                scam_col = candidate_scam
                break

        records: List[Dict[str, Any]] = []
        for cell, group in df.groupby("h3_cell"):
            cnt = len(group)
            tot_loss = float(group[loss_col].sum()) if loss_col else 0.0
            avg_loss = float(group[loss_col].mean()) if loss_col else 0.0

            dom_scam = None
            if scam_col and not group[scam_col].dropna().empty:
                dom_scam = str(group[scam_col].mode().iloc[0])

            records.append({
                "h3_cell": cell,
                "complaint_count": cnt,
                "total_complaint_loss": round(tot_loss, 2),
                "avg_complaint_loss": round(avg_loss, 2),
                "dominant_scam_type": dom_scam,
            })

        return pd.DataFrame(records)

    def build_unified_cell_profiles(
        self,
        tx_agg_df: pd.DataFrame,
        cmp_agg_df: pd.DataFrame,
        atm_analyzer: Optional[ATMProximityAnalyzer] = None,
        cell_to_cluster_map: Optional[Dict[str, int]] = None,
    ) -> List[H3CellRiskProfile]:
        """Combine transaction and complaint aggregations into unified cell profiles with risk scoring."""
        cell_to_cluster = cell_to_cluster_map or {}
        atm_engine = atm_analyzer or ATMProximityAnalyzer()

        # Merge on h3_cell
        merged = pd.merge(tx_agg_df, cmp_agg_df, on="h3_cell", how="outer")
        if merged.empty:
            return []

        # Fill defaults
        merged["transaction_count"] = merged["transaction_count"].fillna(0).astype(int)
        merged["fraud_count"] = merged["fraud_count"].fillna(0).astype(int)
        merged["fraud_ratio"] = merged["fraud_ratio"].fillna(0.0)
        merged["total_transaction_amount"] = merged["total_transaction_amount"].fillna(0.0)
        merged["complaint_count"] = merged["complaint_count"].fillna(0).astype(int)
        merged["total_complaint_loss"] = merged["total_complaint_loss"].fillna(0.0)
        if "dominant_scam_type" not in merged.columns:
            merged["dominant_scam_type"] = None

        profiles: List[H3CellRiskProfile] = []

        for _, row in merged.iterrows():
            cell = str(row["h3_cell"])
            lat, lng = H3Indexer.h3_to_point(cell)

            tx_cnt = int(row["transaction_count"])
            frd_cnt = int(row["fraud_count"])
            frd_ratio = float(row["fraud_ratio"])
            cmp_cnt = int(row["complaint_count"])
            tot_amt = float(row["total_transaction_amount"])
            tot_loss = float(row["total_complaint_loss"])
            dom_scam = row.get("dominant_scam_type")

            # Check cluster
            cluster_id = cell_to_cluster.get(cell, -1)

            # Nearest ATMs
            nearest_atms = atm_engine.find_nearest_atms(lat, lng, top_k=3, max_radius_km=15.0)

            # Distance to known reference cyber hubs
            closest_hub = None
            min_hub_dist = float("inf")
            for hub in INDIAN_CYBER_REFERENCE_HUBS:
                dlat = math.radians(hub["lat"] - lat)
                dlng = math.radians(hub["lng"] - lng)
                a = (
                    math.sin(dlat / 2) ** 2
                    + math.cos(math.radians(lat))
                    * math.cos(math.radians(hub["lat"]))
                    * math.sin(dlng / 2) ** 2
                )
                dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                if dist_km < min_hub_dist:
                    min_hub_dist = dist_km
                    closest_hub = hub["name"]

            # Spatial Risk Score Calculation (0.0 to 100.0)
            # Component 1: Fraud ratio (0-30 pts)
            fraud_ratio_pts = min(30.0, frd_ratio * 60.0)

            # Component 2: Fraud volume (0-20 pts)
            fraud_vol_pts = min(20.0, frd_cnt * 2.0)

            # Component 3: Complaint volume & loss density (0-25 pts)
            cmp_pts = min(25.0, cmp_cnt * 3.5 + min(10.0, tot_loss / 20000.0))

            # Component 4: DBSCAN Hotspot cluster membership (0-15 pts)
            cluster_pts = 15.0 if cluster_id >= 0 else 0.0

            # Component 5: Cyber hub proximity bonus (0-10 pts within 50km)
            hub_pts = 0.0
            if min_hub_dist <= 25.0:
                hub_pts = 10.0
            elif min_hub_dist <= 60.0:
                hub_pts = 5.0

            raw_score = fraud_ratio_pts + fraud_vol_pts + cmp_pts + cluster_pts + hub_pts
            risk_score = round(min(100.0, max(0.0, raw_score)), 1)

            # Risk Band
            band = "LOW"
            for b_name, (b_min, b_max) in SPATIAL_RISK_BANDS.items():
                if b_min <= risk_score <= b_max:
                    band = b_name
                    break

            profile = H3CellRiskProfile(
                h3_cell=cell,
                latitude=lat,
                longitude=lng,
                transaction_count=tx_cnt,
                complaint_count=cmp_cnt,
                fraud_count=frd_cnt,
                fraud_ratio=frd_ratio,
                total_transaction_amount=tot_amt,
                total_complaint_loss=tot_loss,
                risk_score=risk_score,
                risk_band=band,
                hotspot_cluster=cluster_id,
                nearest_atms=nearest_atms,
                dominant_scam_type=dom_scam if pd.notna(dom_scam) else None,
                nearest_cyber_hub=closest_hub if min_hub_dist <= 100.0 else None,
                distance_to_cyber_hub_km=round(min_hub_dist, 2) if min_hub_dist <= 100.0 else None,
            )
            profiles.append(profile)

        # Sort descending by risk_score
        profiles.sort(key=lambda x: x.risk_score, reverse=True)
        return profiles

    def profiles_to_dataframe(self, profiles: List[H3CellRiskProfile]) -> pd.DataFrame:
        """Convert list of H3CellRiskProfile into a pandas DataFrame."""
        return pd.DataFrame([asdict(p) for p in profiles])
