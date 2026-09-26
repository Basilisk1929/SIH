"""Pydantic schemas for investigative case docket management and export."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CaseCreate(BaseModel):
    """Payload to instantiate a new investigative case docket."""

    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    priority: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    total_fraud_amount_inr: Decimal = Field(default=Decimal("0.00"), ge=0)
    assigned_to: Optional[str] = Field(None, description="Investigator email or badge number")


class CaseUpdate(BaseModel):
    """Payload to update case docket status and disposition."""

    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(ACTIVE|UNDER_REVIEW|FROZEN|RESOLVED|CLOSED|DISMISSED)$")
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    recovered_amount_inr: Optional[Decimal] = Field(None, ge=0)
    assigned_to: Optional[str] = None
    investigation_notes: Optional[str] = Field(None, max_length=2000)


class CaseResponse(BaseModel):
    """Investigative case docket response."""

    id: str
    case_number: str
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    total_fraud_amount_inr: Decimal
    recovered_amount_inr: Decimal
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    """Paginated list of investigative cases."""

    total: int
    page: int
    limit: int
    cases: List[CaseResponse]


class CaseExportResponse(BaseModel):
    """Forensic case dossier export schema complying with evidence chain-of-custody."""

    export_id: str
    case_number: str
    exported_at: datetime
    exported_by: str
    exported_role: str
    case_data: Dict[str, Any]
    chain_of_custody_hash: str
    legal_disclaimer: str = (
        "Statutory Notice: This export contains law enforcement intelligence compiled "
        "under statutory mandate. Do not alter or disclose outside authorized judicial proceedings."
    )
