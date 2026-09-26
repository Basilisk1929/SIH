"""FastAPI route handlers for transaction risk scoring."""

from fastapi import APIRouter, HTTPException, status
from ml.api.schemas import (
    ModelInfoResponse,
    RiskPredictRequest,
    RiskPredictResponse,
)
from ml.inference.predictor import RiskInferenceService

router = APIRouter(prefix="/risk", tags=["Risk Engine"])

# Shared singleton inference service instance
_inference_service = RiskInferenceService()


@router.post(
    "/predict",
    response_model=RiskPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict transaction risk score, risk band, and feature explanations",
)
async def predict_transaction_risk(payload: RiskPredictRequest) -> RiskPredictResponse:
    """Score transaction risk using trained gradient boosted ensemble.
    Returns:
    - calibrated risk_score from 0 to 100
    - categorical risk_band (LOW, MEDIUM, HIGH, CRITICAL)
    - top driving feature explanations
    - mandatory legal disclaimer stating risk score represents an investigative signal, not proof of criminal activity.
    """
    try:
        data_dict = payload.model_dump()
        result = _inference_service.predict(data_dict)
        return RiskPredictResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk scoring failed: {str(exc)}",
        )


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve active model metadata, feature configuration, and evaluation metrics",
)
async def get_model_info() -> ModelInfoResponse:
    """Retrieve metadata of the current active risk model."""
    config = _inference_service.engine.config
    return ModelInfoResponse(
        model_type=config.get("model_type", "XGBClassifier"),
        version=config.get("version", "1.0.0"),
        trained_at=config.get("trained_at"),
        feature_names=_inference_service.engine.feature_names,
        metrics=config.get("metrics"),
    )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check for risk engine service",
)
async def health_check():
    """Verify that model artifacts are loaded and inference engine is operational."""
    return {
        "status": "healthy",
        "service": "Financial Transaction Risk Engine",
        "model_loaded": _inference_service.engine.model is not None,
    }
