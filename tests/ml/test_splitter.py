"""Tests for time-aware chronological dataset splitter."""

import pandas as pd
from ml.pipeline.splitter import TimeAwareSplitter


def test_time_aware_splitter_proportions():
    n = 100
    X = pd.DataFrame({"feat1": range(n)})
    y = pd.Series([i % 2 for i in range(n)])

    splitter = TimeAwareSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
    splits = splitter.split(X, y)

    assert len(splits.X_train) == 70
    assert len(splits.X_val) == 15
    assert len(splits.X_test) == 15

    # Check chronological ordering: max train index < min val index < min test index
    assert splits.X_train["feat1"].max() < splits.X_val["feat1"].min()
    assert splits.X_val["feat1"].max() < splits.X_test["feat1"].min()
