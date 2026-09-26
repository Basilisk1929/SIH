"""Tests for model evaluator metrics."""

import numpy as np
from ml.pipeline.evaluator import ModelEvaluator


def test_evaluator_metrics_calculation():
    # 10 binary instances
    y_true = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
    y_prob = np.array([0.9, 0.8, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1, 0.1, 0.2])

    metrics = ModelEvaluator.evaluate_predictions(y_true, y_prob, threshold=0.50)

    assert 0.0 <= metrics.precision <= 1.0
    assert 0.0 <= metrics.recall <= 1.0
    assert 0.0 <= metrics.f1 <= 1.0
    assert metrics.roc_auc >= 0.80
    assert metrics.pr_auc >= 0.70
    assert len(metrics.confusion_matrix) == 2
    assert len(metrics.confusion_matrix[0]) == 2

    # Check serialized dictionary format
    d = metrics.to_dict()
    assert "precision" in d
    assert "recall" in d
    assert "f1" in d
    assert "roc_auc" in d
    assert "pr_auc" in d
    assert "confusion_matrix" in d
