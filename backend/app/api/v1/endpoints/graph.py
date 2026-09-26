"""Graph analysis and mule network visualization endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from neo4j import AsyncSession
from backend.app.db.neo4j import get_neo4j_session
from backend.app.schemas.graph import MuleChainResponse, SubgraphResponse
from backend.app.services.graph_service import GraphService

router = APIRouter()


@router.get("/subgraph/{account_number}", response_model=SubgraphResponse)
async def get_account_subgraph(
    account_number: str,
    depth: int = Query(2, ge=1, le=4),
) -> SubgraphResponse:
    """Retrieve multi-hop network subgraph centered on a suspect bank account."""
    # GraphService handles fallback automatically if Neo4j is in local prototype mode
    subgraph = await GraphService.get_account_subgraph(
        session=None, account_number=account_number, depth=depth
    )
    return subgraph


@router.get("/mule-chain/{complaint_ack}", response_model=MuleChainResponse)
async def trace_mule_chain(
    complaint_ack: str,
) -> MuleChainResponse:
    """Trace money flow hops from initial victim debit to downstream cash-out destinations."""
    result = await GraphService.trace_mule_chain(session=None, complaint_ack=complaint_ack)
    return result
