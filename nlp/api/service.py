"""Standalone FastAPI microservice for Cybercrime NLP Intelligence."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nlp.api.routes import router

app = FastAPI(
    title="Cybercrime NLP Intelligence Service",
    description="NLP microservice extracting forensic entities, structured values, and scam typologies from Indian cybercrime incident narratives.",
    version="1.0.0",
)

# CORS configuration
allowed_origins = os.getenv("NLP_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
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
        "service": "Cybercrime NLP Intelligence Service",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "extract": "POST /nlp/extract",
            "evaluate": "POST /nlp/evaluate",
            "health": "GET /nlp/health",
        },
    }
