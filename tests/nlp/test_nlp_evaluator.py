"""Tests for NLP evaluation framework."""

from nlp.evaluation.evaluator import ComplaintGroundTruthEvaluator, NLPEvaluationMetrics


def test_prf1_calculation():
    p, r, f1 = NLPEvaluationMetrics.compute_prf1(tp=80, fp=20, fn=20)
    assert p == 0.8
    assert r == 0.8
    assert f1 == 0.8


def test_prf1_zero_division():
    p, r, f1 = NLPEvaluationMetrics.compute_prf1(tp=0, fp=0, fn=0)
    assert p == 0.0
    assert r == 0.0
    assert f1 == 0.0


def test_evaluator_runs_on_synthetic_dataset_sample():
    evaluator = ComplaintGroundTruthEvaluator()
    metrics = evaluator.evaluate(sample_size=20)

    assert "evaluated_complaints_count" in metrics
    assert metrics["evaluated_complaints_count"] == 20
    assert "macro_averages" in metrics
    assert metrics["macro_averages"]["f1_score"] >= 0.85
    assert "per_entity_metrics" in metrics
    assert "ACCOUNT" in metrics["per_entity_metrics"]
