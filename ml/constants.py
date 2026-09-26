"""Constants, feature schemas, and default paths for the risk engine."""

from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "ml" / "artifacts"
DEFAULT_MODEL_PATH = ARTIFACTS_DIR / "risk_model_xgb.json"
DEFAULT_CONFIG_PATH = ARTIFACTS_DIR / "feature_config.json"

DISCLAIMER_TEXT = (
    "Do not claim that a risk score proves criminal activity. "
    "It represents a model-generated risk signal for investigation."
)

RISK_BANDS: List[Tuple[str, float]] = [
    ("CRITICAL", 85.0),
    ("HIGH", 60.0),
    ("MEDIUM", 30.0),
    ("LOW", 0.0),
]

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
