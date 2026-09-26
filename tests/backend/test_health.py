"""Tests for system health and diagnostics endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_healthy(async_client: AsyncClient):
    """Verify basic liveness probe returns HTTP 200 and synthetic mode flag."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["mode"] == "SYNTHETIC_DEVELOPMENT"


@pytest.mark.asyncio
async def test_root_endpoint_metadata(async_client: AsyncClient):
    """Verify root endpoint returns operational metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert data["compliance"] == "SYNTHETIC_DATA_ENVIRONMENT_ONLY"
