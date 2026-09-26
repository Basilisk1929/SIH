"""REST API Endpoints for Ingestion Service."""

from typing import Any, Dict, List, Union
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from ingestion.app.config import settings
from ingestion.app.services.csv_ingestor import CSVIngestionService
from ingestion.app.services.json_ingestor import JSONIngestionService
from ingestion.app.services.publisher import kafka_publisher
from ingestion.app.services.storage import storage_service

router = APIRouter()


@router.get("/health")
async def health_status() -> Dict[str, Any]:
    """Health and dependency readiness check."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "kafka_connected": kafka_publisher.is_connected,
        "kafka_enabled": settings.KAFKA_ENABLED,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/stats")
async def ingestion_metrics() -> Dict[str, Any]:
    """Retrieve cumulative ingestion counts and error rates."""
    return storage_service.get_stats()


@router.get("/rejections")
async def list_rejections(limit: int = Query(50, ge=1, le=500)) -> List[Dict[str, Any]]:
    """Inspect dead-letter rejected records with detailed validation error reasons."""
    return storage_service.get_recent_rejections(limit=limit)


# ------------------------------------------------------------------------------
# Generic CSV / JSON Ingestion Endpoints
# ------------------------------------------------------------------------------

@router.post("/csv/{entity_type}")
async def ingest_csv_upload(
    entity_type: str,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Ingest CSV batch via multipart file upload."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have .csv extension",
        )

    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")

    res = await CSVIngestionService.ingest_csv_content(
        entity_type=entity_type,
        csv_text=csv_text,
        source=f"UPLOAD:{file.filename}",
    )
    return res


@router.post("/json/{entity_type}")
async def ingest_json_payload(
    entity_type: str,
    payload: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Ingest single JSON record or array of records."""
    if isinstance(payload, list):
        return await JSONIngestionService.ingest_batch(
            entity_type=entity_type,
            records=payload,
            source="REST_JSON_BULK",
        )
    return await JSONIngestionService.ingest_record(
        entity_type=entity_type,
        raw_payload=payload,
        source="REST_JSON_SINGLE",
    )


# ------------------------------------------------------------------------------
# Typed Semantic Endpoints
# ------------------------------------------------------------------------------

@router.post("/transactions")
async def ingest_transaction(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Ingest single or batch financial transaction events."""
    return await ingest_json_payload("transaction", payload)


@router.post("/accounts")
async def ingest_account(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Ingest single or batch bank account lifecycle events."""
    return await ingest_json_payload("account", payload)


@router.post("/complaints")
async def ingest_complaint(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Ingest single or batch 1930 / NCRP cyber fraud complaint records."""
    return await ingest_json_payload("complaint", payload)


@router.post("/atm")
async def ingest_atm(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Ingest single or batch ATM terminal interaction events."""
    return await ingest_json_payload("atm", payload)


@router.post("/banks")
async def ingest_bank(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Ingest single or batch bank institutional directory updates."""
    return await ingest_json_payload("bank", payload)


@router.post("/alerts")
async def ingest_alert(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Ingest single or batch cybercrime detection alert triggers."""
    return await ingest_json_payload("alert", payload)
