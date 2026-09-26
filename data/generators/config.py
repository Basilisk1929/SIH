"""Configuration and scaling profiles for synthetic cybercrime & transaction generation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Literal


@dataclass(frozen=True)
class ScaleProfile:
    name: str
    target_transactions: int
    num_customers: int
    num_accounts: int
    num_upi_ids: int
    num_devices: int
    num_locations: int
    num_fraud_clusters: int
    target_complaints: int
    target_atm_interactions: int
    fraud_transaction_ratio: float = 0.22


SCALE_PROFILES: Dict[str, ScaleProfile] = {
    "10K": ScaleProfile(
        name="10K",
        target_transactions=10_000,
        num_customers=1_500,
        num_accounts=2_000,
        num_upi_ids=2_500,
        num_devices=1_600,
        num_locations=250,
        num_fraud_clusters=35,
        target_complaints=850,
        target_atm_interactions=1_200,
        fraud_transaction_ratio=0.25,
    ),
    "50K": ScaleProfile(
        name="50K",
        target_transactions=50_000,
        num_customers=7_500,
        num_accounts=10_000,
        num_upi_ids=12_500,
        num_devices=8_000,
        num_locations=500,
        num_fraud_clusters=140,
        target_complaints=3_800,
        target_atm_interactions=5_500,
        fraud_transaction_ratio=0.24,
    ),
    "100K": ScaleProfile(
        name="100K",
        target_transactions=100_000,
        num_customers=15_000,
        num_accounts=20_000,
        num_upi_ids=25_000,
        num_devices=16_000,
        num_locations=800,
        num_fraud_clusters=280,
        target_complaints=7_500,
        target_atm_interactions=11_000,
        fraud_transaction_ratio=0.23,
    ),
    "500K": ScaleProfile(
        name="500K",
        target_transactions=500_000,
        num_customers=75_000,
        num_accounts=100_000,
        num_upi_ids=125_000,
        num_devices=80_000,
        num_locations=1_500,
        num_fraud_clusters=1_200,
        target_complaints=36_000,
        target_atm_interactions=55_000,
        fraud_transaction_ratio=0.22,
    ),
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SYNTHETIC_DATA_DIR = PROJECT_ROOT / "data" / "synthetic"

OUTPUT_DIRS = {
    "accounts": SYNTHETIC_DATA_DIR / "accounts",
    "transactions": SYNTHETIC_DATA_DIR / "transactions",
    "complaints": SYNTHETIC_DATA_DIR / "complaints",
    "entities": SYNTHETIC_DATA_DIR / "entities",
    "fraud_clusters": SYNTHETIC_DATA_DIR / "fraud_clusters",
}

DEFAULT_SEED = 42
ExportFormat = Literal["csv", "parquet", "both"]
