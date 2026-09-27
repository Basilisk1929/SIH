"""Pydantic schemas for end-to-end Transaction and Complaint intelligence pipelines."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TransactionPipelineRequest(BaseModel):
    """Payload to submit and evaluate an incoming transaction through the complete pipeline."""
    transaction_id: Optional[str] = Field(None, description="Unique transaction ID (generated if omitted)")
    txn_ref_no: Optional[str] = Field(None, description="Banking rail reference number")
    sender_account: str = Field(..., description="Originating account number", example="SYN1000004465")
    receiver_account: str = Field(..., description="Beneficiary account number", example="SYN1000002170")
    amount: float = Field(..., gt=0, description="Amount in INR", example=48500.0)
    rail_type: Optional[str] = Field("UPI", description="UPI, IMPS, NEFT, RTGS, ATM")
    sender_upi: Optional[str] = Field(None, example="sender@synthaxis")
    receiver_upi: Optional[str] = Field(None, example="mule.target@synthaxis")
    timestamp: Optional[str] = Field(None, description="ISO-8601 UTC timestamp")

    # Geospatial indicators
    latitude: Optional[float] = Field(None, description="Transaction origin latitude", example=28.6139)
    longitude: Optional[float] = Field(None, description="Transaction origin longitude", example=77.2090)
    location_name: Optional[str] = Field(None, example="New Delhi, India")

    # Velocity and behavioral metrics
    transactions_last_1h: Optional[int] = Field(0, ge=0)
    transactions_last_24h: Optional[int] = Field(0, ge=0)
    cashout_ratio: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    graph_degree: Optional[int] = Field(0, ge=0)
    complaint_link_count: Optional[int] = Field(0, ge=0)


class TransactionPipelineResponse(BaseModel):
    """Unified investigator-facing response combining risk, graph, geo, and alert intelligence."""
    transaction_id: str
    txn_ref_no: str
    sender_account: str
    receiver_account: str
    amount: float
    rail_type: str
    timestamp: str

    risk_assessment: Dict[str, Any] = Field(
        ..., description="XGBoost model risk score, band, and feature explanations"
    )
    graph_evidence: Dict[str, Any] = Field(
        ..., description="Neo4j relationship and multi-hop counterparty evidence"
    )
    geospatial_intelligence: Dict[str, Any] = Field(
        ..., description="H3 cell, ATM proximity, and cyber hotspot clustering"
    )
    alert: Optional[Dict[str, Any]] = Field(
        None, description="Real-time alert engine result if risk threshold exceeded"
    )
    pipeline_status: str = "SUCCESS"
    evaluated_at: str


class ComplaintPipelineRequest(BaseModel):
    """Payload to ingest a cybercrime complaint through the NLP, graph, and case pipeline."""
    narrative: str = Field(..., description="Raw incident complaint narrative text from citizen / 1930 portal")
    acknowledgement_no: Optional[str] = Field(None, description="NCRP acknowledgement number")
    victim_state: Optional[str] = Field(None, example="Delhi")
    victim_district: Optional[str] = Field(None, example="New Delhi")
    reported_loss_inr: Optional[float] = Field(None, description="Reported loss amount (extracted via NLP if omitted)")
    incident_timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp")


class ComplaintPipelineResponse(BaseModel):
    """Complete investigation result from NLP extraction, entity linking, graph, and case generation."""
    complaint_id: str
    acknowledgement_no: str
    raw_narrative: str
    extracted_entities: Dict[str, Any] = Field(..., description="Entities extracted via spaCy and regex")
    scam_typology: Dict[str, Any] = Field(..., description="Classified scam type and confidence score")
    linked_suspect_account: Optional[str] = None
    linked_suspect_upi: Optional[str] = None
    linked_suspect_phone: Optional[str] = None
    reported_loss_inr: float
    graph_relationship: Dict[str, Any] = Field(..., description="Neo4j graph linking complaint to suspect entities")
    intelligence_summary: Dict[str, Any] = Field(..., description="Risk priority, account escalation, and case docket")
    alert: Optional[Dict[str, Any]] = None
    pipeline_status: str = "SUCCESS"
    evaluated_at: str
