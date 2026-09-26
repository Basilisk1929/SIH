"""FastAPI application microservice for Geospatial Intelligence."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from geo.api.routes import router

app = FastAPI(
    title="Geospatial Intelligence Engine API",
    description="H3 hexagonal spatial aggregation, DBSCAN cybercrime hotspot detection, and RBI ATM proximity analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "Geospatial Intelligence Engine",
        "version": "1.0.0",
        "documentation": "/docs",
    }
