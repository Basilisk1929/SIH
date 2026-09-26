"""Unit tests for InMemoryRateLimiter."""

import time
import pytest
from backend.app.alerts.rate_limiter import InMemoryRateLimiter


def test_rate_limiter_allows_under_threshold():
    limiter = InMemoryRateLimiter(max_requests=5, window_seconds=10)
    for _ in range(5):
        assert limiter.is_allowed("client_A") is True


def test_rate_limiter_blocks_above_threshold():
    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=10)
    assert limiter.is_allowed("client_B") is True
    assert limiter.is_allowed("client_B") is True
    assert limiter.is_allowed("client_B") is True

    # 4th request within window must be blocked
    assert limiter.is_allowed("client_B") is False


def test_rate_limiter_different_clients_isolated():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10)
    assert limiter.is_allowed("client_1") is True
    assert limiter.is_allowed("client_1") is True
    assert limiter.is_allowed("client_1") is False

    # client_2 has independent quota
    assert limiter.is_allowed("client_2") is True
    assert limiter.is_allowed("client_2") is True
