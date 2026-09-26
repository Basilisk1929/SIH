"""Bank Account ingestion schema with envelope metadata."""

import re
from decimal import Decimal
from typing import Literal, Optional
from pydantic import Field, field_validator
from ingestion.app.schemas.envelope import IngestionEnvelope

IFSC_REGEX = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


class AccountEvent(IngestionEnvelope):
    """Normalized bank account lifecycle or update event."""

    account_number: str = Field(..., description="Unique bank account identifier", examples=["SYN1000000042"])
    customer_id: str = Field(..., description="Owning customer profile reference", examples=["CUST_0000042"])
    bank_name: str = Field(..., description="Banking entity denomination", examples=["State Bank of Synth"])
    ifsc_code: str = Field(..., description="Indian Financial System Code (11 alphanumeric characters)", examples=["SYNB0001091"])
    branch_name: Optional[str] = Field(default="Main Branch", description="Branch location")
    account_type: Literal["SAVINGS", "CURRENT", "JAN_DHAN", "SALARY"] = Field(default="SAVINGS")
    status: Literal["ACTIVE", "WATCHLIST", "FROZEN", "DORMANT", "CLOSED"] = Field(default="ACTIVE")
    opening_date: Optional[str] = Field(default=None, description="Account inception date YYYY-MM-DD")
    current_balance: Decimal = Field(default=Decimal("0.00"), description="Present balance in INR")
    is_mule: Optional[bool] = Field(default=False, description="Mule account classification flag")
    mule_tier: Optional[int] = Field(default=0, ge=0, le=3, description="Mule tier level (0=Clean, 1=L1, 2=L2, 3=L3)")
    cluster_id: Optional[str] = Field(default="NONE", description="Syndicate cluster association")
    location_id: Optional[str] = Field(default="LOC_00001", description="Branch jurisdiction location ID")

    @field_validator("ifsc_code")
    @classmethod
    def validate_ifsc(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not IFSC_REGEX.match(cleaned):
            raise ValueError(f"Invalid Indian IFSC Code format: '{cleaned}'. Expected 4 letters + 0 + 6 alphanumeric.")
        return cleaned

    @field_validator("account_number")
    @classmethod
    def clean_account_number(cls, v: str) -> str:
        return v.strip().upper()
