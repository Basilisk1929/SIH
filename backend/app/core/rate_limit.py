"""Production-grade sliding-window rate limiting for brute-force and DoS protection."""

import asyncio
from collections import defaultdict
import time
from typing import Callable, Dict, List, Optional
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter tracking client requests per IP or identifier."""

    def __init__(self, default_max_requests: int = 120, default_window_seconds: int = 60):
        self.default_max_requests = default_max_requests
        self.default_window_seconds = default_window_seconds
        # Mapping: key -> list of float timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(
        self,
        key: str,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> tuple[bool, int, int]:
        """Check if request under `key` is allowed.

        Returns: (allowed, remaining_quota, retry_after_seconds)
        """
        limit = max_requests if max_requests is not None else self.default_max_requests
        window = window_seconds if window_seconds is not None else self.default_window_seconds
        now = time.time()
        window_start = now - window

        async with self._lock:
            # Filter timestamps outside window
            valid_timestamps = [t for t in self._history[key] if t > window_start]
            current_count = len(valid_timestamps)

            if current_count >= limit:
                # Oldest timestamp in window determines retry-after
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + window - now))
                self._history[key] = valid_timestamps
                return False, 0, retry_after

            # Quota available: record current timestamp
            valid_timestamps.append(now)
            self._history[key] = valid_timestamps
            remaining = max(0, limit - len(valid_timestamps))
            return True, remaining, 0

    def reset(self) -> None:
        """Clear all rate limit history."""
        self._history.clear()


# Global rate limiter instance
app_rate_limiter = SlidingWindowRateLimiter()


def rate_limit(max_requests: int = 120, window_seconds: int = 60) -> Callable:
    """FastAPI dependency factory enforcing rate limits on endpoint."""

    async def dependency(request: Request) -> None:
        # Extract client IP with forward-header support
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        endpoint_path = request.url.path
        key = f"{client_ip}:{endpoint_path}:{max_requests}"

        allowed, remaining, retry_after = await app_rate_limiter.is_allowed(
            key, max_requests=max_requests, window_seconds=window_seconds
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s. Try again in {retry_after}s.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

    return dependency
