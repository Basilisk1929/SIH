"""Central API v1 router mounting all modular domain routers and intelligence subsystems."""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    accounts,
    alerts,
    analytics,
    audit,
    auth,
    cases,
    complaints,
    demo,
    graph,
    health,
    transactions,
)
from ml.api.routes import router as risk_router
from geo.api.routes import router as geo_router
from nlp.api.routes import router as nlp_router

api_router = APIRouter()

# Core Platform Routers
api_router.include_router(health.router, prefix="/health", tags=["Health & Diagnostics"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Bank Accounts & Mule Detection"])
api_router.include_router(cases.router, prefix="/cases", tags=["Case Docket Management"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Real-Time Alert Engine"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["NCRP/1930 Complaints"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Financial Risk & Accounts"])
api_router.include_router(graph.router, prefix="/graph", tags=["Mule Network Graph"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Intelligence Analytics"])
api_router.include_router(audit.router, prefix="/audit", tags=["Forensic Audit Trail"])
api_router.include_router(demo.router, prefix="/demo", tags=["SIH End-to-End Demo Simulator"])

# Integrated Intelligence Subsystems
api_router.include_router(risk_router)  # /risk/predict, /risk/model-info, /risk/health
api_router.include_router(geo_router)   # /geo/cell-analysis, /geo/coordinate-analysis, /geo/nearest-atms
api_router.include_router(nlp_router)   # /nlp/extract, /nlp/evaluate, /nlp/health
