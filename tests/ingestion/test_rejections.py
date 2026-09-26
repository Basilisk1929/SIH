"""Unit tests for Dead-Letter rejection handling and storage."""

import pytest
from ingestion.app.services.json_ingestor import JSONIngestionService
from ingestion.app.services.storage import storage_service


@pytest.mark.asyncio
async def test_invalid_transaction_rejected_and_stored_separately():
    """Verify invalid transaction is rejected and logged into dead-letter storage."""
    storage_service.clear()

    # Negative amount is invalid
    invalid_tx = {
        "transaction_id": "TXN_BAD_01",
        "sender_account_number": "SYN10001",
        "receiver_account_number": "SYN10002",
        "amount": -500.00,
        "payment_channel": "UPI",
    }

    res = await JSONIngestionService.ingest_record("transaction", invalid_tx, source="TEST_REJECTION")
    assert res["status"] == "REJECTED"
    assert "rejection_id" in res
    assert "errors" in res

    # Verify dead-letter storage holds record
    rejections = storage_service.get_recent_rejections(limit=10)
    assert len(rejections) >= 1
    recent = rejections[0]
    assert recent["error_type"] == "SCHEMA_VALIDATION_ERROR"
    assert recent["source"] == "TEST_REJECTION"
    assert recent["raw_payload"]["transaction_id"] == "TXN_BAD_01"


@pytest.mark.asyncio
async def test_malformed_non_dict_payload_rejected():
    """Verify non-dictionary payload is captured as rejection."""
    res = await JSONIngestionService.ingest_record("transaction", "not a dict", source="TEST_MALFORMED")
    assert res["status"] == "REJECTED"
    assert res["reason"] == "Malformed JSON object"
