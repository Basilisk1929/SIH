"""Cybercrime complaint model reflecting NCRP / 1930 simulated complaint structures."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class Complaint(Base):
    """Simulated NCRP / 1930 Cybercrime complaint record.

    NOTE: All records are strictly synthetic to protect privacy and adhere to SIH rules.
    """

    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    acknowledgement_no: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(150), nullable=True)
    victim_state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    victim_district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reported_loss_inr: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    suspect_upi: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    suspect_account_number: Mapped[str | None] = mapped_column(
        String(50), index=True, nullable=True
    )
    suspect_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    suspect_phone: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    incident_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    reported_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="NEW",
        index=True,
        nullable=False,
    )
    triage_priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        index=True,
        nullable=False,
    )
    description_synthetic: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
