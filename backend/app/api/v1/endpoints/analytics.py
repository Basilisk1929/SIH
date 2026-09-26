"""Cybercrime intelligence dashboard analytics and summary KPI endpoints."""

from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview() -> Dict[str, Any]:
    """Provide high-level intelligence metrics for dashboard header."""
    return {
        "total_complaints_reported": 14280,
        "total_financial_loss_inr": 284500000.0,
        "active_mule_rings_detected": 42,
        "accounts_frozen_in_golden_hour": 189,
        "saved_loss_inr": 48200000.0,
        "critical_escalations": 37,
        "compliance_mode": "Strict Synthetic Simulation (SIH)",
    }


@router.get("/category-distribution")
async def get_category_distribution() -> Dict[str, Any]:
    """Breakdown of complaints by cyber fraud modus operandi."""
    return {
        "categories": [
            {"name": "UPI & QR Code Fraud", "count": 5210, "percentage": 36.5},
            {"name": "Part-Time Job / Task Scam", "count": 3140, "percentage": 22.0},
            {"name": "Electricity Bill APK Phishing", "count": 2150, "percentage": 15.0},
            {"name": "Illegal Instant Loan App", "count": 1820, "percentage": 12.7},
            {"name": "Forex & Crypto Investment", "count": 1240, "percentage": 8.7},
            {"name": "Sextortion / Video Call", "count": 720, "percentage": 5.1},
        ]
    }


@router.get("/state-distribution")
async def get_state_distribution() -> Dict[str, Any]:
    """Geographic breakdown across Indian states for hotspot mapping."""
    return {
        "states": [
            {"state": "Maharashtra", "complaints": 2850, "loss_inr": 58000000.0},
            {"state": "Delhi", "complaints": 2410, "loss_inr": 51200000.0},
            {"state": "Karnataka", "complaints": 1940, "loss_inr": 42100000.0},
            {"state": "Telangana", "complaints": 1680, "loss_inr": 34900000.0},
            {"state": "Uttar Pradesh", "complaints": 1590, "loss_inr": 29800000.0},
            {"state": "Gujarat", "complaints": 1220, "loss_inr": 24500000.0},
            {"state": "Rajasthan", "complaints": 980, "loss_inr": 18200000.0},
            {"state": "Haryana", "complaints": 890, "loss_inr": 16700000.0},
            {"state": "West Bengal", "complaints": 720, "loss_inr": 13900000.0},
        ]
    }
