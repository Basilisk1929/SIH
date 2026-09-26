"""Tests verifying Cypher query structure, parameterization, and explainable evidence parsing."""

from decimal import Decimal
import pytest
from unittest.mock import AsyncMock
from graph.queries.investigation_queries import (
    FIND_CONNECTED_ACCOUNTS,
    FIND_TRANSACTION_CHAINS,
    FIND_HIGH_DEGREE_ACCOUNTS,
    FIND_SUSPICIOUS_CLUSTERS,
    FIND_CASHOUT_PATHS,
    FIND_ACCOUNTS_CONNECTED_TO_COMPLAINTS,
    FIND_SHORTEST_SUSPICIOUS_PATHS,
)
from graph.services.investigation_service import GraphInvestigationService


def test_cypher_queries_use_safe_parameterization():
    """Verify all 7 investigation Cypher queries use parameterized inputs to prevent injection."""
    queries = [
        FIND_CONNECTED_ACCOUNTS,
        FIND_TRANSACTION_CHAINS,
        FIND_HIGH_DEGREE_ACCOUNTS,
        FIND_SUSPICIOUS_CLUSTERS,
        FIND_CASHOUT_PATHS,
        FIND_ACCOUNTS_CONNECTED_TO_COMPLAINTS,
        FIND_SHORTEST_SUSPICIOUS_PATHS,
    ]
    for q in queries:
        assert "$" in q, "Query must use Cypher parameter placeholders"
        assert "WHERE" in q or "WITH" in q or "MATCH" in q


@pytest.mark.asyncio
async def test_find_connected_accounts_service_evidence():
    """Verify GraphInvestigationService parses connected accounts and produces explainable evidence."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[
        {
            "source_account": "SYN1000000001",
            "connected_account": "SYN1000000035",
            "connection_type": "SHARED_DEVICE",
            "hop_distance": 2,
            "shared_entity_id": "DEV_00018",
            "total_amount_inr": 0.0,
            "transaction_count": 0,
            "is_mule": True,
            "mule_tier": 1,
            "explanation": "Shared hardware device DEV_00018 utilized concurrently",
        }
    ])
    mock_session.run = AsyncMock(return_value=mock_result)

    service = GraphInvestigationService(mock_session)
    evidence = await service.find_connected_accounts("SYN1000000001")

    assert len(evidence) == 1
    assert evidence[0].connected_account == "SYN1000000035"
    assert evidence[0].connection_type == "SHARED_DEVICE"
    assert evidence[0].is_mule is True
    assert evidence[0].shared_entity_id == "DEV_00018"
    assert "Shared hardware device" in evidence[0].explanation


@pytest.mark.asyncio
async def test_find_transaction_chains_service_evidence():
    """Verify transaction chains parsing and velocity categorization."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[
        {
            "origin_account": "SYN1000000001",
            "destination_account": "SYN1000000049",
            "path_nodes": ["SYN1000000001", "SYN1000000035", "SYN1000000049"],
            "hop_count": 2,
            "total_flow_amount_inr": 95000.0,
            "min_hop_amount_inr": 48000.0,
            "start_timestamp": "2024-09-20T10:00:00Z",
            "end_timestamp": "2024-09-20T10:15:00Z",
            "chain_duration_seconds": 900.0,
            "velocity_classification": "RAPID_PASSTHROUGH",
            "explanation": "Multi-hop money trail: Funds originating from SYN1000000001 layered across 2 accounts",
        }
    ])
    mock_session.run = AsyncMock(return_value=mock_result)

    service = GraphInvestigationService(mock_session)
    chains = await service.find_transaction_chains("SYN1000000001")

    assert len(chains) == 1
    assert chains[0].hop_count == 2
    assert chains[0].velocity_classification == "RAPID_PASSTHROUGH"
    assert chains[0].total_flow_amount_inr == Decimal("95000.0")


@pytest.mark.asyncio
async def test_find_high_degree_accounts_service_evidence():
    """Verify high degree funnel and hub accounts parsing."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[
        {
            "account_number": "SYN1000000036",
            "bank_name": "State Bank of Synth",
            "in_degree": 12,
            "out_degree": 1,
            "total_degree": 13,
            "unique_senders": 12,
            "unique_receivers": 1,
            "hub_typology": "FUNNEL_COLLECTOR",
            "total_credit_volume": 450000.0,
            "total_debit_volume": 445000.0,
            "is_mule": True,
            "explanation": "Funnel mule collector: Received deposits from 12 distinct senders",
        }
    ])
    mock_session.run = AsyncMock(return_value=mock_result)

    service = GraphInvestigationService(mock_session)
    hubs = await service.find_high_degree_accounts(min_degree=5)

    assert len(hubs) == 1
    assert hubs[0].account_number == "SYN1000000036"
    assert hubs[0].hub_typology == "FUNNEL_COLLECTOR"
    assert hubs[0].in_degree == 12


@pytest.mark.asyncio
async def test_find_cash_out_paths_service_evidence():
    """Verify cash-out trail evidence parsing ending at physical ATM terminal."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[
        {
            "origin_account": "SYN1000000005",
            "cashout_account": "SYN1000000048",
            "atm_id": "ATM_SYNB_0001",
            "atm_location": "Main e-Lobby, Mumbai, Maharashtra",
            "withdrawn_amount_inr": 40000.0,
            "withdrawal_timestamp": "2024-09-20T14:30:00Z",
            "intermediary_mules": ["SYN1000000035"],
            "rapid_cashout": True,
            "explanation": "Fund Liquidation Trail: Origin account SYN1000000005 funds withdrawn as cash at ATM_SYNB_0001",
        }
    ])
    mock_session.run = AsyncMock(return_value=mock_result)

    service = GraphInvestigationService(mock_session)
    cashouts = await service.find_cash_out_paths("SYN1000000005")

    assert len(cashouts) == 1
    assert cashouts[0].atm_id == "ATM_SYNB_0001"
    assert cashouts[0].withdrawn_amount_inr == Decimal("40000.0")
    assert cashouts[0].rapid_cashout is True


@pytest.mark.asyncio
async def test_find_accounts_connected_to_complaints_service_evidence():
    """Verify complaint linkage evidence to suspect accounts across layers."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[
        {
            "acknowledgement_no": "NCRP-SYN-2024-100001",
            "category": "digital arrest scam",
            "reported_loss_inr": 480000.0,
            "connected_account": "SYN1000000038",
            "connection_depth": 1,
            "connection_route": "LAYER_1_RECIPIENT",
            "complaint_reported_date": "2024-09-18",
            "suspect_upi": "suspect.mule99@synaxis",
            "suspect_phone": "+919876543210",
            "explanation": "NCRP Complaint Link: Citizen reported 480000 loss",
        }
    ])
    mock_session.run = AsyncMock(return_value=mock_result)

    service = GraphInvestigationService(mock_session)
    complaint_evidence = await service.find_accounts_connected_to_complaints(category="digital arrest scam")

    assert len(complaint_evidence) == 1
    assert complaint_evidence[0].acknowledgement_no == "NCRP-SYN-2024-100001"
    assert complaint_evidence[0].connection_depth == 1
    assert complaint_evidence[0].category == "digital arrest scam"
