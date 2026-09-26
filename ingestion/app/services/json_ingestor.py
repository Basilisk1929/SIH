"""JSON ingestion service implementing normalization, validation, deduplication, and routing."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from pydantic import ValidationError

from ingestion.app.config import settings
from ingestion.app.schemas import (
    AccountEvent,
    AlertEvent,
    ATMEvent,
    ComplaintEvent,
    TransactionEvent,
    BankEvent,
)
from ingestion.app.services.deduplicator import duplicate_detector
from ingestion.app.services.normalizer import DataNormalizer
from ingestion.app.services.publisher import kafka_publisher
from ingestion.app.services.storage import storage_service

logger = logging.getLogger(__name__)

SCHEMA_MAP = {
    "transaction": TransactionEvent,
    "transactions": TransactionEvent,
    "account": AccountEvent,
    "accounts": AccountEvent,
    "complaint": ComplaintEvent,
    "complaints": ComplaintEvent,
    "atm": ATMEvent,
    "bank": BankEvent,
    "banks": BankEvent,
    "alert": AlertEvent,
    "alerts": AlertEvent,
}


class JSONIngestionService:
    """Processes single and bulk JSON cyber intelligence feeds."""

    @staticmethod
    def _get_schema_class(entity_type: str):
        normalized_key = entity_type.lower().strip()
        schema_cls = SCHEMA_MAP.get(normalized_key)
        if not schema_cls:
            raise ValueError(
                f"Unsupported entity type: '{entity_type}'. Must be one of: {list(SCHEMA_MAP.keys())}"
            )
        return schema_cls

    @classmethod
    async def ingest_record(
        cls,
        entity_type: str,
        raw_payload: Any,
        source: str = "JSON_STREAM",
    ) -> Dict[str, Any]:
        """Ingest, normalize, validate, deduplicate, and route a single JSON event."""
        if not isinstance(raw_payload, dict):
            rej = await storage_service.save_rejection(
                source=source,
                entity_type=entity_type,
                raw_payload=raw_payload,
                error_type="MALFORMED_JSON_PAYLOAD",
                error_details="Expected a JSON object (dict), received a non-dict value.",
            )
            return {"status": "REJECTED", "reason": "Malformed JSON object", "rejection": rej}

        # 1. Resolve schema class
        try:
            schema_cls = cls._get_schema_class(entity_type)
        except ValueError as err:
            rej = await storage_service.save_rejection(
                source=source,
                entity_type=entity_type,
                raw_payload=raw_payload,
                error_type="UNKNOWN_ENTITY_TYPE",
                error_details=str(err),
            )
            return {"status": "REJECTED", "reason": str(err), "rejection": rej}

        # 2. Normalize raw payload
        normalized = DataNormalizer.normalize_record(raw_payload, entity_type)

        # 3. Ensure mandatory envelope attributes
        now_utc = datetime.now(timezone.utc)
        if "event_id" not in normalized or not normalized["event_id"]:
            normalized["event_id"] = str(uuid.uuid4())
        if "event_timestamp" not in normalized or not normalized["event_timestamp"]:
            normalized["event_timestamp"] = now_utc
        if "source" not in normalized or not normalized["source"]:
            normalized["source"] = source
        if "schema_version" not in normalized or not normalized["schema_version"]:
            normalized["schema_version"] = settings.CURRENT_SCHEMA_VERSION
        if "ingestion_timestamp" not in normalized or not normalized["ingestion_timestamp"]:
            normalized["ingestion_timestamp"] = now_utc

        # 4. Duplicate Detection
        is_dup, fingerprint = duplicate_detector.check_and_record(entity_type, normalized)
        if is_dup:
            logger.info(f"Duplicate {entity_type} event suppressed (Fingerprint: {fingerprint[:12]})")
            return {
                "status": "DUPLICATE",
                "message": "Duplicate event suppressed",
                "fingerprint": fingerprint,
                "event_id": normalized["event_id"],
            }

        # 5. Schema Validation
        try:
            validated_event = schema_cls(**normalized)
        except ValidationError as val_err:
            error_details = val_err.errors(include_url=False)
            rej = await storage_service.save_rejection(
                source=source,
                entity_type=entity_type,
                raw_payload=raw_payload,
                error_type="SCHEMA_VALIDATION_ERROR",
                error_details=error_details,
            )
            return {
                "status": "REJECTED",
                "reason": "Schema validation failed",
                "errors": error_details,
                "rejection_id": rej["rejection_id"],
            }

        # 6. Storage & Kafka Dispatch
        event_dict = validated_event.model_dump(mode="json")
        await storage_service.save_valid_record(entity_type, event_dict)
        await kafka_publisher.publish_event(entity_type, event_dict)

        return {
            "status": "ACCEPTED",
            "event_id": validated_event.event_id,
            "entity_type": entity_type,
            "ingestion_timestamp": validated_event.ingestion_timestamp.isoformat(),
        }

    @classmethod
    async def ingest_batch(
        cls,
        entity_type: str,
        records: List[Dict[str, Any]],
        source: str = "JSON_BATCH",
    ) -> Dict[str, Any]:
        """Process a batch of JSON records."""
        total = len(records)
        accepted = 0
        rejected = 0
        duplicates = 0
        rejection_summaries = []

        for r in records:
            res = await cls.ingest_record(entity_type, r, source=source)
            status = res.get("status")
            if status == "ACCEPTED":
                accepted += 1
            elif status == "DUPLICATE":
                duplicates += 1
            else:
                rejected += 1
                rejection_summaries.append(res)

        return {
            "total_records": total,
            "accepted_count": accepted,
            "rejected_count": rejected,
            "duplicate_count": duplicates,
            "rejections": rejection_summaries[:20],  # Return preview of errors
        }
