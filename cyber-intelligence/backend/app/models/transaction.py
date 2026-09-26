"""Financial accounts and transaction models for money trail and risk tracing."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class BankAccount(Base):
    """Simulated Indian bank account entity in the suspect/mule graph."""

    __tablename__ = "bank_accounts"

    account_number: Mapped[str] = mapped_column(String(50), primary_key=True)
    ifsc_code: Mapped[str] = mapped_column(String(20), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(150), nullable=False)
    branch_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    holder_synthetic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_linked: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), index=True, nullable=False
    )
    mule_layer_detected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flagged_reasons: Mapped[List[str] | None] = mapped_column(ARRAY(String), nullable=True)
    total_credit_volume_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )
    total_debit_volume_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00"), nullable=False
    )
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    transactions_received: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="receiver"
    )


class Transaction(Base):
    """Financial transaction record across simulated Indian banking rails."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    txn_ref_no: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    sender_account: Mapped[str | None] = mapped_column(String(50), nullable=True)
    receiver_account: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("bank_accounts.account_number"), index=True, nullable=True
    )
    sender_upi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receiver_upi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount_inr: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    rail_type: Mapped[str] = mapped_column(String(20), nullable=False)  # UPI, IMPS, NEFT, RTGS
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    layer_depth: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_flagged_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    receiver: Mapped[BankAccount | None] = relationship(
        "BankAccount", back_populates="transactions_received"
    )
