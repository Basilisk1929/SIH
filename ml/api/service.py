"""Standalone FastAPI microservice for the Financial Transaction Risk Engine."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ml.api.routes import router

app = FastAPI(
    title="Financial Transaction Risk Engine Service",
    description="Real-time transaction risk scoring microservice powered by gradient boosted trees (XGBoost), providing calibrated scores, risk bands, and explainable feature attributions.",
    version="1.0.0",
)

# CORS configuration
allowed_origins = os.getenv("RISK_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", summary="Root endpoint")
async def root():
    return {
        "service": "Financial Transaction Risk Engine Service",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "predict": "POST /risk/predict",
            "model_info": "GET /risk/model-info",
            "health": "GET /risk/health",
        },
    }
