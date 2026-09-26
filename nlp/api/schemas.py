"""Pydantic schemas for the NLP extraction microservice."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class ComplaintExtractRequest(BaseModel):
    """Input payload for POST /nlp/extract."""
    text: Optional[str] = Field(None, description="Raw cybercrime complaint narrative")
    complaint_text: Optional[str] = Field(None, description="Alias for text field")
    link_entities: bool = Field(True, description="Whether to resolve entities against database registry")

    @model_validator(mode="before")
    @classmethod
    def populate_text(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if not values.get("text") and values.get("complaint_text"):
                values["text"] = values["complaint_text"]
        return values


class ExtractedEntityResponse(BaseModel):
    """Extracted forensic entity item."""
    text: str
    label: str  # PERSON, BANK, ACCOUNT, PHONE, UPI_ID, AMOUNT, LOCATION, DATE, TRANSACTION_ID, SCAM_TYPE
    start: int
    end: int
    normalized_value: Any
    confidence: float
    extractor: str
    linked_entity: Optional[Dict[str, Any]] = None


class ComplaintExtractResponse(BaseModel):
    """Output payload for POST /nlp/extract."""
    scam_type: str = Field(..., description="Top classified cybercrime scam category")
    confidence: float = Field(..., description="Classification confidence score (0.0 - 1.0)")
    category_probabilities: Optional[Dict[str, float]] = Field(None, description="Distribution across all 10 scam typologies")
    entities: List[ExtractedEntityResponse] = Field(default_factory=list, description="Extracted forensic entities")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluateRequest(BaseModel):
    """Request payload for /nlp/evaluate."""
    sample_size: int = Field(50, ge=1, le=500, description="Number of synthetic ground-truth complaints to evaluate")


class EvaluateResponse(BaseModel):
    """Evaluation metrics response containing Precision, Recall, and F1 score."""
    evaluated_complaints_count: int
    scam_classification_accuracy: float
    macro_averages: Dict[str, float]
    micro_averages: Dict[str, float]
    per_entity_metrics: Dict[str, Dict[str, Any]]
