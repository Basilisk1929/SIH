"""Transaction ingestion schema with envelope metadata."""

from decimal import Decimal
from typing import Literal, Optional
from pydantic import Field, field_validator
from ingestion.app.schemas.envelope import IngestionEnvelope


class TransactionEvent(IngestionEnvelope):
    """Normalized financial transaction event."""

    transaction_id: str = Field(..., description="Unique banking reference number or RRN", examples=["TXN_00010928"])
    sender_account_number: str = Field(..., description="Debited account identifier", examples=["SYN1000000042"])
    receiver_account_number: Optional[str] = Field(
        default="N/A", description="Credited account identifier or N/A for cash withdrawals", examples=["SYN1000000084"]
    )
    sender_upi_id: Optional[str] = Field(default="N/A", description="Originating UPI VPA", examples=["citizen@synaxis"])
    receiver_upi_id: Optional[str] = Field(default="N/A", description="Destination UPI VPA", examples=["mule@synaxis"])
    sender_device_id: Optional[str] = Field(default="N/A", description="Sender terminal/phone hardware ID", examples=["DEV_0000018"])
    receiver_device_id: Optional[str] = Field(default="N/A", description="Receiver terminal/phone hardware ID", examples=["DEV_0000084"])
    amount: Decimal = Field(..., gt=0, description="Transaction sum in INR", examples=[48500.00])
    transaction_type: Literal["TRANSFER", "CASH_IN", "CASH_OUT", "PAYMENT"] = Field(
        default="TRANSFER", description="Operational category of transaction"
    )
    payment_channel: Literal["UPI", "IMPS", "NEFT", "RTGS", "ATM"] = Field(
        default="UPI", description="Underlying clearing rail"
    )
    currency: str = Field(default="INR", description="Three-letter ISO currency code")
    sender_location_id: Optional[str] = Field(default="LOC_00001", description="Geographic origin reference")
    receiver_location_id: Optional[str] = Field(default="LOC_00001", description="Geographic destination reference")
    is_fraud: Optional[bool] = Field(default=False, description="Ground truth or preliminary fraud assessment")
    pattern_type: Optional[str] = Field(default="NORMAL", description="Detected or annotated behavioral pattern")
    cluster_id: Optional[str] = Field(default="NONE", description="Syndicate cluster reference")

    @field_validator("amount")
    @classmethod
    def round_amount(cls, v: Decimal) -> Decimal:
        return round(v, 2)
