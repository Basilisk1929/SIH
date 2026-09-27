"""Pydantic schemas for investigative case docket management, workflow, notes, evidence, timeline, and export."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaseCreate(BaseModel):
    """Payload to instantiate a new investigative case docket."""

    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    priority: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    alert_id: Optional[str] = Field(None, description="Originating Alert ID if applicable")
    total_fraud_amount_inr: Decimal = Field(default=Decimal("0.00"), ge=0)
    assigned_to: Optional[str] = Field(None, description="Investigator email or badge number")
    assigned_investigator: Optional[str] = Field(None, description="Alias for assigned_to")
    initial_notes: Optional[str] = Field(None, max_length=4000)
    linked_alert_ids: Optional[List[str]] = Field(default_factory=list)
    linked_account_numbers: Optional[List[str]] = Field(default_factory=list)
    linked_complaint_ids: Optional[List[str]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def resolve_assignment(cls, values: Any) -> Any:
        if isinstance(values, dict):
            assigned = values.get("assigned_investigator") or values.get("assigned_to")
            if assigned:
                values["assigned_to"] = assigned
                values["assigned_investigator"] = assigned
        return values


class CaseFromAlertCreate(BaseModel):
    """Payload to instantiate a case docket directly from an existing alert."""

    alert_id: str = Field(..., description="ID of the alert to convert to a case docket")
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    assigned_to: Optional[str] = Field(None)
    assigned_investigator: Optional[str] = Field(None)
    initial_notes: Optional[str] = Field(None, max_length=4000)
    attach_prediction: bool = Field(True, description="Whether to attach cash-out prediction evidence if available")

    @model_validator(mode="before")
    @classmethod
    def resolve_assignment(cls, values: Any) -> Any:
        if isinstance(values, dict):
            assigned = values.get("assigned_investigator") or values.get("assigned_to")
            if assigned:
                values["assigned_to"] = assigned
                values["assigned_investigator"] = assigned
        return values


class CaseUpdate(BaseModel):
    """Payload to update case docket status, priority, and disposition."""

    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(
        None,
        pattern="^(OPEN|ASSIGNED|INVESTIGATING|ON_HOLD|RESOLVED|CLOSED|ACTIVE|UNDER_REVIEW|DISMISSED)$",
    )
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    recovered_amount_inr: Optional[Decimal] = Field(None, ge=0)
    assigned_to: Optional[str] = None
    assigned_investigator: Optional[str] = None
    investigation_notes: Optional[str] = Field(None, max_length=4000)
    notes: Optional[str] = Field(None, max_length=4000)

    @model_validator(mode="before")
    @classmethod
    def resolve_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            assigned = values.get("assigned_investigator") or values.get("assigned_to")
            if assigned:
                values["assigned_to"] = assigned
                values["assigned_investigator"] = assigned
            notes_val = values.get("notes") or values.get("investigation_notes")
            if notes_val:
                values["investigation_notes"] = notes_val
                values["notes"] = notes_val
        return values


class CaseAssignRequest(BaseModel):
    """Payload to assign an authorized investigator to a case docket."""

    assigned_investigator: str = Field(..., min_length=2, max_length=255, description="Badge, email, or name of assigned investigator")
    notes: Optional[str] = Field(None, max_length=2000)


class CaseNoteCreate(BaseModel):
    """Payload to append an official investigative note or judicial entry."""

    content: str = Field(..., min_length=1, max_length=5000)
    is_internal: bool = Field(True, description="Internal LEA note vs. cross-agency disclosure")


class CaseNoteResponse(BaseModel):
    """Response model for a persisted case note."""

    id: str
    note_id: Optional[str] = None
    case_id: str
    author: Optional[str] = None
    author_id: str
    author_name: str
    author_role: str
    content: str
    is_internal: bool = True
    created_at: datetime
    timestamp: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "id" in values and not values.get("note_id"):
                values["note_id"] = str(values["id"])
            if not values.get("author"):
                values["author"] = values.get("author_name") or values.get("author_id")
            if "created_at" in values and not values.get("timestamp"):
                values["timestamp"] = values["created_at"]
        return values


class CaseEvidenceCreate(BaseModel):
    """Payload to link existing platform intelligence as structured case evidence."""

    evidence_type: str = Field(
        ...,
        pattern="^(TRANSACTION|ACCOUNT|COMPLAINT|GRAPH_ENTITY|GRAPH_RELATIONSHIP|GEO_LOCATION|ALERT|CASHOUT_PREDICTION)$",
    )
    evidence_reference_id: Optional[str] = None
    reference_id: Optional[str] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    metadata_json: Optional[Dict[str, Any]] = None
    metadata_info: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_inputs(cls, values: Any) -> Any:
        if isinstance(values, dict):
            ref = values.get("evidence_reference_id") or values.get("reference_id")
            if ref:
                values["evidence_reference_id"] = str(ref)
                values["reference_id"] = str(ref)
            meta = values.get("metadata_json") or values.get("metadata_info")
            if meta is not None:
                values["metadata_json"] = meta
                values["metadata_info"] = meta
        return values


class CaseEvidenceResponse(BaseModel):
    """Response model for linked case evidence."""

    id: str
    case_id: str
    evidence_type: str
    evidence_reference_id: str
    reference_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    metadata_info: Optional[Dict[str, Any]] = None
    added_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_evidence_aliases(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "evidence_reference_id" in values and not values.get("reference_id"):
                values["reference_id"] = values["evidence_reference_id"]
            if "metadata_json" in values and not values.get("metadata_info"):
                values["metadata_info"] = values["metadata_json"]
        return values


class CaseTimelineEventResponse(BaseModel):
    """Response model for immutable case timeline events."""

    id: str
    case_id: str
    event_type: str
    title: str
    description: Optional[str] = None
    actor_id: str
    actor_role: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CaseResolveRequest(BaseModel):
    """Payload to formally resolve an investigative case docket."""

    resolution_category: str = Field(
        ...,
        pattern="^(CONFIRMED_FRAUD|SUSPECTED_FRAUD|FALSE_POSITIVE|INSUFFICIENT_EVIDENCE|REFERRED|OTHER)$",
    )
    resolution_reason: Optional[str] = Field(None, max_length=255)
    resolution_notes: str = Field(..., min_length=3, max_length=4000)


class CaseCloseRequest(BaseModel):
    """Payload to formally close an investigative case docket."""

    closure_reason: Optional[str] = Field(None, max_length=255)
    closure_notes: Optional[str] = Field(None, max_length=4000)


class CaseResponse(BaseModel):
    """Standardized summary output representation for a case docket."""

    id: str
    case_number: str
    alert_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    total_fraud_amount_inr: Decimal
    recovered_amount_inr: Decimal
    assigned_to: Optional[str] = None
    assigned_investigator: Optional[str] = None
    assigned_at: Optional[datetime] = None
    assigned_by: Optional[str] = None
    created_by: Optional[str] = "SYSTEM"
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_status: Optional[str] = None
    resolution_category: Optional[str] = None
    resolution_reason: Optional[str] = None
    resolution_notes: Optional[str] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None
    linked_alert_ids: List[str] = Field(default_factory=list)
    linked_account_numbers: List[str] = Field(default_factory=list)
    linked_complaint_ids: List[str] = Field(default_factory=list)
    notes_count: int = 0
    evidence_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CaseDetailResponse(CaseResponse):
    """Complete case docket representation including nested notes, evidence, and timeline."""

    notes: List[CaseNoteResponse] = Field(default_factory=list)
    evidence: List[CaseEvidenceResponse] = Field(default_factory=list)
    timeline: List[CaseTimelineEventResponse] = Field(default_factory=list)
    linked_alert: Optional[Dict[str, Any]] = None


class CasePaginatedResponse(BaseModel):
    """Paginated list of case dockets."""

    total: int
    page: int
    limit: int
    cases: List[CaseResponse]


# Backward-compatible alias
CaseListResponse = CasePaginatedResponse


class CaseStatsResponse(BaseModel):
    """Summary statistics for investigative dashboard integration."""

    total_cases: int
    active_cases: int
    requiring_investigation: int
    requires_investigation: int
    assigned_to_user: int
    assigned_to_me: int
    recently_created: int
    recently_resolved: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]


class CaseExportResponse(BaseModel):
    """Forensic case dossier export schema complying with evidence chain-of-custody."""

    export_id: str
    case_number: str
    exported_at: datetime
    exported_by: str
    exported_role: str
    case_data: Dict[str, Any]
    case_metadata: Optional[Dict[str, Any]] = None
    chain_of_custody_hash: str
    dossier_sha256: Optional[str] = None
    legal_disclaimer: str = (
        "Statutory Notice: This export contains law enforcement intelligence compiled "
        "under statutory mandate (BNS / IT Act Section 65B). Do not alter or disclose outside authorized judicial proceedings."
    )
