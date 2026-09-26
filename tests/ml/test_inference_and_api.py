"""Tests for risk scoring REST API microservice."""

from fastapi.testclient import TestClient
from ml.api.service import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Risk Engine" in data["service"]


def test_health_endpoint():
    response = client.get("/risk/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_model_info_endpoint():
    response = client.get("/risk/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "XGBClassifier" in data["model_type"]
    assert len(data["feature_names"]) == 12


def test_predict_endpoint_high_risk():
    payload = {
        "transaction_id": "TXN_TEST_999",
        "sender_account_number": "SYN1000000001",
        "receiver_account_number": "SYN1000009999",
        "amount": 75000.0,
        "features": {
            "transaction_amount": 75000.0,
            "transaction_frequency": 4.5,
            "transactions_last_1h": 6.0,
            "transactions_last_24h": 12.0,
            "unique_receivers": 5.0,
            "unique_senders": 1.0,
            "cashout_ratio": 0.80,
            "account_age": 15.0,
            "graph_degree": 6.0,
            "graph_centrality": 0.45,
            "complaint_link_count": 2.0,
            "geographic_distance": 1200.0,
        },
    }
    response = client.post("/risk/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["transaction_id"] == "TXN_TEST_999"
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["risk_band"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert isinstance(data["feature_explanations"], list)
    assert len(data["feature_explanations"]) >= 1

    # Check mandatory investigative disclaimer
    assert "criminal activity" in data["disclaimer"].lower()
    assert "investigation" in data["disclaimer"].lower()


def test_predict_endpoint_flat_payload():
    payload = {
        "transaction_id": "TXN_FLAT_001",
        "amount": 2500.0,
        "transactions_last_1h": 0.0,
        "transactions_last_24h": 1.0,
    }
    response = client.post("/risk/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TXN_FLAT_001"
    assert 0.0 <= data["risk_score"] <= 100.0
