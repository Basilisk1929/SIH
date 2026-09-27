"""REST API endpoints for the Phase 11F End-to-End SIH Demo Simulator."""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import Role, get_current_user_claims, require_roles
from backend.app.db.neo4j import get_neo4j_session
from backend.app.db.session import get_db_optional
from backend.app.schemas.demo import DemoResetResponse, DemoSimulateResponse, DemoStatusResponse
from backend.app.services.demo_service import demo_service

logger = logging.getLogger("demo.api")
router = APIRouter(tags=["SIH End-to-End Demo Simulator"])


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post(
    "/simulate-fraud",
    response_model=DemoSimulateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def simulate_fraud_scenario(
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
    neo4j_session: Optional[Any] = Depends(get_neo4j_session),
) -> DemoSimulateResponse:
    """Execute a controlled end-to-end synthetic fraud scenario traversing all platform subsystems:

    Synthetic Transaction -> Ingestion -> PostgreSQL -> XGBoost Risk Engine -> Neo4j Graph ->
    Geospatial H3/Hotspot -> Phase 11C Cash-Out Predictor -> Real-Time Alert Engine -> SSE/WebSocket -> UI.
    Also processes synthetic NCRP Complaint -> spaCy NLP -> Entity Linking.

    Audits: DEMO_SIMULATION_STARTED, DEMO_SIMULATION_COMPLETED.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    actor_id = claims.get("sub", "demo_operator")
    actor_role = claims.get("role", "SUPERVISOR")
    client_ip = _get_client_ip(request)

    try:
        scenario_res = await demo_service.simulate_fraud_scenario(
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
            neo4j_session=neo4j_session,
        )
        return scenario_res
    except Exception as exc:
        logger.error(f"Error executing demo simulation scenario: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo simulation scenario failed. The incident has been logged.",
        )


@router.post(
    "/reset",
    response_model=DemoResetResponse,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR]))],
)
async def reset_demo_data(
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> DemoResetResponse:
    """Safely purge all synthetic demonstration artifacts (alerts, transactions, complaints, graph edges, cases).

    Does NOT remove normal development or production baseline data.
    Audits: DEMO_DATA_RESET.
    Authorized Roles: ADMIN, SUPERVISOR.
    """
    actor_id = claims.get("sub", "admin")
    actor_role = claims.get("role", "ADMIN")
    client_ip = _get_client_ip(request)

    try:
        reset_res = await demo_service.reset_demo_data(
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )
        return reset_res
    except Exception as exc:
        logger.error(f"Error resetting demo data: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo reset failed. The incident has been logged.",
        )


@router.get(
    "/status",
    response_model=DemoStatusResponse,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR, Role.ANALYST]))],
)
async def get_demo_status(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> DemoStatusResponse:
    """Retrieve operational count of synthetic demonstration entities currently loaded."""
    return demo_service.get_demo_status()
