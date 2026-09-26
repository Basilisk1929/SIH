"""Time-aware train/validation/test dataset splitter preventing lookahead data leakage."""

import logging
from typing import NamedTuple, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DatasetSplits(NamedTuple):
    X_train: pd.DataFrame
    y_train: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series


class TimeAwareSplitter:
    """Splits chronological transactions into Train, Validation, and Test sets."""

    def __init__(self, train_ratio: float = 0.70, val_ratio: float = 0.15, test_ratio: float = 0.15):
        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

    def split(self, X: pd.DataFrame, y: pd.Series) -> DatasetSplits:
        """Perform chronological time-aware split."""
        n = len(X)
        if n < 10:
            raise ValueError(f"Dataset too small to split ({n} rows)")

        train_end = int(n * self.train_ratio)
        val_end = int(n * (self.train_ratio + self.val_ratio))

        X_train, y_train = X.iloc[:train_end].copy(), y.iloc[:train_end].copy()
        X_val, y_val = X.iloc[train_end:val_end].copy(), y.iloc[train_end:val_end].copy()
        X_test, y_test = X.iloc[val_end:].copy(), y.iloc[val_end:].copy()

        logger.info(
            f"Time-aware split complete: Train={len(X_train)} ({y_train.mean():.1%} fraud), "
            f"Val={len(X_val)} ({y_val.mean():.1%} fraud), Test={len(X_test)} ({y_test.mean():.1%} fraud)"
        )

        return DatasetSplits(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
        )
