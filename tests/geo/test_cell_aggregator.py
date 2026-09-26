"""Unit tests for H3CellAggregator."""

import pandas as pd
import pytest

from geo.aggregation.cell_aggregator import H3CellAggregator
from geo.indexing.h3_indexer import H3Indexer


@pytest.fixture
def aggregator():
    return H3CellAggregator(resolution=7)


def test_aggregate_transactions(aggregator):
    # Two points in Delhi, one in Mumbai
    tx_data = [
        {"transaction_id": "T1", "latitude": 28.6139, "longitude": 77.2090, "amount": 10000.0, "is_fraud": False, "sender_account_number": "A1", "receiver_account_number": "B1"},
        {"transaction_id": "T2", "latitude": 28.6145, "longitude": 77.2095, "amount": 25000.0, "is_fraud": True, "sender_account_number": "A2", "receiver_account_number": "B2"},
        {"transaction_id": "T3", "latitude": 18.9220, "longitude": 72.8347, "amount": 5000.0, "is_fraud": False, "sender_account_number": "A3", "receiver_account_number": "B3"},
    ]
    df = pd.DataFrame(tx_data)

    agg = aggregator.aggregate_transactions(df)
    assert not agg.empty
    assert "h3_cell" in agg.columns
    assert "transaction_count" in agg.columns
    assert "fraud_count" in agg.columns
    assert "fraud_ratio" in agg.columns

    # Delhi transactions share the same H3 res 7 cell
    delhi_cell = H3Indexer.point_to_h3(28.6139, 77.2090, resolution=7)
    delhi_row = agg[agg["h3_cell"] == delhi_cell].iloc[0]
    assert delhi_row["transaction_count"] == 2
    assert delhi_row["fraud_count"] == 1
    assert delhi_row["fraud_ratio"] == 0.50
    assert delhi_row["total_transaction_amount"] == 35000.0


def test_aggregate_complaints(aggregator):
    cmp_data = [
        {"complaint_id": "C1", "latitude": 23.9614, "longitude": 86.8016, "reported_loss_amount": 50000.0, "category": "phishing"},
        {"complaint_id": "C2", "latitude": 23.9620, "longitude": 86.8020, "reported_loss_amount": 35000.0, "category": "phishing"},
    ]
    df = pd.DataFrame(cmp_data)

    agg = aggregator.aggregate_complaints(df)
    assert not agg.empty
    assert "h3_cell" in agg.columns
    assert "complaint_count" in agg.columns
    assert "total_complaint_loss" in agg.columns
    assert agg["complaint_count"].sum() == 2
    assert agg["dominant_scam_type"].iloc[0] == "phishing"


def test_unified_cell_profiles_and_risk_scoring(aggregator):
    cell = H3Indexer.point_to_h3(23.9614, 86.8016, resolution=7)
    tx_df = pd.DataFrame([{
        "h3_cell": cell,
        "transaction_count": 10,
        "fraud_count": 8,
        "fraud_ratio": 0.8,
        "total_transaction_amount": 250000.0,
    }])
    cmp_df = pd.DataFrame([{
        "h3_cell": cell,
        "complaint_count": 5,
        "total_complaint_loss": 150000.0,
        "dominant_scam_type": "phishing",
    }])

    profiles = aggregator.build_unified_cell_profiles(
        tx_agg_df=tx_df,
        cmp_agg_df=cmp_df,
        cell_to_cluster_map={cell: 0},
    )

    assert len(profiles) == 1
    p = profiles[0]
    assert p.h3_cell == cell
    assert p.fraud_count == 8
    assert p.complaint_count == 5
    assert p.risk_score >= 60.0
    assert p.risk_band in ["HIGH", "CRITICAL"]
    assert len(p.nearest_atms) > 0
