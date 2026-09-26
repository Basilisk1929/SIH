"""Mandatory Event Envelope definition applied to all ingested streams."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class IngestionEnvelope(BaseModel):
    """Standardized metadata envelope wrapping every ingested cyber intelligence event."""

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Globally unique identifier for the event",
        examples=["9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"],
    )
    event_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when event occurred at source system (UTC)",
    )
    source: str = Field(
        ...,
        description="Origin source system (e.g. NCRP_1930, UPI_GATEWAY, CBS_CORE_BANKING, ATM_SWITCH)",
        examples=["UPI_GATEWAY"],
    )
    schema_version: str = Field(
        default="1.0.0",
        description="Semantic version of the event schema",
        examples=["1.0.0"],
    )
    ingestion_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when event was accepted by ingestion pipeline (UTC)",
    )
