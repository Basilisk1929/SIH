"""ATM physical terminal cash-out interaction schema with envelope metadata."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import Field, field_validator
from ingestion.app.schemas.envelope import IngestionEnvelope


class ATMEvent(IngestionEnvelope):
    """Normalized ATM cash withdrawal or terminal interaction event."""

    atm_interaction_id: str = Field(..., description="Unique ATM switch transaction identifier", examples=["ATM_0000001"])
    account_number: str = Field(..., description="Debited bank account number", examples=["SYN1000000042"])
    atm_id: str = Field(..., description="Physical ATM kiosk hardware terminal identifier", examples=["ATM_SYN_4921"])
    location_id: str = Field(..., description="Geographical location ID of the ATM kiosk", examples=["LOC_00001"])
    amount: Decimal = Field(..., gt=0, description="Withdrawn cash amount in INR", examples=[40000.00])
    status: Literal["SUCCESS", "FAILED", "LIMIT_EXCEEDED"] = Field(
        default="SUCCESS", description="Terminal execution status"
    )
    card_number_masked: Optional[str] = Field(default="****-****-****-4912", description="PCI-DSS masked PAN")
    rapid_cashout_flag: Optional[bool] = Field(
        default=False, description="Flagged if cash withdrawal executed within minutes of fraudulent credit"
    )
    associated_transaction_id: Optional[str] = Field(
        default="N/A", description="Link to transaction record in transaction ledger"
    )

    @field_validator("amount")
    @classmethod
    def round_amount(cls, v: Decimal) -> Decimal:
        return round(v, 2)
