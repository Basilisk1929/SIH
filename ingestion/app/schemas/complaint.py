"""Cybercrime Complaint ingestion schema with envelope metadata."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field, field_validator
from ingestion.app.schemas.envelope import IngestionEnvelope


class ComplaintEvent(IngestionEnvelope):
    """Normalized cybercrime complaint event from 1930 Helpline or NCRP Portal."""

    complaint_id: str = Field(..., description="Internal system complaint ID", examples=["CMP_0000001"])
    acknowledgement_no: str = Field(..., description="Citizen NCRP Ack reference", examples=["NCRP-SYN-2024-100001"])
    incident_date: datetime = Field(..., description="Timestamp when fraud debit took place")
    reported_date: datetime = Field(..., description="Timestamp when report was logged by citizen")
    reporting_delay_hours: Optional[int] = Field(default=0, ge=0, description="Hours elapsed before filing")
    category: str = Field(..., description="Modus operandi category", examples=["digital arrest scam"])
    reported_loss_amount: Decimal = Field(..., ge=0, description="Financial loss claimed in INR", examples=[480000.00])
    narrative_synthetic: Optional[str] = Field(default=None, description="Citizen incident narrative description")
    victim_account_number: Optional[str] = Field(default="N/A", description="Complainant's debited account")
    suspect_account_number: Optional[str] = Field(default="N/A", description="Suspect beneficiary account")
    suspect_upi_id: Optional[str] = Field(default="N/A", description="Suspect VPA handle")
    suspect_phone_number: Optional[str] = Field(default="N/A", description="Suspect calling/WhatsApp number")
    initial_transaction_id: Optional[str] = Field(default="N/A", description="Primary fraudulent debit transaction ID")
    suspect_device_id: Optional[str] = Field(default="N/A", description="Suspect hardware device identifier")
    victim_state: Optional[str] = Field(default="Maharashtra", description="Complainant state of residence")
    suspect_state: Optional[str] = Field(default="Haryana", description="Suspect branch/jurisdiction state")
    cluster_id: Optional[str] = Field(default="NONE", description="Syndicate cluster association")
    ground_truth_category: Optional[str] = Field(default=None, description="Validated ground-truth typology")

    @field_validator("reported_loss_amount")
    @classmethod
    def round_amount(cls, v: Decimal) -> Decimal:
        return round(v, 2)
