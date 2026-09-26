"""Tests for TransactionRiskEngine model and scoring."""

from ml.models.risk_engine import TransactionRiskEngine


def test_risk_engine_score_bounds_and_banding():
    engine = TransactionRiskEngine()

    high_risk_features = {
        "transaction_amount": 95000.0,
        "transactions_last_1h": 8.0,
        "transactions_last_24h": 15.0,
        "cashout_ratio": 0.85,
        "complaint_link_count": 3.0,
    }
    result = engine.predict_risk(high_risk_features)

    assert 0.0 <= result["risk_score"] <= 100.0
    assert result["risk_band"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(result["feature_explanations"]) >= 1
    assert "investigation" in result["disclaimer"].lower()

    low_risk_features = {
        "transaction_amount": 500.0,
        "transactions_last_1h": 0.0,
        "transactions_last_24h": 0.0,
        "cashout_ratio": 0.0,
        "complaint_link_count": 0.0,
    }
    low_result = engine.predict_risk(low_risk_features)
    assert low_result["risk_score"] < result["risk_score"]


def test_risk_bands_mapping():
    engine = TransactionRiskEngine()
    assert engine._determine_risk_band(90.0) == "CRITICAL"
    assert engine._determine_risk_band(70.0) == "HIGH"
    assert engine._determine_risk_band(45.0) == "MEDIUM"
    assert engine._determine_risk_band(15.0) == "LOW"
