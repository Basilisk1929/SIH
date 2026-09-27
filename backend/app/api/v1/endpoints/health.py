"""System health, service readiness, and dependency connectivity status endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Response, status
from backend.app.core.config import settings
from backend.app.db.neo4j import check_neo4j_health
from backend.app.db.session import check_db_health

router = APIRouter()


async def check_redis_health() -> bool:
    """Probe Redis availability with strict timeout."""
    if not settings.REDIS_URL or settings.REDIS_URL == "":
        return False
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=1.0)
        pong = await client.ping()
        await client.aclose()
        return bool(pong)
    except Exception:
        return False


@router.get("", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Basic liveness probe."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mode": "SYNTHETIC_DEVELOPMENT",
        "timestamp_compliance": "Synthetic data mode enforced",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(response: Response) -> Dict[str, Any]:
    """Readiness probe verifying PostgreSQL and Neo4j connectivity."""
    db_ok = await check_db_health()
    neo4j_ok = await check_neo4j_health()
    redis_ok = await check_redis_health()

    # Core readiness = PostgreSQL connected. Neo4j uses fallback engine if unavailable.
    # Redis is not required for core operation (rate limit, broadcast, revocation all in-memory).
    is_prod = settings.ENVIRONMENT.lower() in ("production", "prod", "staging")
    is_ready = db_ok or (not is_prod)

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if db_ok else ("ready_dev_fallback" if not is_prod else "degraded"),
        "services": {
            "postgresql": "connected" if db_ok else "unavailable",
            "neo4j": "connected" if neo4j_ok else "unavailable_using_fallback_engine",
            "redis": "connected" if redis_ok else "not_provisioned_using_in_memory",
        },
        "environment": settings.ENVIRONMENT,
    }


