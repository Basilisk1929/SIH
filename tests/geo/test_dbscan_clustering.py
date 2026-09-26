"""Unit tests for DBSCANHotspotDetector."""

import pandas as pd
import pytest

from geo.clustering.dbscan_clustering import DBSCANHotspotDetector


def test_dbscan_clustering_on_dense_clusters():
    # 3 points in Jamtara (dense cluster A)
    # 3 points in Mewat (dense cluster B)
    # 1 noise point
    data = [
        {"id": 1, "latitude": 23.9614, "longitude": 86.8016, "amount": 50000.0, "is_fraud": True, "scam_category": "phishing"},
        {"id": 2, "latitude": 23.9620, "longitude": 86.8020, "amount": 35000.0, "is_fraud": True, "scam_category": "phishing"},
        {"id": 3, "latitude": 23.9610, "longitude": 86.8010, "amount": 42000.0, "is_fraud": True, "scam_category": "phishing"},
        {"id": 4, "latitude": 28.1128, "longitude": 77.0017, "amount": 60000.0, "is_fraud": True, "scam_category": "loan scam"},
        {"id": 5, "latitude": 28.1135, "longitude": 77.0022, "amount": 80000.0, "is_fraud": True, "scam_category": "loan scam"},
        {"id": 6, "latitude": 28.1120, "longitude": 77.0010, "amount": 75000.0, "is_fraud": True, "scam_category": "loan scam"},
        {"id": 7, "latitude": 15.0000, "longitude": 75.0000, "amount": 1000.0, "is_fraud": False, "scam_category": "other"},
    ]
    df = pd.DataFrame(data)

    detector = DBSCANHotspotDetector(eps_km=5.0, min_samples=3)
    result_df = detector.fit_predict(df)

    assert "cluster_id" in result_df.columns
    assert "is_hotspot" in result_df.columns

    # Clusters 0 and 1 should be formed, point 7 should be noise (-1)
    unique_clusters = set(result_df["cluster_id"].unique())
    assert -1 in unique_clusters
    assert len(unique_clusters - {-1}) == 2

    # Noise point
    noise_row = result_df[result_df["id"] == 7].iloc[0]
    assert noise_row["cluster_id"] == -1
    assert noise_row["is_hotspot"] == False

    # Check cluster summaries
    summaries = detector.get_cluster_summaries()
    assert len(summaries) == 2
    for s in summaries:
        assert s["point_count"] == 3
        assert s["fraud_count"] == 3
        assert s["total_amount_inr"] > 100000.0
        assert s["dominant_pattern"] in ["phishing", "loan scam"]


def test_assign_point_to_nearest_cluster():
    data = [
        {"id": 1, "latitude": 23.9614, "longitude": 86.8016, "amount": 10000.0, "is_fraud": True, "scam_category": "UPI fraud"},
        {"id": 2, "latitude": 23.9620, "longitude": 86.8020, "amount": 20000.0, "is_fraud": True, "scam_category": "UPI fraud"},
        {"id": 3, "latitude": 23.9610, "longitude": 86.8010, "amount": 15000.0, "is_fraud": True, "scam_category": "UPI fraud"},
    ]
    df = pd.DataFrame(data)

    detector = DBSCANHotspotDetector(eps_km=5.0, min_samples=2)
    detector.fit_predict(df)

    # Point close to Jamtara cluster
    cluster_id = detector.assign_point_to_nearest_cluster(23.9618, 86.8018)
    assert cluster_id == 0

    # Point far away
    far_cluster = detector.assign_point_to_nearest_cluster(12.0, 77.0)
    assert far_cluster is None
