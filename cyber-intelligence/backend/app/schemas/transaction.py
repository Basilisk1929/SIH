"""Pydantic schemas for financial transactions and account entities."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TransactionBase(BaseModel):
    txn_ref_no: str = Field(..., example="UPI/428901849182/SYN")
    sender_account: Optional[str] = Field(None, example="SYN1122334455")
    receiver_account: Optional[str] = Field(None, example="SYN9876543210")
    sender_upi: Optional[str] = Field(None, example="victim@synthaxis")
    receiver_upi: Optional[str] = Field(None, example="mule1@synthaxis")
    amount_inr: Decimal = Field(..., gt=0, example=25000.00)
    rail_type: str = Field("UPI", example="UPI")
    timestamp: datetime
    layer_depth: int = Field(1, ge=1, le=10, example=1)


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: UUID
    is_flagged_suspicious: bool
    anomaly_score: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BankAccountSummary(BaseModel):
    account_number: str
    ifsc_code: str
    bank_name: str
    holder_synthetic_name: str
    is_frozen: bool
    risk_score: Decimal
    mule_layer_detected: int
    flagged_reasons: Optional[List[str]] = None
    total_credit_volume_inr: Decimal
    total_debit_volume_inr: Decimal

    model_config = ConfigDict(from_attributes=True)
