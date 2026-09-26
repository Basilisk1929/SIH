"""Feature engineering pipeline for financial transaction risk detection."""

from collections import defaultdict, deque
import logging
import math
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

FEATURE_COLUMNS: List[str] = [
    "transaction_amount",
    "transaction_frequency",
    "transactions_last_1h",
    "transactions_last_24h",
    "unique_receivers",
    "unique_senders",
    "cashout_ratio",
    "account_age",
    "graph_degree",
    "graph_centrality",
    "complaint_link_count",
    "geographic_distance",
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers."""
    if lat1 == 0.0 and lon1 == 0.0 and lat2 == 0.0 and lon2 == 0.0:
        return 0.0

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(6371.0 * c, 2)


class TransactionFeatureEngineer:
    """Computes leak-free behavioral, temporal, graph, and geographical risk features."""

    def __init__(
        self,
        accounts_df: Optional[pd.DataFrame] = None,
        complaints_df: Optional[pd.DataFrame] = None,
        locations_df: Optional[pd.DataFrame] = None,
        atms_df: Optional[pd.DataFrame] = None,
    ):
        self.accounts_map: Dict[str, Dict[str, any]] = {}
        self.complaint_counts: Dict[str, int] = defaultdict(int)
        self.location_coords: Dict[str, Tuple[float, float]] = {}
        self.account_cashouts: Dict[str, float] = defaultdict(float)

        self._build_static_lookups(accounts_df, complaints_df, locations_df, atms_df)

    def _build_static_lookups(
        self,
        accounts_df: Optional[pd.DataFrame],
        complaints_df: Optional[pd.DataFrame],
        locations_df: Optional[pd.DataFrame],
        atms_df: Optional[pd.DataFrame],
    ) -> None:
        """Index external reference tables for high-throughput feature joins."""
        # 1. Accounts
        if accounts_df is not None and not accounts_df.empty:
            for _, row in accounts_df.iterrows():
                acc_num = str(row["account_number"])
                opening = pd.to_datetime(row.get("opening_date", "2023-01-01"), utc=True)
                self.accounts_map[acc_num] = {
                    "opening_date": opening,
                    "location_id": str(row.get("location_id", "")),
                }

        # 2. Complaints
        if complaints_df is not None and not complaints_df.empty:
            for _, row in complaints_df.iterrows():
                suspect = row.get("suspect_account_number")
                if pd.notna(suspect) and str(suspect).strip():
                    self.complaint_counts[str(suspect).strip()] += 1
                victim = row.get("victim_account_number")
                if pd.notna(victim) and str(victim).strip():
                    self.complaint_counts[str(victim).strip()] += 1

        # 3. Locations
        if locations_df is not None and not locations_df.empty:
            for _, row in locations_df.iterrows():
                loc_id = str(row["location_id"])
                lat = float(row.get("latitude", 0.0))
                lon = float(row.get("longitude", 0.0))
                self.location_coords[loc_id] = (lat, lon)

        # 4. ATM Cashouts
        if atms_df is not None and not atms_df.empty:
            for _, row in atms_df.iterrows():
                acc_num = str(row.get("account_number", "")).strip()
                amt = float(row.get("amount", 0.0))
                if acc_num:
                    self.account_cashouts[acc_num] += amt

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all 12 behavioral and network features in strict chronological order."""
        if df.empty:
            return pd.DataFrame(columns=FEATURE_COLUMNS)

        n = len(df)
        logger.info(f"Computing 12 risk features for {n} transactions without data leakage...")

        # Feature output arrays
        f_amount = np.zeros(n, dtype=float)
        f_frequency = np.zeros(n, dtype=float)
        f_txns_1h = np.zeros(n, dtype=float)
        f_txns_24h = np.zeros(n, dtype=float)
        f_unique_receivers = np.zeros(n, dtype=float)
        f_unique_senders = np.zeros(n, dtype=float)
        f_cashout_ratio = np.zeros(n, dtype=float)
        f_account_age = np.zeros(n, dtype=float)
        f_graph_degree = np.zeros(n, dtype=float)
        f_graph_centrality = np.zeros(n, dtype=float)
        f_complaint_links = np.zeros(n, dtype=float)
        f_geo_distance = np.zeros(n, dtype=float)

        # Stateful trackers (strictly past events)
        sender_timestamps: Dict[str, deque] = defaultdict(deque)
        sender_first_seen: Dict[str, float] = {}
        sender_tx_count: Dict[str, int] = defaultdict(int)
        sender_total_volume: Dict[str, float] = defaultdict(float)

        sender_receivers: Dict[str, set] = defaultdict(set)
        receiver_senders: Dict[str, set] = defaultdict(set)

        active_nodes: set = set()

        # Iterate in chronological order
        for idx in range(n):
            row = df.iloc[idx]
            amt = float(row["amount"])
            ts = pd.to_datetime(row["timestamp"], utc=True)
            ts_epoch = ts.timestamp()

            sender = str(row["sender_account_number"])
            receiver = str(row["receiver_account_number"])

            # 1. Transaction Amount
            f_amount[idx] = amt

            # 2 & 3. Rolling Window Velocity (Past 1h and 24h)
            q = sender_timestamps[sender]
            while q and (ts_epoch - q[0]) > 86400.0:  # 24 hours in seconds
                q.popleft()

            # Past 1 hour (3600 seconds)
            c1h = sum(1 for past_t in q if (ts_epoch - past_t) <= 3600.0)
            f_txns_1h[idx] = float(c1h)
            f_txns_24h[idx] = float(len(q))

            # 4. Transaction Frequency (Transactions per day since first seen)
            first_t = sender_first_seen.get(sender, ts_epoch)
            days_active = max(1.0 / 24.0, (ts_epoch - first_t) / 86400.0)
            f_frequency[idx] = round(sender_tx_count[sender] / days_active, 2)

            # 5 & 6. Unique Receivers & Unique Senders
            f_unique_receivers[idx] = float(len(sender_receivers[sender]))
            f_unique_senders[idx] = float(len(receiver_senders[receiver]))

            # 7. Cashout Ratio
            # Receiver's cashout ratio = ATM withdrawals / total inflow volume
            tot_vol = sender_total_volume[receiver] + amt
            receiver_cashout = self.account_cashouts.get(receiver, 0.0)
            f_cashout_ratio[idx] = round(min(1.0, receiver_cashout / max(100.0, tot_vol)), 4)

            # 8. Account Age (Days since account opening)
            acc_meta = self.accounts_map.get(sender)
            if acc_meta:
                opening_dt = acc_meta["opening_date"]
                age_days = max(1.0, (ts - opening_dt).total_seconds() / 86400.0)
                f_account_age[idx] = round(age_days, 1)
            else:
                f_account_age[idx] = 180.0  # Default 6 months

            # 9 & 10. Graph Degree & Graph Centrality
            out_deg = len(sender_receivers[sender])
            in_deg = len(receiver_senders[receiver])
            total_deg = out_deg + in_deg
            f_graph_degree[idx] = float(total_deg)

            active_nodes_count = max(1, len(active_nodes))
            f_graph_centrality[idx] = round(min(1.0, total_deg / max(10.0, float(active_nodes_count) * 0.05)), 4)

            # 11. Complaint Link Count
            f_complaint_links[idx] = float(
                self.complaint_counts.get(sender, 0) + self.complaint_counts.get(receiver, 0)
            )

            # 12. Geographic Distance (Haversine km between sender & receiver)
            s_loc_id = str(row.get("sender_location_id", ""))
            r_loc_id = str(row.get("receiver_location_id", ""))
            coords_s = self.location_coords.get(s_loc_id, (0.0, 0.0))
            coords_r = self.location_coords.get(r_loc_id, (0.0, 0.0))

            if coords_s != (0.0, 0.0) and coords_r != (0.0, 0.0):
                f_geo_distance[idx] = haversine_distance_km(coords_s[0], coords_s[1], coords_r[0], coords_r[1])
            else:
                f_geo_distance[idx] = 0.0

            # --- Update state for subsequent transactions ---
            q.append(ts_epoch)
            if sender not in sender_first_seen:
                sender_first_seen[sender] = ts_epoch
            sender_tx_count[sender] += 1
            sender_total_volume[sender] += amt
            sender_total_volume[receiver] += amt

            sender_receivers[sender].add(receiver)
            receiver_senders[receiver].add(sender)
            active_nodes.add(sender)
            active_nodes.add(receiver)

        features_df = pd.DataFrame(
            {
                "transaction_amount": f_amount,
                "transaction_frequency": f_frequency,
                "transactions_last_1h": f_txns_1h,
                "transactions_last_24h": f_txns_24h,
                "unique_receivers": f_unique_receivers,
                "unique_senders": f_unique_senders,
                "cashout_ratio": f_cashout_ratio,
                "account_age": f_account_age,
                "graph_degree": f_graph_degree,
                "graph_centrality": f_graph_centrality,
                "complaint_link_count": f_complaint_links,
                "geographic_distance": f_geo_distance,
            }
        )

        return features_df
