"""Complaint service encapsulating business logic for simulated NCRP/1930 reports."""

from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.complaint import Complaint
from backend.app.schemas.complaint import ComplaintCreate, ComplaintFilter, ComplaintUpdate


class ComplaintService:
    """Operations on cybercrime complaint records."""

    @staticmethod
    async def create_complaint(db: AsyncSession, complaint_in: ComplaintCreate) -> Complaint:
        """Create and persist a new synthetic complaint."""
        ack_no = complaint_in.acknowledgement_no or f"NCRP-SYN-2024-{func.floor(func.random() * 90000 + 10000)}"
        
        # Initial preliminary heuristic risk assessment
        initial_risk = Decimal("0.35")
        if complaint_in.reported_loss_inr > 100000:
            initial_risk += Decimal("0.25")
        if complaint_in.suspect_upi and "mule" in complaint_in.suspect_upi.lower():
            initial_risk += Decimal("0.30")
        initial_risk = min(initial_risk, Decimal("0.99"))

        priority = "LOW"
        if initial_risk >= Decimal("0.70"):
            priority = "HIGH"
        elif initial_risk >= Decimal("0.45"):
            priority = "MEDIUM"

        db_obj = Complaint(
            acknowledgement_no=str(ack_no),
            category=complaint_in.category,
            subcategory=complaint_in.subcategory,
            victim_state=complaint_in.victim_state,
            victim_district=complaint_in.victim_district,
            reported_loss_inr=complaint_in.reported_loss_inr,
            suspect_upi=complaint_in.suspect_upi,
            suspect_account_number=complaint_in.suspect_account_number,
            suspect_ifsc=complaint_in.suspect_ifsc,
            suspect_phone=complaint_in.suspect_phone,
            incident_timestamp=complaint_in.incident_timestamp,
            status="NEW",
            triage_priority=priority,
            risk_score=initial_risk,
            description_synthetic=complaint_in.description_synthetic,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, complaint_id: UUID) -> Optional[Complaint]:
        """Fetch complaint by unique UUID."""
        result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
        return result.scalars().first()

    @staticmethod
    async def get_by_ack_no(db: AsyncSession, ack_no: str) -> Optional[Complaint]:
        """Fetch complaint by acknowledgement number."""
        result = await db.execute(select(Complaint).where(Complaint.acknowledgement_no == ack_no))
        return result.scalars().first()

    @staticmethod
    async def list_complaints(
        db: AsyncSession, filters: ComplaintFilter
    ) -> Tuple[List[Complaint], int]:
        """List complaints with flexible filtering and pagination."""
        query = select(Complaint)

        if filters.category:
            query = query.where(Complaint.category == filters.category)
        if filters.victim_state:
            query = query.where(Complaint.victim_state == filters.victim_state)
        if filters.status:
            query = query.where(Complaint.status == filters.status)
        if filters.min_loss is not None:
            query = query.where(Complaint.reported_loss_inr >= filters.min_loss)
        if filters.max_loss is not None:
            query = query.where(Complaint.reported_loss_inr <= filters.max_loss)

        if filters.search:
            pattern = f"%{filters.search}%"
            query = query.where(
                (Complaint.acknowledgement_no.ilike(pattern))
                | (Complaint.suspect_upi.ilike(pattern))
                | (Complaint.suspect_account_number.ilike(pattern))
                | (Complaint.suspect_phone.ilike(pattern))
            )

        # Count total matches
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        # Fetch page items
        query = query.order_by(desc(Complaint.created_at)).offset(filters.offset).limit(filters.limit)
        items_result = await db.execute(query)
        return list(items_result.scalars().all()), total_count

    @staticmethod
    async def update_status(
        db: AsyncSession, complaint_id: UUID, update_in: ComplaintUpdate
    ) -> Optional[Complaint]:
        """Update workflow status or triage priority."""
        complaint = await ComplaintService.get_by_id(db, complaint_id)
        if not complaint:
            return None

        if update_in.status:
            complaint.status = update_in.status
        if update_in.triage_priority:
            complaint.triage_priority = update_in.triage_priority
        if update_in.risk_score is not None:
            complaint.risk_score = update_in.risk_score

        await db.flush()
        await db.refresh(complaint)
        return complaint
