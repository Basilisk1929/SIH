"""In-memory sliding-window rate limiter for API defense against alert flood and DoS."""

import threading
import time
from typing import Dict, List, Optional
from fastapi import HTTPException, Request, status

from backend.app.alerts.constants import (
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
)


class InMemoryRateLimiter:
    """Sliding-window request rate limiter per client IP or identifier."""

    def __init__(
        self,
        max_requests: int = DEFAULT_RATE_LIMIT_REQUESTS,
        window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW,
    ):
        self.max_requests = int(max_requests)
        self.window_seconds = int(window_seconds)
        self._lock = threading.Lock()
        self._history: Dict[str, List[float]] = {}

    def is_allowed(self, client_key: str) -> bool:
        """Check if request from client_key is within allowed rate threshold."""
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._history.get(client_key, [])
            # Filter out expired timestamps
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= self.max_requests:
                self._history[client_key] = valid_timestamps
                return False

            valid_timestamps.append(now)
            self._history[client_key] = valid_timestamps
            return True

    def reset(self) -> None:
        """Reset internal rate limiting records."""
        with self._lock:
            self._history.clear()


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


def verify_rate_limit(
    request: Request,
    max_requests: int = DEFAULT_RATE_LIMIT_REQUESTS,
    window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW,
) -> None:
    """FastAPI dependency to enforce request rate limits per client IP."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{client_ip}:{request.url.path}"

    if not rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {max_requests} requests per {window_seconds}s.",
        )
