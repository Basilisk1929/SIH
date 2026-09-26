"""FastAPI Application Entrypoint for Independently Deployable Ingestion Service."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from ingestion.app.api.router import router as ingest_router
from ingestion.app.config import settings
from ingestion.app.services.publisher import kafka_publisher


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context managing Kafka publisher connection lifecycle."""
    await kafka_publisher.start()
    yield
    await kafka_publisher.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Independently deployable high-throughput data ingestion service for cybercrime intelligence & financial feeds.",
    openapi_url=f"{settings.INGEST_API_PREFIX}/openapi.json",
    docs_url=f"{settings.INGEST_API_PREFIX}/docs",
    redoc_url=f"{settings.INGEST_API_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce defensive security headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# Mount Ingestion API router
app.include_router(ingest_router, prefix=settings.INGEST_API_PREFIX, tags=["Data Ingestion"])


@app.get("/", tags=["Root"])
async def root():
    """Service status and documentation links."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": f"{settings.INGEST_API_PREFIX}/docs",
        "kafka_connected": kafka_publisher.is_connected,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ingestion.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
