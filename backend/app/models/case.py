"""Case model grouping multi-account cybercrime incidents and investigations."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.complaint import Complaint
    from backend.app.models.alert import Alert


class Case(Base, TimestampMixin, SoftDeleteMixin):
    """Investigative docket unifying complaints, mule accounts, alerts, and recovery actions."""

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", index=True, nullable=False)
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    total_fraud_amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )
    recovered_amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )

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
