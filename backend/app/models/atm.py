"""ATM kiosk and cash terminal model for ATM transaction correlation."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.bank import Bank
    from backend.app.models.transaction import Transaction


class ATM(Base, TimestampMixin, SoftDeleteMixin):
    """Physical ATM kiosk terminal for cash-out fraud tracing and geographic mapping."""

    __tablename__ = "atms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    atm_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    bank_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("banks.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    terminal_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    pincode: Mapped[str | None] = mapped_column(String(10), index=True, nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    # Relationships
    bank: Mapped[Optional["Bank"]] = relationship("Bank", back_populates="atms")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="atm")
