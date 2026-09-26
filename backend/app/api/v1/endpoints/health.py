"""System health, service readiness, and dependency connectivity status endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.db.neo4j import check_neo4j_health
from backend.app.db.session import get_db

router = APIRouter()


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
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Readiness probe verifying PostgreSQL and Neo4j connectivity."""
    db_ok = False
    try:
        res = await db.execute(text("SELECT 1"))
        db_ok = res.scalar() == 1
    except Exception:
        db_ok = False

    neo4j_ok = await check_neo4j_health()

    is_ready = db_ok or settings.ENVIRONMENT == "development"

    return {
        "status": "ready" if is_ready else "degraded",
        "services": {
            "postgresql": "connected" if db_ok else "unavailable",
            "neo4j": "connected" if neo4j_ok else "unavailable_using_fallback_engine",
        },
        "environment": settings.ENVIRONMENT,
    }
