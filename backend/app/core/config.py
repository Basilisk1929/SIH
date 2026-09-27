"""Application settings and environment configuration management."""

import logging
import os
import secrets
from typing import Any, List
from pydantic import field_validator
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

    env_mode = os.getenv("ENVIRONMENT", "development").lower()
    if env_mode in ("production", "prod", "staging"):
        raise RuntimeError(
            "FATAL SECURITY MISCONFIGURATION: JWT_SECRET_KEY must be provided via environment variable "
            "or secret mount in production/staging environments. Ephemeral secret generation is prohibited."
        )

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

    # Server Bindings (PORT env var is set by Render/Railway at runtime)
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = int(os.getenv("PORT", "8000"))
    ALLOWED_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://frontend-bay-tau-86.vercel.app",
    ]

    @field_validator("ALLOWED_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(item).strip() for item in v if str(item).strip()]
        return v

    # Auto-seed database with synthetic records on startup if requested
    AUTO_SEED: bool = False

    # Security & JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "cyber_intelligence_db"
    POSTGRES_USER: str = "cyber_admin"
    POSTGRES_PASSWORD: str = ""  # MUST be set via environment variable (never hardcode)
    DATABASE_URL: str = ""  # MUST be set via environment variable

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Any) -> str:
        """Normalize cloud-provider DATABASE_URL formats for asyncpg compatibility.

        Render provides `postgres://...` but SQLAlchemy asyncpg requires
        `postgresql+asyncpg://...`. This validator handles the conversion automatically.
        """
        if not v or not isinstance(v, str):
            return v or ""
        url = v.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""  # MUST be set via environment variable (never hardcode)

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

