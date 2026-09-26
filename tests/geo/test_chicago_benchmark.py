"""Unit tests for Chicago crime methodology validation benchmark."""

from geo.datasets.validation.chicago_benchmark import ChicagoCrimeValidationBenchmark


def test_chicago_benchmark_isolation():
    # Must be explicitly tagged as a methodology benchmark and NOT Indian cybercrime
    df = ChicagoCrimeValidationBenchmark.get_benchmark_dataframe()
    assert not df.empty
    assert (df["is_methodology_validation"] == True).all()
    assert (df["jurisdiction"] == "City of Chicago, Illinois, USA").all()
    assert ChicagoCrimeValidationBenchmark.IS_INDIAN_CYBERCRIME is False


def test_chicago_methodology_pipeline():
    result = ChicagoCrimeValidationBenchmark.validate_methodology_pipeline(
        eps_km=1.0,
        min_samples=3,
        h3_resolution=8,
    )
    assert result["status"] == "VALIDATED"
    assert result["detected_clusters_count"] >= 1
    assert result["sample_points_count"] == 11
    assert result["is_indian_cybercrime"] is False
