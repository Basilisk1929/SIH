"""Pydantic schemas for multi-factor risk scoring and fraud analytics."""

from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RiskFactor(BaseModel):
    name: str = Field(..., example="Rapid Outflow Velocity")
    weight: float = Field(..., example=0.35)
    score: float = Field(..., example=0.90)
    description: str = Field(
        ..., example="95% of credited funds transferred out to downstream accounts within 4 minutes."
    )


class RiskAssessmentRequest(BaseModel):
    account_number: Optional[str] = None
    upi_id: Optional[str] = None
    phone: Optional[str] = None
    transaction_amount_inr: Optional[Decimal] = None
    complaint_ids: Optional[List[str]] = None


class RiskAssessmentResponse(BaseModel):
    entity_id: str
    entity_type: str  # ACCOUNT, UPI, PHONE, TRANSACTION
    overall_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str  # LOW, MEDIUM, HIGH, SEVERE
    is_mule_candidate: bool
    recommended_action: str  # ALLOW, MONITOR, MANUAL_REVIEW, EMERGENCY_FREEZE
    contributing_factors: List[RiskFactor]
    feature_metrics: Dict[str, float] = Field(default_factory=dict)
