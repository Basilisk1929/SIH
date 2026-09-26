"""Tests for transaction feature engineering and Haversine distance."""

from datetime import datetime, timezone
import pandas as pd
from ml.pipeline.feature_engineering import (
    FEATURE_COLUMNS,
    TransactionFeatureEngineer,
    haversine_distance_km,
)


def test_haversine_distance():
    # Mumbai (18.9220, 72.8347) to Delhi (28.6139, 77.2090) ~ 1150-1200 km
    dist = haversine_distance_km(18.9220, 72.8347, 28.6139, 77.2090)
    assert 1100.0 < dist < 1250.0

    # Same coordinates should be 0.0
    assert haversine_distance_km(18.9220, 72.8347, 18.9220, 72.8347) == 0.0


def test_feature_engineering_extracts_all_twelve_features():
    tx_data = pd.DataFrame(
        [
            {
                "transaction_id": "TXN_001",
                "sender_account_number": "ACC_S1",
                "receiver_account_number": "ACC_R1",
                "amount": 25000.0,
                "timestamp": "2024-08-15T10:00:00Z",
                "sender_location_id": "LOC_01",
                "receiver_location_id": "LOC_02",
            },
            {
                "transaction_id": "TXN_002",
                "sender_account_number": "ACC_S1",
                "receiver_account_number": "ACC_R2",
                "amount": 35000.0,
                "timestamp": "2024-08-15T10:15:00Z",
                "sender_location_id": "LOC_01",
                "receiver_location_id": "LOC_02",
            },
            {
                "transaction_id": "TXN_003",
                "sender_account_number": "ACC_S1",
                "receiver_account_number": "ACC_R3",
                "amount": 45000.0,
                "timestamp": "2024-08-15T10:30:00Z",
                "sender_location_id": "LOC_01",
                "receiver_location_id": "LOC_02",
            },
        ]
    )

    accounts_df = pd.DataFrame(
        [
            {"account_number": "ACC_S1", "opening_date": "2023-01-01", "location_id": "LOC_01"},
            {"account_number": "ACC_R1", "opening_date": "2023-01-01", "location_id": "LOC_02"},
        ]
    )

    engineer = TransactionFeatureEngineer(accounts_df=accounts_df)
    features_df = engineer.compute_features(tx_data)

    assert len(features_df) == 3
    for col in FEATURE_COLUMNS:
        assert col in features_df.columns, f"Missing feature {col}"

    # Verify burst velocity increases strictly in rolling 1h window
    assert features_df.iloc[0]["transactions_last_1h"] == 0.0
    assert features_df.iloc[1]["transactions_last_1h"] == 1.0
    assert features_df.iloc[2]["transactions_last_1h"] == 2.0

    # Verify unique receivers increases
    assert features_df.iloc[0]["unique_receivers"] == 0.0
    assert features_df.iloc[1]["unique_receivers"] == 1.0
    assert features_df.iloc[2]["unique_receivers"] == 2.0
