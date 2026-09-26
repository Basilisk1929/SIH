"""Unit tests for AlertRuleEvaluator across the 6 threat factors and severity tiers."""

import pytest
from backend.app.alerts.constants import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from backend.app.alerts.evaluator import AlertRuleEvaluator
from backend.app.alerts.schemas import TransactionEvent


def test_evaluator_factor_1_ml_risk():
    event_crit = TransactionEvent(
        transaction_id="TXN_ML_01",
        account_id="SYN001",
        amount=10000.0,
        ml_risk_score=92.0,
    )
    eval_crit = AlertRuleEvaluator.evaluate(event_crit)
    assert eval_crit.ml_risk["triggered"] is True
    assert eval_crit.ml_risk["points"] == 30.0
    assert eval_crit.assigned_severity == SEVERITY_CRITICAL

    event_high = TransactionEvent(
        transaction_id="TXN_ML_02",
        account_id="SYN002",
        amount=10000.0,
        ml_risk_score=68.0,
    )
    eval_high = AlertRuleEvaluator.evaluate(event_high)
    assert eval_high.ml_risk["points"] == 20.0

    event_low = TransactionEvent(
        transaction_id="TXN_ML_03",
        account_id="SYN003",
        amount=500.0,
        ml_risk_score=12.0,
    )
    eval_low = AlertRuleEvaluator.evaluate(event_low)
    assert eval_low.ml_risk["points"] == 0.0
    assert eval_low.assigned_severity == SEVERITY_LOW


def test_evaluator_factor_2_velocity():
    event_burst = TransactionEvent(
        transaction_id="TXN_VEL_01",
        account_id="SYN004",
        amount=5000.0,
        transactions_last_1h=9,
        transactions_last_24h=28,
    )
    eval_burst = AlertRuleEvaluator.evaluate(event_burst)
    assert eval_burst.velocity["triggered"] is True
    assert eval_burst.velocity["points"] >= 20.0
    assert any("burst" in exp.lower() for exp in eval_burst.explanations)


def test_evaluator_factor_3_graph():
    event_graph = TransactionEvent(
        transaction_id="TXN_GRP_01",
        account_id="SYN005",
        amount=15000.0,
        graph_degree=30,
        graph_centrality=0.055,
        unique_receivers=14,
    )
    eval_graph = AlertRuleEvaluator.evaluate(event_graph)
    assert eval_graph.graph["triggered"] is True
    assert eval_graph.graph["points"] >= 20.0
    assert any("fan-out" in exp.lower() or "connectivity" in exp.lower() for exp in eval_graph.explanations)


def test_evaluator_factor_4_cashout():
    event_cashout = TransactionEvent(
        transaction_id="TXN_CSH_01",
        account_id="SYN006",
        amount=40000.0,
        cashout_ratio=0.92,
        pattern_type="RAPID_CASHOUT",
        transaction_type="CASH_OUT",
    )
    eval_cashout = AlertRuleEvaluator.evaluate(event_cashout)
    assert eval_cashout.cashout["triggered"] is True
    assert eval_cashout.cashout["points"] >= 25.0
    assert any("cashout" in exp.lower() for exp in eval_cashout.explanations)


def test_evaluator_factor_5_geographic():
    event_geo = TransactionEvent(
        transaction_id="TXN_GEO_01",
        account_id="SYN007",
        amount=12000.0,
        geographic_distance=1450.0,
        is_hotspot_location=True,
        location_name="Jamtara-Karmatanr Hub",
    )
    eval_geo = AlertRuleEvaluator.evaluate(event_geo)
    assert eval_geo.geographic["triggered"] is True
    assert eval_geo.geographic["points"] >= 20.0
    assert any("geographic" in exp.lower() or "hotspot" in exp.lower() for exp in eval_geo.explanations)


def test_evaluator_factor_6_complaint():
    # 2 prior complaints = instant CRITICAL
    event_cmp = TransactionEvent(
        transaction_id="TXN_CMP_01",
        account_id="SYN008",
        amount=25000.0,
        complaint_link_count=2,
        suspect_phone="+919876543210",
    )
    eval_cmp = AlertRuleEvaluator.evaluate(event_cmp)
    assert eval_cmp.complaint["triggered"] is True
    assert eval_cmp.complaint["points"] >= 35.0
    assert eval_cmp.assigned_severity == SEVERITY_CRITICAL


def test_severity_tiers_all_four_levels():
    # LOW
    low_event = TransactionEvent(transaction_id="T_LOW", account_id="S_LOW", amount=500.0)
    assert AlertRuleEvaluator.evaluate(low_event).assigned_severity == SEVERITY_LOW

    # MEDIUM (e.g. elevated velocity + cross-state distance + moderate ML score)
    med_event = TransactionEvent(
        transaction_id="T_MED",
        account_id="S_MED",
        amount=8000.0,
        transactions_last_1h=5,
        transactions_last_24h=15,
        geographic_distance=500.0,
        ml_risk_score=45.0,
    )
    assert AlertRuleEvaluator.evaluate(med_event).assigned_severity == SEVERITY_MEDIUM

    # HIGH (e.g. 1 complaint or high ML score)
    high_event = TransactionEvent(
        transaction_id="T_HIGH",
        account_id="S_HIGH",
        amount=30000.0,
        complaint_link_count=1,
    )
    assert AlertRuleEvaluator.evaluate(high_event).assigned_severity == SEVERITY_HIGH

    # CRITICAL (e.g. 2 complaints + rapid cashout)
    crit_event = TransactionEvent(
        transaction_id="T_CRIT",
        account_id="S_CRIT",
        amount=95000.0,
        complaint_link_count=2,
        cashout_ratio=0.88,
        transactions_last_1h=6,
    )
    assert AlertRuleEvaluator.evaluate(crit_event).assigned_severity == SEVERITY_CRITICAL
