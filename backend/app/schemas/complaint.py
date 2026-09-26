"""Pydantic schemas for simulated NCRP/1930 Cybercrime complaints."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ComplaintBase(BaseModel):
    category: str = Field(..., example="Financial Fraud")
    subcategory: Optional[str] = Field(None, example="UPI Impersonation / QR Code Scam")
    victim_state: str = Field(..., example="Maharashtra")
    victim_district: Optional[str] = Field(None, example="Mumbai Suburban")
    reported_loss_inr: Decimal = Field(..., ge=0, example=45000.00)
    suspect_upi: Optional[str] = Field(None, example="fraud.mule99@synthaxis")
    suspect_account_number: Optional[str] = Field(None, example="SYN9876543210")
    suspect_ifsc: Optional[str] = Field(None, example="SYNB0001001")
    suspect_phone: Optional[str] = Field(None, example="+919876543210")
    incident_timestamp: datetime
    description_synthetic: Optional[str] = Field(
        None, example="Victim was duped via electricity bill payment APK link asking for ₹10 test transfer."
    )


class ComplaintCreate(ComplaintBase):
    acknowledgement_no: Optional[str] = Field(
        None, example="NCRP-SYN-2024-88412"
    )


class ComplaintUpdate(BaseModel):
    status: Optional[str] = Field(None, example="UNDER_INVESTIGATION")
    triage_priority: Optional[str] = Field(None, example="HIGH")
    risk_score: Optional[Decimal] = Field(None, ge=0, le=1)


class ComplaintResponse(ComplaintBase):
    id: UUID
    acknowledgement_no: str
    reported_timestamp: datetime
    status: str
    triage_priority: str
    risk_score: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintFilter(BaseModel):
    category: Optional[str] = None
    victim_state: Optional[str] = None
    min_loss: Optional[Decimal] = None
    max_loss: Optional[Decimal] = None
    status: Optional[str] = None
    search: Optional[str] = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
