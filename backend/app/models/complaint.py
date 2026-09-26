"""Cybercrime complaint model reflecting NCRP / 1930 simulated complaint structures."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.case import Case
    from backend.app.models.account import Account


class Complaint(Base, TimestampMixin, SoftDeleteMixin):
    """Simulated NCRP / 1930 Cybercrime incident report with suspect trail and case linkage."""

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
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(150), nullable=True)
    victim_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    victim_phone: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    victim_state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    victim_district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reported_loss_inr: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        index=True,
        nullable=False,
    )
    suspect_upi: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    suspect_account_number: Mapped[str | None] = mapped_column(
        String(50), index=True, nullable=True
    )
    suspect_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    suspect_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    suspect_phone: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    incident_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    reported_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="NEW",
        index=True,
        nullable=False,
    )
    triage_priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", index=True, nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        index=True,
        nullable=False,
    )
    description_synthetic: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    case: Mapped[Optional["Case"]] = relationship("Case", back_populates="complaints", lazy="selectin")
    suspect_account: Mapped[Optional["Account"]] = relationship("Account", lazy="selectin")
