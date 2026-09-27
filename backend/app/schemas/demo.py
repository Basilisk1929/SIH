"""Pydantic schemas for the Phase 11F End-to-End SIH Demo Simulator."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DemoSimulateResponse(BaseModel):
    """Structured response payload of an executed end-to-end synthetic fraud scenario."""

    scenario_id: str = Field(..., description="Unique scenario execution identifier")
    status: str = Field("COMPLETED", description="Simulation status")
    is_demo: bool = Field(True, description="Flag indicating synthetic demonstration data")
    disclaimer: str = Field(
        "SIH DEMONSTRATION SCENARIO — All entities, accounts, and complaints are synthetic simulations for evaluative benchmarking.",
        description="Statutory simulation disclosure",
    )
    narrative_summary: str
    victim_account: str
    mule_account: str
    amount_inr: float
    complaint: Optional[Dict[str, Any]] = None
    transaction: Optional[Dict[str, Any]] = None
    ml_risk_assessment: Optional[Dict[str, Any]] = None
    graph_evidence: Optional[Dict[str, Any]] = None
    geospatial_intelligence: Optional[Dict[str, Any]] = None
    cashout_prediction: Optional[Dict[str, Any]] = None
    alert: Optional[Dict[str, Any]] = None
    created_at: str


class DemoResetResponse(BaseModel):
    """Response payload confirming purging of synthetic demonstration artifacts."""

    status: str = Field("SUCCESS", description="Reset operation status")
    purged_alerts: int = Field(0, description="Count of purged demo alerts")
    purged_transactions: int = Field(0, description="Count of purged demo transactions")
    purged_complaints: int = Field(0, description="Count of purged demo complaints")
    purged_cases: int = Field(0, description="Count of purged demo case dockets")
    purged_graph_edges: int = Field(0, description="Count of purged demo graph edges")
    message: str = "Synthetic demonstration artifacts successfully purged from active intelligence stores."
    reset_at: datetime


class DemoStatusResponse(BaseModel):
    """Status summary of active demonstration artifacts currently residing in memory."""

    is_demo_mode_enabled: bool = True
    active_demo_alerts_count: int
    active_demo_cases_count: int
    active_demo_transactions_count: int
    active_demo_complaints_count: int
    disclaimer: str = "SIH Demonstration Mode active."
