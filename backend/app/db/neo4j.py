"""Neo4j graph database driver and session lifecycle management."""

import logging
from typing import AsyncGenerator, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_driver: Optional[AsyncDriver] = None


def get_neo4j_driver() -> AsyncDriver:
    """Return the global singleton Neo4j async driver instance."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
        )
    return _driver


async def close_neo4j_driver() -> None:
    """Close the active Neo4j driver connection pool."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver pool closed cleanly.")


def _get_session_kwargs() -> dict:
    kwargs = {}
    if getattr(settings, "NEO4J_DATABASE", None):
        kwargs["database"] = settings.NEO4J_DATABASE
    return kwargs


async def get_neo4j_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a managed Neo4j async session."""
    driver = get_neo4j_driver()
    async with driver.session(**_get_session_kwargs()) as session:
        yield session


async def get_optional_neo4j_session() -> AsyncGenerator[AsyncSession | None, None]:
    """Dependency that yields an active Neo4j session if accessible, else None."""
    try:
        driver = get_neo4j_driver()
        async with driver.session(**_get_session_kwargs()) as session:
            yield session
    except Exception:
        yield None



async def check_neo4j_health() -> bool:
    """Verify connectivity to the Neo4j cluster."""
    try:
        driver = get_neo4j_driver()
        async with driver.session(**_get_session_kwargs()) as session:
            result = await session.run("RETURN 1 AS ping")
            record = await result.single()
            return record is not None and record["ping"] == 1
    except Exception as exc:
        logger.warning(f"Neo4j health check failed: {exc}")
        return False
