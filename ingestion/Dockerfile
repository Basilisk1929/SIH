# ==============================================================================
# Ingestion Service Dockerfile - Independently Deployable FastAPI Service
# ==============================================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ingestion/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY ingestion /app/ingestion

RUN addgroup --system ingestgroup && adduser --system --ingroup ingestgroup ingestuser
USER ingestuser

EXPOSE 8001

HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/v1/ingest/health || exit 1

CMD ["uvicorn", "ingestion.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
