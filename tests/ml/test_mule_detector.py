"""Tests for ML mule detection model and feature extraction."""

from ml.models.mule_detector import MuleDetectorModel


def test_mule_detector_feature_extraction():
    """Verify feature extractor normalizes transaction metrics accurately."""
    model = MuleDetectorModel()
    metrics = {
        "drain_velocity_mins": 2.0,
        "retention_ratio": 0.02,
        "fan_out_degree": 5.0,
        "complaint_count": 3.0,
    }
    features = model.extract_features(metrics)
    assert len(features) == 4
    assert all(0.0 <= f <= 1.0 for f in features)


def test_mule_detector_high_risk_threshold():
    """Verify account exhibiting rapid drain and zero balance retention triggers mule candidate."""
    model = MuleDetectorModel(risk_threshold=0.75)
    high_risk_metrics = {
        "drain_velocity_mins": 1.0,
        "retention_ratio": 0.01,
        "fan_out_degree": 6.0,
        "complaint_count": 4.0,
    }
    score = model.predict_risk_score(high_risk_metrics)
    assert score >= 0.75
    assert model.is_mule_ring_candidate(high_risk_metrics) is True
