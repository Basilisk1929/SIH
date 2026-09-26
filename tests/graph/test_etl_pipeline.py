"""Tests for the Neo4j ETL ingestion pipeline."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
from graph.etl.loader import GraphETLPipeline


def test_etl_dataset_extraction():
    """Verify that extract_dataset loads synthetic CSVs and computes derived Bank & ATM batches."""
    pipeline = GraphETLPipeline()
    datasets = pipeline.extract_dataset()

    expected_keys = [
        "locations",
        "customers",
        "accounts",
        "devices",
        "phones",
        "upis",
        "atms",
        "transactions",
        "complaints",
        "banks",
        "distinct_atms",
    ]
    for k in expected_keys:
        assert k in datasets, f"Missing key {k} in extracted datasets"
        assert isinstance(datasets[k], list)

    # Check non-empty datasets
    assert len(datasets["locations"]) > 0
    assert len(datasets["customers"]) > 0
    assert len(datasets["accounts"]) > 0
    assert len(datasets["banks"]) > 0
    assert len(datasets["transactions"]) > 0
    assert len(datasets["complaints"]) > 0


def test_etl_batch_chunking():
    """Verify chunking splits large record arrays into requested batch sizes."""
    pipeline = GraphETLPipeline(batch_size=25)
    sample_data = [{"id": i} for i in range(70)]

    chunks = pipeline._chunk_list(sample_data, 25)
    assert len(chunks) == 3
    assert len(chunks[0]) == 25
    assert len(chunks[1]) == 25
    assert len(chunks[2]) == 20


@pytest.mark.asyncio
async def test_etl_pipeline_execution_with_mock_driver():
    """Verify that run_pipeline executes the full sequential loading stages."""
    mock_session = AsyncMock()
    mock_session.run = AsyncMock()

    mock_driver = MagicMock()
    mock_driver.session = MagicMock()
    mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=None)

    pipeline = GraphETLPipeline(driver=mock_driver, batch_size=500)
    metrics = await pipeline.run_pipeline()

    # Verify metrics returned for all loading stages
    for stage in [
        "locations",
        "banks",
        "customers",
        "accounts",
        "devices",
        "phones",
        "upis",
        "atms",
        "transactions",
        "atm_withdrawals",
        "complaints",
    ]:
        assert stage in metrics, f"Stage {stage} missing from ETL pipeline metrics"
        assert metrics[stage] >= 0

    assert mock_session.run.call_count > 0
