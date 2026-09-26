"""Bank model representing simulated Indian financial institutions."""

import uuid
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.account import Account
    from backend.app.models.atm import ATM


class Bank(Base, TimestampMixin, SoftDeleteMixin):
    """Financial institution entity for routing, nodal liaison, and account origin."""

    __tablename__ = "banks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    bank_code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    bank_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    bank_type: Mapped[str] = mapped_column(String(50), default="Commercial", nullable=False)
    headquarters: Mapped[str | None] = mapped_column(String(150), nullable=True)
    nodal_officer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nodal_officer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nodal_officer_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    # Relationships
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="bank")
    atms: Mapped[List["ATM"]] = relationship("ATM", back_populates="bank")
