"""Graph analysis and mule network visualization endpoints."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from neo4j import AsyncSession
from backend.app.core.security import get_current_user_claims
from backend.app.db.neo4j import get_optional_neo4j_session
from backend.app.schemas.graph import MuleChainResponse, SubgraphResponse
from backend.app.services.graph_service import GraphService
from graph.services.investigation_service import GraphInvestigationService

logger = logging.getLogger("graph.api")
router = APIRouter()


@router.get("/subgraph/{account_number}", response_model=SubgraphResponse)
async def get_account_subgraph(
    account_number: str,
    depth: int = Query(2, ge=1, le=4),
    session: Optional[AsyncSession] = Depends(get_optional_neo4j_session),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> SubgraphResponse:
    """Retrieve multi-hop network subgraph centered on a suspect bank account.
    Uses live Neo4j session when connected, or graceful synthetic topological fallback.
    """
    subgraph = await GraphService.get_account_subgraph(
        session=session, account_number=account_number, depth=depth
    )
    return subgraph


@router.get("/mule-chain/{complaint_ack}", response_model=MuleChainResponse)
async def trace_mule_chain(
    complaint_ack: str,
    session: Optional[AsyncSession] = Depends(get_optional_neo4j_session),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> MuleChainResponse:
    """Trace money flow hops from initial victim debit to downstream cash-out destinations."""
    result = await GraphService.trace_mule_chain(session=session, complaint_ack=complaint_ack)
    return result


@router.get("/connected-accounts/{account_number}")
async def get_connected_accounts(
    account_number: str,
    limit: int = Query(50, ge=1, le=200),
    session: Optional[AsyncSession] = Depends(get_optional_neo4j_session),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    """Find accounts connected directly or via shared infrastructure (Device, Phone, UPI)."""
    if session is not None:
        try:
            svc = GraphInvestigationService(session)
            evidence = await svc.find_connected_accounts(account_number, limit=limit)
            return {
                "account_number": account_number,
                "evidence": [e.model_dump() for e in evidence],
                "source": "neo4j_live",
            }
        except Exception as e:
            logger.warning(f"Neo4j connected accounts query fallback: {e}")

    # Fallback to topology
    return {
        "account_number": account_number,
        "evidence": [
            {
                "target_account": "SYN1000002170",
                "reason": "DIRECT_TRANSFER",
                "weight": 0.85,
                "transaction_count": 3,
                "total_volume": 125000.0,
            }
        ],
        "source": "synthetic_topology",
    }


@router.get("/cashout-paths/{account_number}")
async def get_cashout_paths(
    account_number: str,
    max_hops: int = Query(4, ge=1, le=6),
    session: Optional[AsyncSession] = Depends(get_optional_neo4j_session),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    """Identify rapid cash-out dissipation paths terminating at ATMs or outward payment switches."""
    if session is not None:
        try:
            svc = GraphInvestigationService(session)
            paths = await svc.find_cashout_paths(account_number, max_hops=max_hops)
            return {
                "account_number": account_number,
                "paths": [p.model_dump() for p in paths],
                "source": "neo4j_live",
            }
        except Exception as e:
            logger.warning(f"Neo4j cashout paths query fallback: {e}")

    return {
        "account_number": account_number,
        "paths": [
            {
                "path_nodes": [account_number, "MULE_L2_SYN", "ATM_TERM_019"],
                "total_hops": 2,
                "exit_channel": "ATM_DISPENSE",
                "exit_amount": 45000.0,
            }
        ],
        "source": "synthetic_topology",
    }
