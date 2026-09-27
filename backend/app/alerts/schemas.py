"""Pydantic schemas for Alert Engine API, evaluation payloads, and state management."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from backend.app.alerts.constants import (
    ALERT_DISCLAIMER,
    ALERT_STATES,
    DEFAULT_DEDUP_WINDOW_SECONDS,
    SEVERITY_LEVELS,
)


class TransactionEvent(BaseModel):
    """Transaction payload consumed by the alert engine for risk evaluation."""

    transaction_id: str = Field(..., description="Unique transaction reference", examples=["TXN_00038001"])
    account_id: str = Field(..., description="Originating/suspect account number", examples=["SYN1000004465"])
    receiver_account: Optional[str] = Field(None, description="Beneficiary account number", examples=["SYN1000002170"])
    amount: float = Field(..., gt=0, description="Transaction amount in INR", examples=[49999.0])
    timestamp: Optional[str] = Field(None, description="ISO-8601 UTC timestamp")
    transaction_type: Optional[str] = Field("TRANSFER", description="TRANSFER, CASH_IN, CASH_OUT, PAYMENT")
    payment_channel: Optional[str] = Field("UPI", description="UPI, IMPS, NEFT, RTGS, ATM")

    # The 6 Factor Inputs
    ml_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Model-generated risk score (0-100)")
    transactions_last_1h: Optional[int] = Field(0, ge=0, description="Rolling 1-hour transaction velocity")
    transactions_last_24h: Optional[int] = Field(0, ge=0, description="Rolling 24-hour transaction velocity")
    transaction_frequency: Optional[float] = Field(0.0, ge=0.0, description="Account lifetime transaction count")

    graph_degree: Optional[int] = Field(0, ge=0, description="Degree in active transaction graph")
    graph_centrality: Optional[float] = Field(0.0, ge=0.0, description="Normalized degree centrality")
    unique_receivers: Optional[int] = Field(0, ge=0, description="Distinct receivers in rolling 24h")
    unique_senders: Optional[int] = Field(0, ge=0, description="Distinct senders in rolling 24h")

    cashout_ratio: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Cumulative cash-out volume ratio")
    pattern_type: Optional[str] = Field("NORMAL", description="Detected behavioral pattern")

    geographic_distance: Optional[float] = Field(0.0, ge=0.0, description="Distance in km to counterparty/ATM")
    is_hotspot_location: Optional[bool] = Field(False, description="Flag indicating cybercrime hotspot proximity")
    location_name: Optional[str] = Field(None, description="City, district, or hotspot name")

    complaint_link_count: Optional[int] = Field(0, ge=0, description="Prior complaints naming account as suspect")
    suspect_phone: Optional[str] = Field(None, description="Associated suspect mobile phone")
    suspect_upi: Optional[str] = Field(None, description="Associated suspect UPI handle")


class AlertRuleEvaluation(BaseModel):
    """Detailed breakdown of the 6 evaluation factors."""

    ml_risk: Dict[str, Any]
    velocity: Dict[str, Any]
    graph: Dict[str, Any]
    cashout: Dict[str, Any]
    geographic: Dict[str, Any]
    complaint: Dict[str, Any]
    total_composite_score: float
    assigned_severity: str
    primary_alert_type: str
    explanations: List[str]


class AlertCreateRequest(BaseModel):
    """Payload to trigger alert evaluation for a transaction event."""

    event: TransactionEvent
    dedup_window_seconds: Optional[int] = Field(
        DEFAULT_DEDUP_WINDOW_SECONDS,
        ge=0,
        le=86400,
        description="Deduplication window in seconds (0 to disable)",
    )
    notes: Optional[str] = Field(None, description="Optional triage context or notes")


class AlertStatusUpdateRequest(BaseModel):
    """Payload to transition alert state."""

    status: str = Field(..., description="NEW, ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE")
    investigator_id: Optional[str] = Field(None, description="Badge or user ID of investigating officer")
    resolution_notes: Optional[str] = Field(None, description="Action taken or investigative rationale")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        s = v.strip().upper()
        if s not in ALERT_STATES:
            raise ValueError(f"Invalid alert status: {v}. Must be one of {sorted(ALERT_STATES)}")
        return s


class AlertResponse(BaseModel):
    """Standardized Alert output representation."""

    id: str = Field(..., description="System UUID identifier")
    alert_id: str = Field(..., description="Human-readable business identifier", examples=["ALT_20260926_A1B2C3D4"])
    alert_type: str = Field(..., description="Classification category")
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    status: str = Field(..., description="NEW, ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Calibrated risk index (0-100)")
    triggered_entity_type: str = Field("TRANSACTION", description="TRANSACTION or ACCOUNT")
    triggered_entity_id: str = Field(..., description="Specific ID of flagged entity")
    account_id: str = Field(..., description="Associated bank account number")
    transaction_id: Optional[str] = None
    rule_flags: Dict[str, Any] = Field(default_factory=dict, description="Evaluation breakdown and explanations")
    is_deduplicated: bool = Field(False, description="True if alert is a suppressed duplicate")
    duplicate_count: int = Field(1, description="Number of identical events seen in deduplication window")
    investigator_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    linked_case_id: Optional[str] = None
    created_at: str
    updated_at: str
    disclaimer: str = Field(default=ALERT_DISCLAIMER)


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""

    items: List[AlertResponse]
    total: int
    page: int
    limit: int
    pages: int


class AlertStatsResponse(BaseModel):
    """Aggregated operational metrics for dashboard triage."""

    total_alerts: int
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    deduplicated_suppressions: int
