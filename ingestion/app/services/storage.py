"""PostgreSQL storage and Dead-Letter Rejection repository for ingested data."""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from ingestion.app.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory dead-letter and valid record store for offline / dev mode
_IN_MEMORY_VALID_STORE: Dict[str, List[Dict[str, Any]]] = {
    "transaction": [],
    "account": [],
    "complaint": [],
    "atm": [],
    "bank": [],
    "alert": [],
}
_IN_MEMORY_REJECTIONS: List[Dict[str, Any]] = []


class IngestionStorageService:
    """Handles persistence of validated records and dead-letter rejected records."""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._init_db()

    def _init_db(self):
        """Initialize PostgreSQL async engine if configured."""
        try:
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                echo=False,
            )
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
            )
        except Exception as exc:
            logger.warning(f"PostgreSQL connection initialization failed: {exc}. Operating in in-memory mode.")
            self.engine = None
            self.session_factory = None

    async def save_valid_record(self, entity_type: str, record: Dict[str, Any]) -> bool:
        """Store validated and normalized event into database or fallback store."""
        # Always maintain in-memory buffer for fast query and testing
        if entity_type in _IN_MEMORY_VALID_STORE:
            _IN_MEMORY_VALID_STORE[entity_type].append(record)
            if len(_IN_MEMORY_VALID_STORE[entity_type]) > 20000:
                _IN_MEMORY_VALID_STORE[entity_type].pop(0)

        # If PostgreSQL session is available, attempt insert
        if self.session_factory:
            try:
                async with self.session_factory() as session:
                    # Ingested table insert (using generic JSONB event store)
                    query = text("""
                        INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, details, timestamp)
                        VALUES (:id, NULL, :action, :resource_type, :resource_id, :details, :ts)
                    """)
                    await session.execute(
                        query,
                        {
                            "id": uuid.uuid4(),
                            "action": f"INGEST_{entity_type.upper()}",
                            "resource_type": entity_type,
                            "resource_id": str(record.get("event_id", record.get("transaction_id", "N/A"))),
                            "details": json.dumps(record, default=str),
                            "ts": datetime.now(timezone.utc),
                        },
                    )
                    await session.commit()
                    return True
            except Exception as exc:
                logger.debug(f"DB insert skipped: {exc}")
                return True

        return True

    async def save_rejection(
        self,
        source: str,
        entity_type: str,
        raw_payload: Any,
        error_type: str,
        error_details: Any,
    ) -> Dict[str, Any]:
        """Record invalid or corrupted event separately in Dead-Letter Queue."""
        rejection_entry = {
            "rejection_id": f"REJ_{uuid.uuid4().hex[:12].upper()}",
            "source": source,
            "entity_type": entity_type,
            "raw_payload": raw_payload,
            "error_type": error_type,
            "error_details": error_details,
            "rejection_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 1. Store in memory
        _IN_MEMORY_REJECTIONS.append(rejection_entry)
        if len(_IN_MEMORY_REJECTIONS) > 10000:
            _IN_MEMORY_REJECTIONS.pop(0)

        # 2. Append to local dead-letter JSONL file if enabled
        if settings.ENABLE_LOCAL_DLQ_FILE:
            try:
                settings.DEAD_LETTER_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
                dlq_file = settings.DEAD_LETTER_LOCAL_DIR / "rejections.jsonl"
                with open(dlq_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rejection_entry, default=str) + "\n")
            except Exception as exc:
                logger.warning(f"Failed to append to DLQ file: {exc}")

        # 3. Log structured warning
        logger.warning(
            f"[REJECTION] Source: {source} | Entity: {entity_type} | "
            f"Error: {error_type} | ID: {rejection_entry['rejection_id']}"
        )
        return rejection_entry

    @staticmethod
    def get_recent_rejections(limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent dead-letter rejections."""
        return list(reversed(_IN_MEMORY_REJECTIONS[-limit:]))

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Return cumulative ingestion counts and error metrics."""
        return {
            "ingested_counts": {k: len(v) for k, v in _IN_MEMORY_VALID_STORE.items()},
            "total_valid_ingested": sum(len(v) for v in _IN_MEMORY_VALID_STORE.values()),
            "total_rejected_dlq": len(_IN_MEMORY_REJECTIONS),
        }

    @staticmethod
    def clear():
        """Clear memory buffers (primarily for unit tests)."""
        for k in _IN_MEMORY_VALID_STORE:
            _IN_MEMORY_VALID_STORE[k].clear()
        _IN_MEMORY_REJECTIONS.clear()


# Global singleton instance
storage_service = IngestionStorageService()
