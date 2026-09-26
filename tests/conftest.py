"""Pytest configuration and shared test fixtures."""

import os
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app

# Ensure testing environment flags are active
os.environ["ENVIRONMENT"] = "development"
os.environ["SYNTHETIC_DATA_ONLY"] = "True"
os.environ["DEBUG"] = "True"


@pytest.fixture
async def async_client():
    """Async HTTP test client bound to ASGI app via localhost transport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
        yield client


@pytest.fixture
def sample_synthetic_complaint_payload():
    """Valid synthetic complaint payload for endpoint testing."""
    return {
        "category": "Financial Fraud",
        "subcategory": "UPI QR Code & Impersonation Scam",
        "victim_state": "Maharashtra",
        "victim_district": "Mumbai Suburban",
        "reported_loss_inr": 35000.00,
        "suspect_upi": "suspect.mule99@synthaxis",
        "suspect_account_number": "SYN9012345678",
        "suspect_ifsc": "SYNB000101",
        "suspect_phone": "+919876543210",
        "incident_timestamp": "2024-09-20T14:30:00Z",
        "description_synthetic": "Complainant was instructed to scan QR code to receive refund.",
    }
