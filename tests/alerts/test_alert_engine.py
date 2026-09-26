"""Unit and integration tests for RealTimeAlertEngine orchestration."""

import pytest
from backend.app.alerts.constants import (
    ALERT_DISCLAIMER,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    STATE_ACKNOWLEDGED,
    STATE_FALSE_POSITIVE,
    STATE_INVESTIGATING,
    STATE_NEW,
    STATE_RESOLVED,
)
from backend.app.alerts.engine import RealTimeAlertEngine
from backend.app.alerts.schemas import TransactionEvent


@pytest.fixture
def engine():
    eng = RealTimeAlertEngine(dedup_window_seconds=300)
    eng.clear()
    return eng


@pytest.mark.asyncio
async def test_engine_process_and_deduplicate(engine):
    event = TransactionEvent(
        transaction_id="TXN_ORCH_01",
        account_id="SYN_ACC_100",
        amount=65000.0,
        ml_risk_score=91.0,
        transactions_last_1h=6,
        cashout_ratio=0.88,
        complaint_link_count=2,
    )

    # 1. First event -> creates alert
    alert1 = await engine.process_transaction_event(event)
    assert alert1.alert_id.startswith("ALT_")
    assert alert1.severity == SEVERITY_CRITICAL
    assert alert1.status == STATE_NEW
    assert alert1.risk_score >= 85.0
    assert alert1.is_deduplicated is False
    assert alert1.duplicate_count == 1
    assert alert1.disclaimer == ALERT_DISCLAIMER

    # 2. Duplicate event within window -> suppresses duplicate
    alert2 = await engine.process_transaction_event(event)
    assert alert2.alert_id == alert1.alert_id
    assert alert2.is_deduplicated is True
    assert alert2.duplicate_count == 2


@pytest.mark.asyncio
async def test_engine_list_and_filter(engine):
    ev1 = TransactionEvent(
        transaction_id="TXN_L1",
        account_id="ACC_A",
        amount=50000.0,
        ml_risk_score=95.0,
        complaint_link_count=2,
    )
    ev2 = TransactionEvent(
        transaction_id="TXN_L2",
        account_id="ACC_B",
        amount=1000.0,
        ml_risk_score=15.0,
    )
    await engine.process_transaction_event(ev1)
    await engine.process_transaction_event(ev2)

    # Filter by severity
    res_crit = engine.list_alerts(severity="CRITICAL")
    assert len(res_crit.items) == 1
    assert res_crit.items[0].severity == SEVERITY_CRITICAL

    # Filter by account_id
    res_acc = engine.list_alerts(account_id="ACC_B")
    assert len(res_acc.items) == 1
    assert res_acc.items[0].account_id == "ACC_B"


@pytest.mark.asyncio
async def test_engine_state_transitions(engine):
    ev = TransactionEvent(
        transaction_id="TXN_STATE_01",
        account_id="ACC_STATE",
        amount=40000.0,
        ml_risk_score=75.0,
    )
    alert = await engine.process_transaction_event(ev)
    assert alert.status == STATE_NEW

    # NEW -> ACKNOWLEDGED
    up1 = await engine.update_alert_status(alert.alert_id, STATE_ACKNOWLEDGED, investigator_id="OFFICER_007")
    assert up1.status == STATE_ACKNOWLEDGED
    assert up1.investigator_id == "OFFICER_007"

    # ACKNOWLEDGED -> INVESTIGATING
    up2 = await engine.update_alert_status(alert.alert_id, STATE_INVESTIGATING, resolution_notes="Case initiated")
    assert up2.status == STATE_INVESTIGATING
    assert up2.resolution_notes == "Case initiated"

    # INVESTIGATING -> RESOLVED
    up3 = await engine.update_alert_status(alert.alert_id, STATE_RESOLVED, resolution_notes="Account frozen under Sec 91")
    assert up3.status == STATE_RESOLVED

    # Illegal transition: RESOLVED -> NEW (not permitted without re-investigation)
    with pytest.raises(ValueError, match="Illegal state transition"):
        await engine.update_alert_status(alert.alert_id, STATE_NEW)


@pytest.mark.asyncio
async def test_engine_stats(engine):
    ev1 = TransactionEvent(transaction_id="T1", account_id="A1", amount=50000.0, ml_risk_score=95.0, complaint_link_count=2)
    ev2 = TransactionEvent(transaction_id="T2", account_id="A2", amount=500.0, ml_risk_score=10.0)
    await engine.process_transaction_event(ev1)
    await engine.process_transaction_event(ev2)
    # Duplicate
    await engine.process_transaction_event(ev1)

    stats = engine.get_stats()
    assert stats.total_alerts == 2
    assert stats.deduplicated_suppressions == 1
    assert stats.by_severity["CRITICAL"] == 1
    assert stats.by_status["NEW"] == 2
