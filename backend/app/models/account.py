"""Bank account model representing legitimate customer and mule accounts."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.bank import Bank
    from backend.app.models.transaction import Transaction
    from backend.app.models.alert import Alert


class Account(Base, TimestampMixin, SoftDeleteMixin):
    """Normalized bank account entity tracking risk scores, mule layers, and financial flow."""

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    account_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    bank_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("banks.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    bank_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    branch_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    holder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_linked: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    account_type: Mapped[str] = mapped_column(String(50), default="SAVINGS", nullable=False)
    balance_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )
    total_credit_volume_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )
    total_debit_volume_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), index=True, nullable=False
    )
    mule_layer_detected: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    flagged_reasons: Mapped[List[str] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    bank: Mapped[Optional["Bank"]] = relationship("Bank", back_populates="accounts", lazy="selectin")
    sent_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="[Transaction.sender_account_id]",
        back_populates="sender_account_rel",
    )
    received_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="[Transaction.receiver_account_id]",
        back_populates="receiver_account_rel",
    )
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="account")

    # Compatibility alias for legacy attribute name
    @property
    def holder_synthetic_name(self) -> str:
        return self.holder_name

    @holder_synthetic_name.setter
    def holder_synthetic_name(self, value: str):
        self.holder_name = value


# Legacy alias
BankAccount = Account
