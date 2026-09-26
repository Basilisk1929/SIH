"""Unit tests for DuplicateDetector service."""

from ingestion.app.services.deduplicator import DuplicateDetector


def test_transaction_duplicate_detection():
    """Verify identical transactions are flagged as duplicates."""
    detector = DuplicateDetector(max_cache_size=100)
    tx = {
        "transaction_id": "TXN_0001",
        "sender_account_number": "SYN10001",
        "receiver_account_number": "SYN10002",
        "amount": 5000.0,
    }

    is_dup1, fp1 = detector.check_and_record("transaction", tx)
    assert is_dup1 is False

    is_dup2, fp2 = detector.check_and_record("transaction", tx)
    assert is_dup2 is True
    assert fp1 == fp2


def test_complaint_duplicate_detection():
    """Verify duplicate NCRP complaints are suppressed."""
    detector = DuplicateDetector(max_cache_size=100)
    comp = {
        "acknowledgement_no": "NCRP-SYN-2024-88412",
        "reported_loss_amount": 75000.0,
    }

    is_dup1, _ = detector.check_and_record("complaint", comp)
    assert is_dup1 is False

    is_dup2, _ = detector.check_and_record("complaint", comp)
    assert is_dup2 is True


def test_lru_cache_eviction():
    """Verify cache respects capacity constraint."""
    detector = DuplicateDetector(max_cache_size=2)
    detector.check_and_record("transaction", {"transaction_id": "TXN_A"})
    detector.check_and_record("transaction", {"transaction_id": "TXN_B"})
    detector.check_and_record("transaction", {"transaction_id": "TXN_C"})

    # TXN_A should have been evicted
    is_dup_a, _ = detector.check_and_record("transaction", {"transaction_id": "TXN_A"})
    assert is_dup_a is False
