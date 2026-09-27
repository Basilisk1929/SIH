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
async def test_root_health_check_returns_healthy(async_client: AsyncClient):
    """Verify root /health liveness probe returns HTTP 200."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "CyberShield-Intel"


@pytest.mark.asyncio
async def test_readiness_probe(async_client: AsyncClient):
    """Verify /health/ready and /api/v1/health/ready return readiness payload."""
    res_root = await async_client.get("/health/ready")
    assert res_root.status_code in (200, 503)
    data_root = res_root.json()
    assert "status" in data_root
    assert "services" in data_root

    res_v1 = await async_client.get("/api/v1/health/ready")
    assert res_v1.status_code in (200, 503)
    data_v1 = res_v1.json()
    assert "status" in data_v1
    assert "services" in data_v1


@pytest.mark.asyncio
async def test_root_endpoint_metadata(async_client: AsyncClient):
    """Verify root endpoint returns operational metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert data["compliance"] == "SYNTHETIC_DATA_ENVIRONMENT_ONLY"
