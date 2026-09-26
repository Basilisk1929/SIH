"""Central API v1 router mounting all modular domain routers."""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    analytics,
    auth,
    complaints,
    graph,
    health,
    transactions,
    alerts,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health & Diagnostics"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["NCRP/1930 Complaints"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Financial Risk & Accounts"])
api_router.include_router(graph.router, prefix="/graph", tags=["Mule Network Graph"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Intelligence Analytics"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Real-Time Alert Engine"])
