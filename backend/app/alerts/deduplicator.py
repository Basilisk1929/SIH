"""Time-windowed alert deduplication engine to suppress redundant alert storms."""

from dataclasses import dataclass
import hashlib
import threading
import time
from typing import Dict, Optional, Tuple


@dataclass
class DeduplicationRecord:
    alert_id: str
    first_seen: float
    last_seen: float
    count: int


class AlertDeduplicator:
    """Thread-safe time-windowed deduplication manager for financial transaction alerts."""

    def __init__(self, default_window_seconds: int = 300):
        self.default_window_seconds = int(default_window_seconds)
        self._lock = threading.Lock()
        self._cache: Dict[str, DeduplicationRecord] = {}

    @staticmethod
    def compute_fingerprint(account_id: str, transaction_id: str, alert_type: str) -> str:
        """Generate deterministic SHA-256 fingerprint for identity matching."""
        raw = f"{account_id.strip()}:{transaction_id.strip()}:{alert_type.strip()}".lower()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def check_and_register(
        self,
        account_id: str,
        transaction_id: str,
        alert_type: str,
        window_seconds: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], int]:
        """Check if an identical alert was emitted within window_seconds.

        Returns:
            (is_duplicate, original_alert_id, duplicate_count)
        """
        window = int(window_seconds if window_seconds is not None else self.default_window_seconds)
        if window <= 0:
            return False, None, 1

        fingerprint = self.compute_fingerprint(account_id, transaction_id, alert_type)
        now = time.time()

        with self._lock:
            # Check existing entry
            if fingerprint in self._cache:
                rec = self._cache[fingerprint]
                if (now - rec.first_seen) <= window:
                    # Duplicate within window
                    rec.count += 1
                    rec.last_seen = now
                    return True, rec.alert_id, rec.count
                else:
                    # Expired, reset entry
                    del self._cache[fingerprint]

            # Not a duplicate yet; placeholder record until alert_id is registered
            self._cache[fingerprint] = DeduplicationRecord(
                alert_id="",
                first_seen=now,
                last_seen=now,
                count=1,
            )
            return False, None, 1

    def bind_alert_id(
        self,
        account_id: str,
        transaction_id: str,
        alert_type: str,
        alert_id: str,
    ) -> None:
        """Bind the persisted alert_id to the registered fingerprint."""
        fingerprint = self.compute_fingerprint(account_id, transaction_id, alert_type)
        with self._lock:
            if fingerprint in self._cache:
                self._cache[fingerprint].alert_id = alert_id

    def evict_expired(self, max_age_seconds: int = 3600) -> int:
        """Clean up entries older than max_age_seconds."""
        now = time.time()
        evicted = 0
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if (now - v.last_seen) > max_age_seconds
            ]
            for k in expired_keys:
                del self._cache[k]
                evicted += 1
        return evicted

    def clear(self) -> None:
        """Reset internal deduplication cache."""
        with self._lock:
            self._cache.clear()
