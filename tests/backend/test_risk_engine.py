"""Tests for multi-factor risk assessment and mule scoring engine."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_assess_risk_endpoint_high_risk(async_client: AsyncClient):
    """Verify high risk calculation for mule account with multiple linked complaints."""
    payload = {
        "account_number": "MULE_ACC_99812",
        "upi_id": "fastmule@synthaxis",
        "transaction_amount_inr": 150000.0,
        "complaint_ids": ["c1", "c2", "c3", "c4"],
    }
    response = await async_client.post("/api/v1/transactions/assess-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk_score"] >= 0.70
    assert data["risk_level"] in ("HIGH", "SEVERE")
    assert data["is_mule_candidate"] is True
    assert data["recommended_action"] in ("MANUAL_REVIEW", "EMERGENCY_FREEZE")
    assert len(data["contributing_factors"]) >= 3
