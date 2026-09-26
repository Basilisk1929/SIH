"""Data preprocessor preparing transactions for feature engineering and ML training."""

import logging
from typing import Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class TransactionPreprocessor:
    """Cleans, formats, and chronologically orders financial transactions."""

    REQUIRED_COLUMNS = [
        "transaction_id",
        "sender_account_number",
        "receiver_account_number",
        "amount",
        "timestamp",
    ]

    @classmethod
    def preprocess_transactions(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Validate, clean, cast, and sort transactions chronologically."""
        if df.empty:
            raise ValueError("Input transaction DataFrame is empty")

        for col in cls.REQUIRED_COLUMNS:
            if col not in df.columns:
                raise ValueError(f"Missing required transaction column: {col}")

        clean_df = df.copy()

        # Parse timestamp to UTC datetime
        clean_df["timestamp"] = pd.to_datetime(clean_df["timestamp"], utc=True)

        # Cast amounts to positive float
        clean_df["amount"] = pd.to_numeric(clean_df["amount"], errors="coerce").fillna(0.0)
        clean_df["amount"] = clean_df["amount"].clip(lower=0.0)

        # Ensure target column is boolean/int
        if "is_fraud" in clean_df.columns:
            clean_df["is_fraud"] = clean_df["is_fraud"].astype(bool).astype(int)

        # CRITICAL: Sort chronologically to avoid lookahead data leakage in rolling features
        clean_df = clean_df.sort_values(by="timestamp").reset_index(drop=True)

        return clean_df
