"""Ingestion service exports."""

from ingestion.app.services.normalizer import DataNormalizer
from ingestion.app.services.deduplicator import DuplicateDetector, duplicate_detector
from ingestion.app.services.publisher import KafkaEventPublisher, kafka_publisher
from ingestion.app.services.storage import IngestionStorageService, storage_service
from ingestion.app.services.json_ingestor import JSONIngestionService
from ingestion.app.services.csv_ingestor import CSVIngestionService

__all__ = [
    "DataNormalizer",
    "DuplicateDetector",
    "duplicate_detector",
    "KafkaEventPublisher",
    "kafka_publisher",
    "IngestionStorageService",
    "storage_service",
    "JSONIngestionService",
    "CSVIngestionService",
]
