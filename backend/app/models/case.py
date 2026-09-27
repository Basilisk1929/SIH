"""Case model grouping multi-account cybercrime incidents and investigations, notes, evidence, and timeline."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.complaint import Complaint
    from backend.app.models.alert import Alert


class Case(Base, TimestampMixin, SoftDeleteMixin):
    """Investigative docket unifying complaints, mule accounts, alerts, evidence, and recovery actions."""

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    alert_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True, nullable=False)

    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    assigned_investigator: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    created_by_username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    total_fraud_amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )
    recovered_amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )

    # Resolution & Closure
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolution_status: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    resolution_category: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
        back_populates="assigned_cases",
        lazy="selectin",
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="created_cases",
        lazy="selectin",
    )
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="case")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="case")

    notes: Mapped[List["CaseNote"]] = relationship(
        "CaseNote",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseNote.created_at",
        lazy="selectin",
    )
    evidence: Mapped[List["CaseEvidence"]] = relationship(
        "CaseEvidence",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseEvidence.created_at",
        lazy="selectin",
    )
    timeline: Mapped[List["CaseTimelineEvent"]] = relationship(
        "CaseTimelineEvent",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseTimelineEvent.timestamp",
        lazy="selectin",
    )


class CaseNote(Base, TimestampMixin):
    """Append-only investigative entry or judicial directive for a case docket."""

    __tablename__ = "case_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    author_id: Mapped[str] = mapped_column(String(255), nullable=False)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    case: Mapped["Case"] = relationship("Case", back_populates="notes")


class CaseEvidence(Base, TimestampMixin):
    """Structured reference linking platform intelligence (transaction, account, alert, ATM, etc.) to a case."""

    __tablename__ = "case_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    evidence_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    evidence_reference_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    added_by: Mapped[str] = mapped_column(String(255), nullable=False)

    case: Mapped["Case"] = relationship("Case", back_populates="evidence")


class CaseTimelineEvent(Base):
    """Chronological, immutable record of investigative lifecycle events."""

    __tablename__ = "case_timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(50), default="INVESTIGATOR", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    details: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )

    case: Mapped["Case"] = relationship("Case", back_populates="timeline")

