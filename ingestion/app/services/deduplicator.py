"""Duplicate detection and fingerprinting engine for streaming and batch ingestion."""

import hashlib
from collections import OrderedDict
from typing import Any, Dict, Tuple
from ingestion.app.config import settings


class DuplicateDetector:
    """Detects re-submitted transactions, duplicated 1930 reports, and replay events."""

    def __init__(self, max_cache_size: int = settings.DUPLICATE_CACHE_SIZE):
        self.max_cache_size = max_cache_size
        self._seen_fingerprints: OrderedDict[str, str] = OrderedDict()

    def generate_fingerprint(self, entity_type: str, record: Dict[str, Any]) -> str:
        """Compute deterministic SHA-256 fingerprint from immutable business keys."""
        if entity_type == "transaction":
            # Business key: txn_ref or sender:receiver:amount:timestamp:channel
            txn_id = record.get("transaction_id")
            if txn_id and txn_id != "N/A":
                raw_key = f"txn:{txn_id}"
            else:
                sender = record.get("sender_account_number", "")
                receiver = record.get("receiver_account_number", "")
                amt = record.get("amount", "")
                ts = str(record.get("event_timestamp", record.get("timestamp", "")))
                channel = record.get("payment_channel", "")
                raw_key = f"txn:{sender}:{receiver}:{amt}:{ts}:{channel}"

        elif entity_type == "complaint":
            # Business key: NCRP Acknowledgement Number
            ack = record.get("acknowledgement_no", record.get("complaint_id", ""))
            raw_key = f"cmp:{ack}"

        elif entity_type == "account":
            # Business key: Account Number + IFSC
            acc = record.get("account_number", "")
            ifsc = record.get("ifsc_code", "")
            raw_key = f"acc:{acc}:{ifsc}"

        elif entity_type == "atm":
            # Business key: ATM Interaction ID or account:atm:amount:ts
            atm_int_id = record.get("atm_interaction_id")
            if atm_int_id and atm_int_id != "N/A":
                raw_key = f"atm:{atm_int_id}"
            else:
                acc = record.get("account_number", "")
                amt = record.get("amount", "")
                ts = str(record.get("event_timestamp", record.get("timestamp", "")))
                raw_key = f"atm:{acc}:{amt}:{ts}"

        elif entity_type == "bank":
            raw_key = f"bank:{record.get('bank_code', '')}"

        elif entity_type == "alert":
            raw_key = f"alert:{record.get('alert_id', '')}"

        else:
            raw_key = f"{entity_type}:{sorted(record.items())}"

        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def check_and_record(self, entity_type: str, record: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if record is duplicate. If unique, record fingerprint into cache.

        Returns: (is_duplicate: bool, fingerprint: str)
        """
        fingerprint = self.generate_fingerprint(entity_type, record)

        if fingerprint in self._seen_fingerprints:
            # Move to end for LRU refresh
            self._seen_fingerprints.move_to_end(fingerprint)
            return True, fingerprint

        # Store fingerprint
        self._seen_fingerprints[fingerprint] = entity_type

        # Prune LRU cache if exceeds capacity
        if len(self._seen_fingerprints) > self.max_cache_size:
            self._seen_fingerprints.popitem(last=False)

        return False, fingerprint

    def is_duplicate(self, entity_type: str, record_id: str, record: Dict[str, Any]) -> bool:
        """Convenience method checking whether a record is a duplicate."""
        is_dup, _ = self.check_and_record(entity_type, record)
        return is_dup

    def clear(self):
        """Clear cache (primarily for test resets)."""
        self._seen_fingerprints.clear()



# Global singleton instance
duplicate_detector = DuplicateDetector()
