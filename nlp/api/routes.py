"""API route definitions for cybercrime NLP service."""

from fastapi import APIRouter, HTTPException, status
from nlp.api.schemas import (
    ComplaintExtractRequest,
    ComplaintExtractResponse,
    ExtractedEntityResponse,
    EvaluateRequest,
    EvaluateResponse,
)
from nlp.pipelines.cybercrime_nlp_pipeline import CybercrimeNLPPipeline
from nlp.evaluation.evaluator import ComplaintGroundTruthEvaluator

router = APIRouter(prefix="/nlp", tags=["NLP Intelligence"])

# Shared singleton pipeline instance
_pipeline = CybercrimeNLPPipeline()
_evaluator = ComplaintGroundTruthEvaluator(pipeline=_pipeline)


@router.post(
    "/extract",
    response_model=ComplaintExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract entities and classify cybercrime incident narrative",
)
async def extract_complaint_entities(payload: ComplaintExtractRequest) -> ComplaintExtractResponse:
    """Analyze unstructured citizen complaint narrative:
    1. Preprocesses and normalizes text.
    2. Extracts PERSON, BANK, ACCOUNT, PHONE, UPI_ID, AMOUNT, LOCATION, DATE, TRANSACTION_ID, SCAM_TYPE.
    3. Standardizes entities to canonical formats.
    4. Links entities against synthetic financial registries.
    5. Categorizes narrative into 10 cyber scam typologies with confidence calibration.
    """
    input_text = payload.text
    if not input_text or not input_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint text cannot be empty",
        )

    result = _pipeline.process(input_text, link_entities=payload.link_entities)

    entity_responses = [
        ExtractedEntityResponse(
            text=e.text,
            label=e.label,
            start=e.start,
            end=e.end,
            normalized_value=e.normalized_value,
            confidence=round(e.confidence, 2),
            extractor=e.extractor,
            linked_entity=e.linked_entity,
        )
        for e in result.entities
    ]

    return ComplaintExtractResponse(
        scam_type=result.scam_type,
        confidence=result.confidence,
        category_probabilities=result.category_probabilities,
        entities=entity_responses,
        metadata={
            "processing_time_ms": round(result.processing_time_ms, 2),
            "entities_count": len(entity_responses),
            "text_length": len(result.cleaned_text),
        },
    )


@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate NLP pipeline against synthetic ground-truth complaints",
)
async def evaluate_complaints(payload: EvaluateRequest) -> EvaluateResponse:
    """Run pipeline against synthetic complaints ground truth and return Precision, Recall, and F1 scores."""
    try:
        metrics = _evaluator.evaluate(sample_size=payload.sample_size)
        if "error" in metrics:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=metrics["error"])
        return EvaluateResponse(**metrics)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(exc)}",
        )


@router.get("/health", status_code=status.HTTP_200_OK, summary="Health status of NLP microservice")
async def health_check():
    """Verify NLP pipeline models and services are operational."""
    return {
        "status": "healthy",
        "service": "Cybercrime NLP Intelligence Service",
        "spacy_loaded": _pipeline.extractor.spacy_extractor is not None,
        "scam_categories_count": len(_pipeline.classifier.CATEGORIES),
    }
