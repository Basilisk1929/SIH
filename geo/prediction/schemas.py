"""Pydantic request and response schemas for Cash-Out Location Prediction."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from geo.prediction.constants import (
    CASHOUT_DATA_LIMITATION_DISCLAIMER,
    DEFAULT_CANDIDATE_RADIUS_KM,
    DEFAULT_PREDICTION_TOP_K,
    MAX_CANDIDATE_RADIUS_KM,
    MAX_PREDICTION_TOP_K,
    MIN_CANDIDATE_RADIUS_KM,
)


class TransactionContext(BaseModel):
    """Transaction item in account history with optional georeferenced metadata."""

    transaction_id: Optional[str] = Field(None, description="Transaction identifier or reference number")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Transaction origin latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Transaction origin longitude")
    amount: Optional[float] = Field(None, ge=0.0, description="Transaction amount in INR")
    timestamp: Optional[str] = Field(None, description="ISO-8601 transaction timestamp")
    transaction_type: Optional[str] = Field(None, description="TRANSFER, CASH_OUT, PAYMENT, etc.")
    is_cashout: Optional[bool] = Field(False, description="True if transaction represents cash withdrawal")


class CashoutPredictionRequest(BaseModel):
    """Request payload to predict and rank likely cash-out ATM locations."""

    account_id: str = Field(..., description="Target bank account or mule account number")
    recent_transactions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of recent account transactions (with optional coordinates/types)",
    )
    current_latitude: Optional[float] = Field(
        None, ge=-90.0, le=90.0, description="Current or latest known latitude of account operator"
    )
    current_longitude: Optional[float] = Field(
        None, ge=-180.0, le=180.0, description="Current or latest known longitude of account operator"
    )
    candidate_radius_km: Optional[float] = Field(
        DEFAULT_CANDIDATE_RADIUS_KM,
        ge=MIN_CANDIDATE_RADIUS_KM,
        le=MAX_CANDIDATE_RADIUS_KM,
        description="Search radius in kilometers around anchor point to query candidate ATMs",
    )
    top_k: Optional[int] = Field(
        DEFAULT_PREDICTION_TOP_K,
        ge=1,
        le=MAX_PREDICTION_TOP_K,
        description="Number of highest-ranked ATMs to return",
    )
    account_risk_score: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Current ML or composite risk score of the account"
    )
    cashout_ratio: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Ratio of withdrawn to deposited funds"
    )
    transactions_last_1h: Optional[int] = Field(
        None, ge=0, description="Count of transactions executed in last 60 minutes"
    )


class PredictedATM(BaseModel):
    """Ranked RBI ATM outlet with predictive cash-out likelihood and explanations."""

    atm_id: str = Field(..., description="Unique ATM or banking outlet identifier")
    bank_name: str = Field(..., description="Operating bank or WLA entity name")
    latitude: float = Field(..., description="Latitude coordinate of the ATM")
    longitude: float = Field(..., description="Longitude coordinate of the ATM")
    distance_km: float = Field(..., description="Haversine distance from recent account activity in km")
    prediction_score: float = Field(..., ge=0.0, le=100.0, description="Calibrated predictive cash-out score (0-100)")
    rank: int = Field(..., ge=1, description="Relative priority rank (1 = most likely)")
    explanations: List[str] = Field(default_factory=list, description="List of reasons for this ranking")

    # Informational enrichment attributes
    outlet_type: Optional[str] = Field(None, description="ON_SITE_ATM, OFF_SITE_ATM, CASH_RECYCLER, WHITE_LABEL_ATM")
    bank_category: Optional[str] = None
    h3_cell: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None


class CashoutPredictionResponse(BaseModel):
    """Standardized response containing ranked ATM destinations and evidentiary explanations."""

    account_id: str = Field(..., description="Investigated account number")
    prediction_timestamp: str = Field(..., description="ISO-8601 prediction timestamp")
    anchor_location: Dict[str, Any] = Field(..., description="Latitude, longitude, and origin source of anchor point")
    candidate_radius_km: float = Field(..., description="Radius searched for candidate ATMs")
    total_candidates_evaluated: int = Field(..., description="Count of operational ATMs evaluated within radius")
    predicted_atms: List[PredictedATM] = Field(default_factory=list, description="Ranked predicted ATM locations")
    urgency_level: str = Field("STANDARD", description="CRITICAL, HIGH, ELEVATED, STANDARD")
    disclaimer: str = Field(default=CASHOUT_DATA_LIMITATION_DISCLAIMER, description="Mandatory statutory notice")
