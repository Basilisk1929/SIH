"""Tests verifying sliding-window rate limiting on sensitive endpoints."""

from fastapi.testclient import TestClient
import pytest
from backend.app.core.rate_limit import app_rate_limiter
from backend.app.core.security import Role, create_access_token
from backend.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    app_rate_limiter.reset()
    yield
    app_rate_limiter.reset()


def test_auth_login_brute_force_rate_limiting():
    """Verify that exceeding 5 login attempts within a 60s window triggers HTTP 429."""
    payload = {"email": "attacker@victim.com", "password": "WrongPassword123!"}

    # 1. First 5 requests reach endpoint (returns 401 Unauthorized for invalid credentials)
    for _ in range(5):
        res = client.post("/api/v1/auth/login-json", json=payload)
        assert res.status_code == 401

    # 2. The 6th request must be intercepted by rate limiter -> 429 Too Many Requests
    blocked_res = client.post("/api/v1/auth/login-json", json=payload)
    assert blocked_res.status_code == 429
    assert "Retry-After" in blocked_res.headers
    assert "X-RateLimit-Limit" in blocked_res.headers
    assert blocked_res.headers["X-RateLimit-Remaining"] == "0"
    assert "Rate limit exceeded" in blocked_res.json()["message"]


def test_rate_limiter_reset_clears_throttle():
    """Verify rate limit history can be reset."""
    payload = {"email": "attacker@victim.com", "password": "WrongPassword123!"}

    for _ in range(5):
        client.post("/api/v1/auth/login-json", json=payload)

    blocked = client.post("/api/v1/auth/login-json", json=payload)
    assert blocked.status_code == 429

    # Reset
    app_rate_limiter.reset()

    # Now allowed again
    allowed = client.post("/api/v1/auth/login-json", json=payload)
    assert allowed.status_code == 401  # Passes rate limiter, rejected by auth
