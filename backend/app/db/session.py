"""PostgreSQL async database session management using SQLAlchemy 2.0 and asyncpg."""

import os
import ssl
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.app.core.config import settings

# Detect if we need SSL for managed cloud databases (Render, Supabase, etc.)
_is_cloud_db = (
    ".render.com" in settings.DATABASE_URL
    or ".supabase.co" in settings.DATABASE_URL
    or os.getenv("PGSSLMODE") == "require"
    or settings.ENVIRONMENT.lower() in ("production", "prod", "staging")
)

# Create async engine with connection pooling and statement pre-compilation
engine_kwargs = {
    "echo": settings.DEBUG and not _is_cloud_db,  # Reduce noise in production
    "pool_pre_ping": True,
}
if "sqlite" not in settings.DATABASE_URL:
    # Render free tier allows max ~50 connections; keep pool conservative
    engine_kwargs["pool_size"] = 5 if _is_cloud_db else 10
    engine_kwargs["max_overflow"] = 10 if _is_cloud_db else 20

# Enable SSL for cloud-hosted PostgreSQL (Render requires SSL)
if _is_cloud_db and "sqlite" not in settings.DATABASE_URL:
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    engine_kwargs["connect_args"] = {"ssl": ssl_ctx}

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a managed SQLAlchemy async session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


_db_available: bool | None = None


async def check_db_health() -> bool:
    """Check whether PostgreSQL database engine is reachable."""
    global _db_available
    try:
        async with engine.connect() as conn:
            _db_available = True
            return True
    except Exception:
        _db_available = False
        return False


def reset_db_health_cache() -> None:
    """Reset cached database availability status."""
    global _db_available
    _db_available = None


async def get_db_optional() -> AsyncGenerator[AsyncSession | None, None]:
    """Dependency that yields a managed database session if connection succeeds, else None."""
    global _db_available
    if _db_available is False:
        yield None
        return

    is_alive = await check_db_health()
    if not is_alive:
        yield None
        return

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


