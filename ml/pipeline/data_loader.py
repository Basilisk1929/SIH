"""Data loading utilities for the financial transaction risk engine."""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SYNTHETIC_DATA_DIR = PROJECT_ROOT / "data" / "synthetic"


class RiskDataLoader:
    """Loads raw transaction, account, complaint, location, and ATM datasets."""

    def __init__(self, data_dir: Path = SYNTHETIC_DATA_DIR):
        self.data_dir = data_dir

    def load_transactions(self, sample_limit: Optional[int] = None) -> pd.DataFrame:
        """Load transactions dataset."""
        csv_path = self.data_dir / "transactions" / "transactions.csv"
        parquet_path = self.data_dir / "transactions" / "transactions.parquet"

        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
        elif csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            raise FileNotFoundError(f"Transactions dataset not found in {self.data_dir}")

        if sample_limit and len(df) > sample_limit:
            import numpy as np
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.sort_values(by="timestamp").reset_index(drop=True)
            indices = np.linspace(0, len(df) - 1, sample_limit, dtype=int)
            df = df.iloc[indices].copy()
        return df

    def load_accounts(self) -> pd.DataFrame:
        """Load accounts metadata."""
        path = self.data_dir / "accounts" / "bank_accounts.csv"
        if not path.exists():
            raise FileNotFoundError(f"Accounts file not found at {path}")
        return pd.read_csv(path)

    def load_complaints(self) -> pd.DataFrame:
        """Load cybercrime complaints metadata."""
        path = self.data_dir / "complaints" / "complaints.csv"
        if not path.exists():
            raise FileNotFoundError(f"Complaints file not found at {path}")
        return pd.read_csv(path)

    def load_locations(self) -> pd.DataFrame:
        """Load geographical coordinates."""
        path = self.data_dir / "entities" / "locations.csv"
        if not path.exists():
            raise FileNotFoundError(f"Locations file not found at {path}")
        return pd.read_csv(path)

    def load_atm_interactions(self) -> pd.DataFrame:
        """Load ATM withdrawal interactions."""
        path = self.data_dir / "entities" / "atm_interactions.csv"
        if not path.exists():
            raise FileNotFoundError(f"ATM interactions file not found at {path}")
        return pd.read_csv(path)

    def load_all_datasets(self, sample_transactions: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """Load all five datasets into memory."""
        logger.info("Loading synthetic financial datasets for risk engine pipeline...")
        return {
            "transactions": self.load_transactions(sample_transactions),
            "accounts": self.load_accounts(),
            "complaints": self.load_complaints(),
            "locations": self.load_locations(),
            "atms": self.load_atm_interactions(),
        }
