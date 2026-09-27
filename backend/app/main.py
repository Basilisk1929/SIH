"""Main FastAPI Application Entrypoint.

Cybercrime Intelligence and Financial Transaction Risk Detection Platform (SIH Prototype).
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.api.v1.endpoints import accounts, alerts, auth, cases, complaints, health, transactions
from backend.app.api.v1.router import api_router
from ml.api.routes import router as risk_router
from geo.api.routes import router as geo_router
from nlp.api.routes import router as nlp_router
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.core.sanitizer import sanitize_for_logging
from backend.app.db.neo4j import close_neo4j_driver


logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and graceful shutdown."""
    setup_logging(debug=settings.DEBUG)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.ENVIRONMENT} mode")
    yield
    logger.info("Initiating graceful shutdown sequence")
    await close_neo4j_driver()


# Conditionally disable OpenAPI documentation in production/staging
_is_prod = settings.ENVIRONMENT.lower() in ("production", "prod", "staging")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-oriented Cybercrime Intelligence and Financial Transaction Risk "
        "Detection Platform (SIH Prototype). Evaluated strictly with synthetic datasets."
    ),
    openapi_url=None if _is_prod else f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=None if _is_prod else f"{settings.API_V1_PREFIX}/docs",
    redoc_url=None if _is_prod else f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# Enforce strict CORS policies (wildcards prohibited in production/staging)
if settings.ENVIRONMENT.lower() in ("production", "prod", "staging") and "*" in settings.ALLOWED_CORS_ORIGINS:
    raise RuntimeError(
        "FATAL SECURITY MISCONFIGURATION: Wildcard CORS origin ('*') is strictly prohibited in production!"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_origin_regex=r"^https:\/\/([a-zA-Z0-9_-]+\.)?vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Forwarded-For",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "bypass-tunnel-reminder",
    ],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce defense-in-depth HTTP security headers complying with CERT-In & RBI guidelines."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self';"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), "
        "microphone=(), payment=(), usb=()"
    )
    # Prevent browser caching of sensitive transactional and identity intelligence
    if request.url.path.startswith("/api/") or "/auth/" in request.url.path:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"

    return response


# --- Unified Structured Error Handlers ---


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Structured handler for standard HTTP errors."""
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers or {},
        content={
            "error": "HttpException",
            "status_code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Structured handler for schema validation failures without internal stack leaks."""
    sanitized_errors = []
    for err in exc.errors():
        sanitized_errors.append({
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error"),
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "status_code": 422,
            "message": "Request parameter validation failed.",
            "details": sanitized_errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Sanitized 500 error handler preventing data, credentials, and trace leaks."""
    raw_error = str(exc)
    safe_error = sanitize_for_logging(raw_error)
    logger.error(f"UNHANDLED_EXCEPTION at {request.url.path}: {safe_error}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "status_code": 500,
            "message": "An unexpected error occurred. The incident has been recorded in the security audit log.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Mount central v1 API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Direct root mountings for prompt compliance and dual routing
app.include_router(health.router, prefix="/health")
app.include_router(alerts.router, prefix="/alerts")
app.include_router(auth.router, prefix="/auth")
app.include_router(cases.router, prefix="/cases")
app.include_router(accounts.router, prefix="/accounts")
app.include_router(transactions.router, prefix="/transactions")
app.include_router(complaints.router, prefix="/complaints")
app.include_router(risk_router)
app.include_router(geo_router)
app.include_router(nlp_router)



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
