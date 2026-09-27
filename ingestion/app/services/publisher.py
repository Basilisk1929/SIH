"""Asynchronous Kafka Event Publisher with resilient local fallback buffering."""

import json
import logging
from typing import Any, Dict, List, Optional
try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None  # type: ignore

from ingestion.app.config import settings

logger = logging.getLogger(__name__)


class KafkaEventPublisher:
    """Publishes validated and normalized events to Kafka topics."""

    def __init__(self):
        self.producer: Optional[Any] = None
        self.is_connected = False
        self.local_buffer: List[Dict[str, Any]] = []  # Fallback for local tests / offline Kafka

    async def start(self):
        """Initialize Kafka async producer connection."""
        if not settings.KAFKA_ENABLED or AIOKafkaProducer is None:
            logger.info("Kafka publishing disabled or aiokafka not installed. Using in-memory event buffer.")
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=settings.KAFKA_CLIENT_ID,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                request_timeout_ms=3000,
            )
            await self.producer.start()
            self.is_connected = True
            logger.info(f"Connected to Kafka broker at {settings.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as exc:
            self.is_connected = False
            logger.warning(
                f"Kafka broker offline ({exc}). Ingestion will buffer events locally without dropping data."
            )

    async def stop(self):
        """Clean shutdown of Kafka producer."""
        if self.producer and self.is_connected:
            try:
                await self.producer.stop()
                self.is_connected = False
                logger.info("Kafka producer stopped cleanly.")
            except Exception as exc:
                logger.warning(f"Error stopping Kafka producer: {exc}")

    def get_topic_for_entity(self, entity_type: str) -> str:
        """Resolve Kafka destination topic."""
        topic_map = {
            "transaction": settings.TOPIC_TRANSACTIONS,
            "account": settings.TOPIC_ACCOUNTS,
            "complaint": settings.TOPIC_COMPLAINTS,
            "atm": settings.TOPIC_ATM,
            "bank": settings.TOPIC_BANKS,
            "alert": settings.TOPIC_ALERTS,
            "rejection": settings.TOPIC_DEAD_LETTER,
        }
        return topic_map.get(entity_type.lower(), settings.TOPIC_DEAD_LETTER)

    async def publish_event(self, entity_type: str, event_payload: Dict[str, Any]) -> bool:
        """Publish event to designated topic or fallback buffer."""
        topic = self.get_topic_for_entity(entity_type)
        enriched_event = {
            "topic": topic,
            "entity_type": entity_type,
            "payload": event_payload,
        }

        if self.is_connected and self.producer:
            try:
                await self.producer.send_and_wait(topic, event_payload)
                return True
            except Exception as exc:
                logger.warning(f"Failed to publish to Kafka topic {topic}: {exc}. Buffering locally.")
                self.local_buffer.append(enriched_event)
                return False
        else:
            self.local_buffer.append(enriched_event)
            # Limit memory buffer size
            if len(self.local_buffer) > 20000:
                self.local_buffer.pop(0)
            return True

    def get_buffered_events(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return buffered events for inspection and tests."""
        if entity_type:
            return [e for e in self.local_buffer if e["entity_type"] == entity_type]
        return list(self.local_buffer)

    def clear_buffer(self):
        """Clear local buffer."""
        self.local_buffer.clear()


# Global singleton instance
kafka_publisher = KafkaEventPublisher()
