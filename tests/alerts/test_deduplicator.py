"""Unit tests for AlertDeduplicator."""

import time
import pytest
from backend.app.alerts.deduplicator import AlertDeduplicator


def test_deduplicator_initial_event():
    dedup = AlertDeduplicator(default_window_seconds=10)
    is_dup, orig_id, count = dedup.check_and_register("ACC_001", "TXN_001", "RAPID_VELOCITY")
    assert is_dup is False
    assert orig_id is None
    assert count == 1


def test_deduplicator_suppresses_identical_event_within_window():
    dedup = AlertDeduplicator(default_window_seconds=10)
    is_dup1, _, count1 = dedup.check_and_register("ACC_002", "TXN_002", "RAPID_CASHOUT")
    assert is_dup1 is False
    assert count1 == 1

    dedup.bind_alert_id("ACC_002", "TXN_002", "RAPID_CASHOUT", "ALT_EXISTING_01")

    # Second event immediately within window
    is_dup2, orig_id2, count2 = dedup.check_and_register("ACC_002", "TXN_002", "RAPID_CASHOUT")
    assert is_dup2 is True
    assert orig_id2 == "ALT_EXISTING_01"
    assert count2 == 2

    # Third event immediately within window
    is_dup3, orig_id3, count3 = dedup.check_and_register("ACC_002", "TXN_002", "RAPID_CASHOUT")
    assert is_dup3 is True
    assert orig_id3 == "ALT_EXISTING_01"
    assert count3 == 3


def test_deduplicator_allows_different_transactions():
    dedup = AlertDeduplicator(default_window_seconds=10)
    is_dup1, _, _ = dedup.check_and_register("ACC_003", "TXN_A", "HIGH_ML_RISK")
    is_dup2, _, _ = dedup.check_and_register("ACC_003", "TXN_B", "HIGH_ML_RISK")
    assert is_dup1 is False
    assert is_dup2 is False


def test_deduplicator_window_zero_bypasses():
    dedup = AlertDeduplicator(default_window_seconds=10)
    # Passing window_seconds=0 turns off deduplication
    is_dup1, _, _ = dedup.check_and_register("ACC_004", "TXN_004", "HIGH_ML_RISK", window_seconds=0)
    is_dup2, _, _ = dedup.check_and_register("ACC_004", "TXN_004", "HIGH_ML_RISK", window_seconds=0)
    assert is_dup1 is False
    assert is_dup2 is False


def test_deduplicator_window_expiration():
    # Very short 1-second window
    dedup = AlertDeduplicator(default_window_seconds=1)
    is_dup1, _, _ = dedup.check_and_register("ACC_005", "TXN_005", "RAPID_CASHOUT", window_seconds=1)
    dedup.bind_alert_id("ACC_005", "TXN_005", "RAPID_CASHOUT", "ALT_SHORT")
    assert is_dup1 is False

    # Wait 1.1s for expiration
    time.sleep(1.1)

    is_dup2, _, count2 = dedup.check_and_register("ACC_005", "TXN_005", "RAPID_CASHOUT", window_seconds=1)
    assert is_dup2 is False
    assert count2 == 1
