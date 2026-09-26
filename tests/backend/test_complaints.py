"""Tests for synthetic complaints listing and triage endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_complaints_returns_items(async_client: AsyncClient):
    """Verify complaint listing endpoint returns paginated results in synthetic mode."""
    response = await async_client.get("/api/v1/complaints?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["synthetic_mode"] is True
    assert len(data["items"]) <= 10


@pytest.mark.asyncio
async def test_get_complaint_by_ack(async_client: AsyncClient):
    """Verify searching complaint by acknowledgement number."""
    response = await async_client.get("/api/v1/complaints/ack/NCRP-SYN-2024-10001")
    assert response.status_code == 200
    data = response.json()
    assert "acknowledgement_no" in data
    assert "reported_loss_inr" in data
