"""Main FastAPI Application Entrypoint.

Cybercrime Intelligence and Financial Transaction Risk Detection Platform (SIH Prototype).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.api.v1.endpoints import alerts
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.db.neo4j import close_neo4j_driver


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and graceful shutdown."""
    # Startup sequence
    setup_logging(debug=settings.DEBUG)
    yield
    # Shutdown sequence
    await close_neo4j_driver()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-oriented Cybercrime Intelligence and Financial Transaction Risk "
        "Detection Platform (SIH Prototype). Evaluated strictly with synthetic datasets."
    ),
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS Middleware with strict origin allowlist
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce defense-in-depth HTTP security headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return sanitized error response to prevent data/trace leaks."""
    if settings.DEBUG:
        # In debug mode during local development, provide readable context
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "detail": str(exc)},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "InternalServerError", "message": "An unexpected error occurred. Reference has been logged."},
    )


# Mount central v1 API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# Direct /alerts root mounting for prompt compliance
app.include_router(alerts.router, prefix="/alerts")


@app.get("/", tags=["Root"])
async def root():
    """Root metadata endpoint."""
    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "documentation": f"{settings.API_V1_PREFIX}/docs",
        "compliance": "SYNTHETIC_DATA_ENVIRONMENT_ONLY",
    }
