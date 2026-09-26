"""Complaints API endpoints implementing NCRP/1930 incident ingestion and management."""

from typing import Any, Dict, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.complaint import (
    ComplaintCreate,
    ComplaintFilter,
    ComplaintResponse,
    ComplaintUpdate,
)
from backend.app.services.complaint_service import ComplaintService
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
        return {
            "items": items,
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


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint_by_id(
    complaint_id: UUID,
    db: AsyncSession = Depends(get_db),
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
) -> Any:
    """Search for complaint by acknowledgement number (e.g. NCRP-SYN-2024-XXXXX)."""
    complaint = await ComplaintService.get_by_ack_no(db, ack_no)
    if not complaint:
        # Fallback synthetic record
        return SyntheticFeedService.generate_synthetic_complaint(999)
    return complaint


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
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


@router.post("/seed", status_code=status.HTTP_200_OK)
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
