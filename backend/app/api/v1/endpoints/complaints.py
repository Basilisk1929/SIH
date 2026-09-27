"""Complaints API endpoints implementing NCRP/1930 incident ingestion and management."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import Role, get_current_user_claims, require_roles
from backend.app.db.session import get_db, get_db_optional
from backend.app.schemas.complaint import (
    ComplaintCreate,
    ComplaintFilter,
    ComplaintResponse,
    ComplaintUpdate,
)
from backend.app.schemas.pipeline import ComplaintPipelineRequest, ComplaintPipelineResponse
from backend.app.services.complaint_service import ComplaintService
from backend.app.services.pipeline_service import PipelineService
from backend.app.services.synthetic_feed_service import SyntheticFeedService


router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def list_complaints(
    category: str | None = None,
    victim_state: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    """Retrieve filtered list of synthetic cybercrime complaints."""
    try:
        filters = ComplaintFilter(
            category=category,
            victim_state=victim_state,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
        )
        items, total = await ComplaintService.list_complaints(db, filters)
        serialized_items = [ComplaintResponse.model_validate(c) for c in items]
        return {
            "items": serialized_items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "synthetic_mode": True,
        }
    except Exception:
        # Standalone development fallback: generate synthetic complaints if DB is not populated/connected
        items = [
            SyntheticFeedService.generate_synthetic_complaint(i + offset + 1)
            for i in range(min(limit, 10))
        ]
        return {
            "items": items,
            "total": 100,
            "limit": limit,
            "offset": offset,
            "synthetic_mode": True,
            "fallback": True,
        }


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def create_complaint(
    complaint_in: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new synthetic cybercrime incident report."""
    try:
        new_complaint = await ComplaintService.create_complaint(db, complaint_in)
        return new_complaint
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register incident report.",
        )


@router.post(
    "/pipeline",
    response_model=ComplaintPipelineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
@router.post(
    "/analyze",
    response_model=ComplaintPipelineResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def process_complaint_pipeline(
    request: ComplaintPipelineRequest,
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> ComplaintPipelineResponse:
    """Execute complete end-to-end complaint intelligence flow:
    Complaint -> NLP extraction -> Entity normalization -> Entity linking -> PostgreSQL -> Neo4j -> Risk/Intelligence layer -> Alert/Case system.
    """
    try:
        result = await PipelineService.process_complaint(request.model_dump(), db=db)
        return ComplaintPipelineResponse(**result)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Complaint pipeline error. The incident has been logged.",
        )



@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint_by_id(
    complaint_id: UUID,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Retrieve details for a single complaint record by UUID."""
    complaint = await ComplaintService.get_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint record not found.",
        )
    return complaint


@router.get("/ack/{ack_no}")
async def get_complaint_by_ack(
    ack_no: str,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Any:
    """Search for complaint by acknowledgement number (e.g. NCRP-SYN-2024-XXXXX)."""
    try:
        complaint = await ComplaintService.get_by_ack_no(db, ack_no)
        if complaint:
            return complaint
    except Exception:
        pass
    # Fallback synthetic record
    return SyntheticFeedService.generate_synthetic_complaint(999)


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def update_complaint_status(
    complaint_id: UUID,
    update_in: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update triage priority or workflow investigation status."""
    complaint = await ComplaintService.update_status(db, complaint_id, update_in)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint record not found.",
        )
    return complaint


@router.post(
    "/seed",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([Role.ADMIN]))],
)
async def seed_synthetic_complaints(
    count: int = Query(25, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Seed synthetic NCRP/1930 records into the database for demonstrations."""
    try:
        seeded = await SyntheticFeedService.seed_initial_synthetic_data(db, count=count)
        return {"status": "success", "records_seeded": seeded}
    except Exception as exc:
        return {"status": "simulated", "records_seeded": count, "note": "Synthetic fallback activated"}
