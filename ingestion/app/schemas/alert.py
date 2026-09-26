"""Fraud detection Alert schema with envelope metadata."""

from typing import Literal
from pydantic import Field, field_validator
from ingestion.app.schemas.envelope import IngestionEnvelope


class AlertEvent(IngestionEnvelope):
    """Normalized cyber fraud risk detection or anomaly alert event."""

    alert_id: str = Field(..., description="Unique alert identifier", examples=["ALT_0000001"])
    alert_type: Literal[
        "RAPID_VELOCITY",
        "MULE_CHAIN",
        "FAN_IN",
        "FAN_OUT",
        "RAPID_CASHOUT",
        "HIGH_LOSS",
        "REPEATED_BURST",
        "GEO_ANOMALY",
    ] = Field(..., description="Fraud heuristic or ML pattern triggering the alert")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        default="HIGH", description="Priority escalation tier"
    )
    triggered_entity_type: Literal["ACCOUNT", "TRANSACTION", "COMPLAINT", "UPI", "DEVICE"] = Field(
        ..., description="Entity classification against which alert is anchored"
    )
    triggered_entity_id: str = Field(..., description="Specific ID of the flagged entity", examples=["SYN1000000042"])
    description: str = Field(..., description="Actionable rationale explaining reason for alert")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk probability index [0.0 - 1.0]", examples=[0.88])
    recommended_action: Literal["ALLOW", "MONITOR", "MANUAL_REVIEW", "EMERGENCY_FREEZE"] = Field(
        default="MANUAL_REVIEW", description="Prescribed LEA / Bank response action"
    )

    @field_validator("risk_score")
    @classmethod
    def round_score(cls, v: float) -> float:
        return round(v, 4)
