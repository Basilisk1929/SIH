"""Application settings and environment configuration management."""

import logging
import os
import secrets
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_jwt_secret() -> str:
    """Resolve JWT secret key using multi-tiered fallback:

    1. Environment variable
    2. Secret file (e.g. Docker secret mount /jwt_secret.txt)
    3. Ephemeral cryptographically random secret with warning log
    """
    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret and env_secret.strip():
        return env_secret.strip()

    secret_file_path = os.getenv("JWT_SECRET_FILE", "/run/secrets/jwt_secret.txt")
    if os.path.exists(secret_file_path):
        with open(secret_file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return content

    logging.warning(
        "JWT_SECRET_KEY not supplied. Generating ephemeral secret. "
        "Tokens will NOT persist across instance restarts or horizontal replicas!"
    )
    return secrets.token_hex(32)


class Settings(BaseSettings):
    """Central configuration validated via Pydantic v2 Settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Application
    APP_NAME: str = "CyberShield-Intel"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server Bindings
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    ALLOWED_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Security & JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "cyber_intelligence_db"
    POSTGRES_USER: str = "cyber_admin"
    POSTGRES_PASSWORD: str = "cyber_dev_password_123!"
    DATABASE_URL: str = (
        "postgresql+asyncpg://cyber_admin:cyber_dev_password_123!@localhost:5432/cyber_intelligence_db"
    )

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "cyber_graph_password_123!"

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Synthetic Compliance
    SYNTHETIC_DATA_ONLY: bool = True
    SYNTHETIC_SEED: int = 42

    # ML & Risk Thresholds
    MULE_RISK_THRESHOLD: float = 0.75

    def get_resolved_jwt_secret(self) -> str:
        if self.JWT_SECRET_KEY and self.JWT_SECRET_KEY.strip():
            return self.JWT_SECRET_KEY.strip()
        return get_jwt_secret()


settings = Settings()
