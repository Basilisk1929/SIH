"""Financial transaction model representing fund flows, velocity, and mule chains."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.account import Account
    from backend.app.models.atm import ATM
    from backend.app.models.alert import Alert


class Transaction(Base, TimestampMixin):
    """Financial transaction record across simulated Indian banking rails and ATM switches."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    txn_ref_no: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    sender_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    receiver_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    sender_account_number: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    receiver_account_number: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    sender_upi: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    receiver_upi: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    sender_device_id: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    receiver_device_id: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    atm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("atms.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    amount_inr: Mapped[Decimal] = mapped_column(Numeric(15, 2), index=True, nullable=False)
    rail_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS", index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    layer_depth: Mapped[int] = mapped_column(Integer, default=1, index=True, nullable=False)
    is_flagged_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    anomaly_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), index=True, nullable=False
    )

    # Relationships
    sender_account_rel: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[sender_account_id],
        back_populates="sent_transactions",
    )
    receiver_account_rel: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[receiver_account_id],
        back_populates="received_transactions",
    )
    atm: Mapped[Optional["ATM"]] = relationship("ATM", back_populates="transactions")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="transaction")

    # Backward compatibility properties
    @property
    def sender_account(self) -> str | None:
        return self.sender_account_number

    @sender_account.setter
    def sender_account(self, val: str | None):
        self.sender_account_number = val

    @property
    def receiver_account(self) -> str | None:
        return self.receiver_account_number

    @receiver_account.setter
    def receiver_account(self, val: str | None):
        self.receiver_account_number = val

    @property
    def receiver(self) -> Optional["Account"]:
        return self.receiver_account_rel


# Re-export BankAccount for legacy compatibility
from backend.app.models.account import Account as BankAccount  # noqa: E402
