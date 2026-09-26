"""Ingestion service settings and configuration."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):
    """Configuration for streaming and batch ingestion service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "CyberShield-Ingestion-Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    INGEST_API_PREFIX: str = "/api/v1/ingest"

    # Server Bindings
    HOST: str = "127.0.0.1"
    PORT: int = 8001

    # Kafka Broker Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_ENABLED: bool = os.getenv("KAFKA_ENABLED", "True").lower() in ("true", "1", "yes")
    KAFKA_CLIENT_ID: str = "cybershield-ingestor"

    # Kafka Topic Mappings
    TOPIC_TRANSACTIONS: str = "ingest.transactions"
    TOPIC_ACCOUNTS: str = "ingest.accounts"
    TOPIC_COMPLAINTS: str = "ingest.complaints"
    TOPIC_ATM: str = "ingest.atm"
    TOPIC_BANKS: str = "ingest.banks"
    TOPIC_ALERTS: str = "ingest.alerts"
    TOPIC_DEAD_LETTER: str = "ingest.dead_letter"

    # PostgreSQL Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://cyber_admin:cyber_dev_password_123!@localhost:5432/cyber_intelligence_db",
    )

    # Ingestion & Schema Parameters
    CURRENT_SCHEMA_VERSION: str = "1.0.0"
    DEAD_LETTER_LOCAL_DIR: Path = Path("./data/dead_letter")
    ENABLE_LOCAL_DLQ_FILE: bool = True
    DUPLICATE_CACHE_SIZE: int = 50_000


settings = IngestionSettings()
