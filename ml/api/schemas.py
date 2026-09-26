"""Pydantic schemas for the financial transaction risk engine API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureExplanationItem(BaseModel):
    """Forensic factor contributing to transaction risk signal."""
    feature: str = Field(..., description="Feature column identifier")
    value: float = Field(..., description="Observed feature numeric value")
    contribution: float = Field(..., description="Relative risk contribution weight [-1.0, 1.0]")
    description: str = Field(..., description="Forensic human-readable rationale")


class RiskPredictRequest(BaseModel):
    """Input payload for POST /risk/predict."""
    transaction_id: Optional[str] = Field("TXN_LIVE", description="Unique transaction reference ID")
    sender_account_number: Optional[str] = Field(None, description="Debited sender bank account")
    receiver_account_number: Optional[str] = Field(None, description="Credited beneficiary account")
    amount: Optional[float] = Field(None, description="Transaction amount in INR")
    timestamp: Optional[str] = Field(None, description="ISO-8601 transaction event timestamp")
    features: Optional[Dict[str, float]] = Field(None, description="Precomputed or explicit 12-feature risk vector")


class RiskPredictResponse(BaseModel):
    """Output payload for POST /risk/predict."""
    transaction_id: str = Field(..., description="Unique transaction reference ID")
    sender_account_number: Optional[str] = Field(None, description="Debited sender account")
    receiver_account_number: Optional[str] = Field(None, description="Credited beneficiary account")
    amount: float = Field(..., description="Transaction amount in INR")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Calibrated risk score between 0 and 100")
    risk_band: str = Field(..., description="Categorical risk band: LOW, MEDIUM, HIGH, CRITICAL")
    is_suspicious: bool = Field(..., description="Flag indicating score exceeds investigative threshold")
    feature_explanations: List[FeatureExplanationItem] = Field(
        default_factory=list,
        description="Top driving features explaining the risk score",
    )
    disclaimer: str = Field(
        ...,
        description="Mandatory disclaimer clarifying that risk score represents an investigative signal, not proof of criminal activity",
    )
    evaluated_at: str = Field(..., description="UTC timestamp of evaluation")


class ModelInfoResponse(BaseModel):
    """Metadata regarding current trained risk model."""
    model_type: str
    version: str
    trained_at: Optional[str]
    feature_names: List[str]
    metrics: Optional[Dict[str, Any]]
