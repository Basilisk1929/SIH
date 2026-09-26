"""Tests for NLP FastAPI microservice endpoints."""

from fastapi.testclient import TestClient
from nlp.api.service import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Cybercrime NLP Intelligence Service" in data["service"]


def test_health_check_endpoint():
    response = client.get("/nlp/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["scam_categories_count"] == 10


def test_extract_endpoint_success():
    payload = {
        "text": (
            "Complainant Suresh Bhatia received call stating FedEx parcel sent from Mumbai with illegal currency. "
            "Forwarded to fake police officer (+919816980800). Directed transfer of ₹50,536.84 to suspect account "
            "SYN1000000065 at Synth ICICI Banking Corp (UPI: pooja.jadhav.919@synicici)."
        ),
        "link_entities": True,
    }
    response = client.post("/nlp/extract", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["scam_type"] == "impersonation"
    assert data["confidence"] >= 0.70
    assert len(data["entities"]) >= 4

    labels = {e["label"] for e in data["entities"]}
    assert "ACCOUNT" in labels
    assert "PHONE" in labels
    assert "AMOUNT" in labels


def test_extract_endpoint_empty_text_fails():
    response = client.post("/nlp/extract", json={"text": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_evaluate_endpoint():
    response = client.post("/nlp/evaluate", json={"sample_size": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["evaluated_complaints_count"] == 10
    assert data["scam_classification_accuracy"] >= 0.80
    assert "macro_averages" in data
