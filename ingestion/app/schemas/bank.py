"""Bank institutional metadata schema with envelope metadata."""

from typing import Literal, Optional
from pydantic import EmailStr, Field
from ingestion.app.schemas.envelope import IngestionEnvelope


class BankEvent(IngestionEnvelope):
    """Normalized banking institution registry event."""

    bank_code: str = Field(..., description="4-letter institution code", examples=["SYNB"])
    bank_name: str = Field(..., description="Full banking corporate denomination", examples=["State Bank of Synth"])
    category: Literal[
        "Public Sector", "Private Sector", "Payments Bank", "Regional Rural", "Cooperative"
    ] = Field(default="Public Sector", description="Banking licensing class")
    nodal_officer_email: Optional[EmailStr] = Field(
        default="nodal.fraud@synthbank.com", description="Cyber fraud nodal escalation email"
    )
    nodal_officer_phone: Optional[str] = Field(
        default="+919876543210", description="24x7 law enforcement liaison hotline"
    )
    headquarters_city: Optional[str] = Field(default="Mumbai", description="Corporate headquarters city")
    cbs_connected: bool = Field(default=True, description="Direct core banking API connectivity flag")
