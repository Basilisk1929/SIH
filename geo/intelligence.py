"""Unified Geospatial Intelligence Engine for cybercrime risk detection, H3 cell aggregation, and ATM proximity."""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from geo.aggregation.cell_aggregator import H3CellAggregator, H3CellRiskProfile
from geo.clustering.dbscan_clustering import DBSCANHotspotDetector
from geo.constants import (
    DEFAULT_DBSCAN_EPS_KM,
    DEFAULT_DBSCAN_MIN_SAMPLES,
    DEFAULT_H3_RESOLUTION,
    GEO_DISCLAIMER,
)
from geo.datasets.rbi_atm_registry import RBIAtmRegistry
from geo.datasets.validation.chicago_benchmark import ChicagoCrimeValidationBenchmark
from geo.geojson.geojson_exporter import GeoJSONExporter
from geo.indexing.h3_indexer import H3Indexer
from geo.proximity.atm_proximity import ATMProximityAnalyzer
from geo.temporal.temporal_analyzer import TemporalAnalyzer
from geo.validation.coordinate_validator import CoordinateValidator


class GeospatialIntelligenceEngine:
    """Orchestrates end-to-end spatial indexing, cell aggregations, DBSCAN clustering, and ATM proximity."""

    def __init__(
        self,
        resolution: int = DEFAULT_H3_RESOLUTION,
        rbi_registry: Optional[RBIAtmRegistry] = None,
        data_dir: Optional[str] = None,
    ):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            root_dir = Path(__file__).resolve().parent.parent
            self.data_dir = root_dir / "data"
        self.resolution = resolution
        self.rbi_registry = rbi_registry or RBIAtmRegistry()
        self.atm_analyzer = ATMProximityAnalyzer(registry=self.rbi_registry)
        self.cell_aggregator = H3CellAggregator(resolution=self.resolution)
        self.hotspot_detector = DBSCANHotspotDetector(
            eps_km=DEFAULT_DBSCAN_EPS_KM,
            min_samples=DEFAULT_DBSCAN_MIN_SAMPLES,
        )

        self._locations_df: Optional[pd.DataFrame] = None
        self._transactions_df: Optional[pd.DataFrame] = None
        self._complaints_df: Optional[pd.DataFrame] = None
        self._cell_profiles: Dict[str, H3CellRiskProfile] = {}
        self._is_initialized = False

    def load_synthetic_data(self) -> None:
        """Load synthetic locations, transactions, and complaints from disk if available."""
        loc_path = self.data_dir / "synthetic" / "entities" / "locations.csv"
        txn_path = self.data_dir / "synthetic" / "transactions" / "transactions.csv"
        cmp_path = self.data_dir / "synthetic" / "complaints" / "complaints.csv"

        if loc_path.exists():
            self._locations_df = pd.read_csv(loc_path)
        if txn_path.exists():
            # Load transactions (sampling up to 10k for fast spatial index build)
            self._transactions_df = pd.read_csv(txn_path, nrows=10000)
        if cmp_path.exists():
            self._complaints_df = pd.read_csv(cmp_path)

        self._build_spatial_intelligence()
        self._is_initialized = True

    def _build_spatial_intelligence(self) -> None:
        """Run DBSCAN and build unified H3 cell risk profiles from loaded datasets."""
        # Step 1: Detect DBSCAN clusters from complaints or transactions
        cell_to_cluster: Dict[str, int] = {}
        if self._complaints_df is not None and not self._complaints_df.empty:
            # Map coordinates to complaints
            cmp_df = self._complaints_df.copy()
            if self._locations_df is not None:
                city_coords = (
                    self._locations_df.drop_duplicates(subset=["city"])
                    .set_index("city")[["latitude", "longitude"]]
                    .to_dict("index")
                )
                def _get_cmp_coords(row: pd.Series):
                    for candidate in ["suspect_state", "suspect_city", "victim_state", "victim_city"]:
                        val = str(row.get(candidate, ""))
                        if val in city_coords:
                            return city_coords[val]["latitude"], city_coords[val]["longitude"]
                    return None, None

                coords = cmp_df.apply(_get_cmp_coords, axis=1)
                cmp_df["latitude"] = [c[0] for c in coords]
                cmp_df["longitude"] = [c[1] for c in coords]

            loss_col = (
                "reported_loss_amount" if "reported_loss_amount" in cmp_df.columns
                else "amount_lost" if "amount_lost" in cmp_df.columns
                else "amount"
            )
            pattern_col = (
                "category" if "category" in cmp_df.columns
                else "ground_truth_category" if "ground_truth_category" in cmp_df.columns
                else "scam_category" if "scam_category" in cmp_df.columns
                else "scam_type"
            )

            clustered_cmp = self.hotspot_detector.fit_predict(
                cmp_df,
                lat_col="latitude",
                lng_col="longitude",
                fraud_col=loss_col,
                amount_col=loss_col,
                pattern_col=pattern_col,
            )
            # Map cells to cluster IDs
            for _, r in clustered_cmp.iterrows():
                if pd.notna(r.get("latitude")) and pd.notna(r.get("longitude")) and r.get("cluster_id", -1) >= 0:
                    c_cell = H3Indexer.point_to_h3(r["latitude"], r["longitude"], resolution=self.resolution, validate=False)
                    cell_to_cluster[c_cell] = int(r["cluster_id"])

        # Step 2: Aggregate Transactions
        tx_agg = pd.DataFrame()
        if self._transactions_df is not None and not self._transactions_df.empty:
            tx_agg = self.cell_aggregator.aggregate_transactions(
                self._transactions_df,
                locations_df=self._locations_df,
            )

        # Step 3: Aggregate Complaints
        cmp_agg = pd.DataFrame()
        if self._complaints_df is not None and not self._complaints_df.empty:
            cmp_agg = self.cell_aggregator.aggregate_complaints(
                self._complaints_df,
                locations_df=self._locations_df,
            )

        # Step 4: Build Unified Profiles
        profiles = self.cell_aggregator.build_unified_cell_profiles(
            tx_agg_df=tx_agg,
            cmp_agg_df=cmp_agg,
            atm_analyzer=self.atm_analyzer,
            cell_to_cluster_map=cell_to_cluster,
        )

        self._cell_profiles = {p.h3_cell: p for p in profiles}

    def analyze_cell(self, h3_cell: str) -> Dict[str, Any]:
        """Query spatial risk profile and nearest ATMs for a specific H3 cell.

        Returns:
            Dictionary with h3_cell, transaction_count, complaint_count,
            fraud_count, risk_score, hotspot_cluster, nearest_atms, disclaimer.
        """
        cell_str = str(h3_cell).strip()
        if not H3Indexer.is_valid_cell(cell_str):
            raise ValueError(f"Invalid H3 cell index: {cell_str}")

        if not self._is_initialized and not self._cell_profiles:
            self.load_synthetic_data()

        profile = self._cell_profiles.get(cell_str)
        if profile is not None:
            res = asdict(profile)
            res["disclaimer"] = GEO_DISCLAIMER
            return res

        # If cell has no recorded events yet, compute baseline profile on the fly
        lat, lng = H3Indexer.h3_to_point(cell_str)
        nearest_atms = self.atm_analyzer.find_nearest_atms(lat, lng, top_k=3, max_radius_km=15.0)
        cluster_id = self.hotspot_detector.assign_point_to_nearest_cluster(lat, lng)

        base_profile = H3CellRiskProfile(
            h3_cell=cell_str,
            latitude=lat,
            longitude=lng,
            transaction_count=0,
            complaint_count=0,
            fraud_count=0,
            fraud_ratio=0.0,
            total_transaction_amount=0.0,
            total_complaint_loss=0.0,
            risk_score=15.0 if cluster_id is not None and cluster_id >= 0 else 5.0,
            risk_band="LOW",
            hotspot_cluster=cluster_id if cluster_id is not None else -1,
            nearest_atms=nearest_atms,
            dominant_scam_type=None,
        )

        res = asdict(base_profile)
        res["disclaimer"] = GEO_DISCLAIMER
        return res

    def analyze_coordinate(
        self,
        lat: float,
        lng: float,
        resolution: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Convert coordinate to H3 cell and analyze spatial intelligence."""
        valid, err = CoordinateValidator.validate_point(lat, lng)
        if not valid:
            raise ValueError(f"Invalid coordinate: {err}")

        res = resolution if resolution is not None else self.resolution
        h3_cell = H3Indexer.point_to_h3(lat, lng, resolution=res)
        return self.analyze_cell(h3_cell)

    def get_all_cell_profiles(self) -> List[Dict[str, Any]]:
        """Return all active H3 cell profiles."""
        if not self._is_initialized:
            self.load_synthetic_data()
        return [asdict(p) for p in self._cell_profiles.values()]

    def get_hotspot_clusters(self) -> List[Dict[str, Any]]:
        """Return detected DBSCAN hotspot cluster summaries."""
        if not self._is_initialized:
            self.load_synthetic_data()
        return self.hotspot_detector.get_cluster_summaries()

    def get_nearest_atms(
        self,
        lat: float,
        lng: float,
        top_k: int = 5,
        max_radius_km: float = 25.0,
    ) -> List[Dict[str, Any]]:
        """Query nearest RBI ATMs and bank outlets."""
        return self.atm_analyzer.find_nearest_atms(
            lat=lat,
            lng=lng,
            top_k=top_k,
            max_radius_km=max_radius_km,
        )

    def analyze_temporal(self) -> Dict[str, Any]:
        """Run time-of-day and day-of-week analysis on transaction and complaint streams."""
        if not self._is_initialized:
            self.load_synthetic_data()

        tx_res = (
            TemporalAnalyzer.analyze_dataframe(self._transactions_df, "timestamp")
            if self._transactions_df is not None
            else {}
        )
        cmp_date_col = (
            "incident_date" if self._complaints_df is not None and "incident_date" in self._complaints_df.columns
            else "incident_datetime"
        )
        cmp_res = (
            TemporalAnalyzer.analyze_dataframe(self._complaints_df, cmp_date_col)
            if self._complaints_df is not None
            else {}
        )

        return {
            "transactions_temporal": tx_res,
            "complaints_temporal": cmp_res,
        }

    def export_h3_geojson(
        self,
        min_risk_score: float = 0.0,
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export H3 cell risk profiles as RFC 7946 visualizable GeoJSON FeatureCollection."""
        if not self._is_initialized:
            self.load_synthetic_data()

        filtered = [
            p for p in self._cell_profiles.values()
            if p.risk_score >= min_risk_score
        ]
        return GeoJSONExporter.export_h3_cells(filtered, output_file=output_file)

    def export_hotspots_geojson(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Export DBSCAN hotspot clusters as RFC 7946 GeoJSON."""
        clusters = self.get_hotspot_clusters()
        return GeoJSONExporter.export_clusters(clusters, output_file=output_file)

    def export_atms_geojson(self, output_file: Optional[str] = None, max_records: int = 500) -> Dict[str, Any]:
        """Export RBI ATM locations as RFC 7946 GeoJSON."""
        df = self.rbi_registry.get_atms_only()
        return GeoJSONExporter.export_atms(df, output_file=output_file, max_records=max_records)

    def run_chicago_benchmark(self) -> Dict[str, Any]:
        """Execute methodology validation against Chicago open crime benchmark dataset."""
        return ChicagoCrimeValidationBenchmark.validate_methodology_pipeline()

    def predict_cashout_locations(
        self,
        account_id: str,
        current_lat: Optional[float] = None,
        current_lng: Optional[float] = None,
        recent_transactions: Optional[List[Dict[str, Any]]] = None,
        candidate_radius_km: float = 15.0,
        top_k: int = 5,
        account_risk_score: Optional[float] = None,
        cashout_ratio: Optional[float] = None,
        transactions_last_1h: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Predict and rank nearby operational RBI ATMs by likelihood of future cash-out activity."""
        from geo.prediction.predictor import CashoutLocationPredictor
        from geo.prediction.schemas import CashoutPredictionRequest

        predictor = CashoutLocationPredictor(rbi_registry=self.rbi_registry, geo_engine=self)
        req = CashoutPredictionRequest(
            account_id=account_id,
            current_latitude=current_lat,
            current_longitude=current_lng,
            recent_transactions=recent_transactions,
            candidate_radius_km=candidate_radius_km,
            top_k=top_k,
            account_risk_score=account_risk_score,
            cashout_ratio=cashout_ratio,
            transactions_last_1h=transactions_last_1h,
        )
        return predictor.predict(req).model_dump()

