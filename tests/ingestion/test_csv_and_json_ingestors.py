"""Unit tests for CSV and JSON batch ingestion and REST API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from ingestion.app.main import app
from ingestion.app.services.csv_ingestor import CSVIngestionService
from ingestion.app.services.json_ingestor import JSONIngestionService


@pytest.mark.asyncio
async def test_csv_batch_ingestion():
    """Verify parsing and ingestion of CSV content with both valid and invalid rows."""
    csv_sample = """account_number,customer_id,bank_name,ifsc_code,account_type,current_balance
SYN1001,CUST_001,State Bank of Synth,SYNB0001091,SAVINGS,15000.00
SYN1002,CUST_002,State Bank of Synth,INVALID_IFSC,SAVINGS,25000.00
SYN1003,CUST_003,State Bank of Synth,SYNB0001093,SAVINGS,35000.00
"""
    res = await CSVIngestionService.ingest_csv_content("account", csv_sample, source="TEST_CSV_BATCH")
    assert res["total_records"] == 3
    assert res["accepted_count"] == 2
    assert res["rejected_count"] == 1


@pytest.mark.asyncio
async def test_json_batch_ingestion():
    """Verify batch JSON ingestion with duplicate detection."""
    records = [
        {
            "transaction_id": "TXN_BATCH_01",
            "sender_account_number": "SYN10001",
            "receiver_account_number": "SYN10002",
            "amount": 1000.00,
        },
        {
            "transaction_id": "TXN_BATCH_01",  # Duplicate
            "sender_account_number": "SYN10001",
            "receiver_account_number": "SYN10002",
            "amount": 1000.00,
        },
        {
            "transaction_id": "TXN_BATCH_02",
            "sender_account_number": "SYN10003",
            "receiver_account_number": "SYN10004",
            "amount": 2500.00,
        },
    ]
    res = await JSONIngestionService.ingest_batch("transaction", records, source="TEST_JSON_BATCH")
    assert res["total_records"] == 3
    assert res["accepted_count"] == 2
    assert res["duplicate_count"] == 1


@pytest.mark.asyncio
async def test_ingest_api_endpoints():
    """Verify FastAPI ingestion endpoints using AsyncClient."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8001") as client:
        # Health check
        h_res = await client.get("/api/v1/ingest/health")
        assert h_res.status_code == 200
        assert h_res.json()["status"] == "healthy"

        # POST /api/v1/ingest/transactions
        tx_payload = {
            "transaction_id": "TXN_API_99",
            "sender_account_number": "SYN10001",
            "receiver_account_number": "SYN10002",
            "amount": 75000.00,
            "payment_channel": "UPI",
            "source": "API_TEST",
        }
        res = await client.post("/api/v1/ingest/transactions", json=tx_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ACCEPTED"
        assert "event_id" in data

        # Check stats
        s_res = await client.get("/api/v1/ingest/stats")
        assert s_res.status_code == 200
        stats = s_res.json()
        assert stats["total_valid_ingested"] >= 1
