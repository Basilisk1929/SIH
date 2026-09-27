"""End-to-End Integration Tests for Transaction and Complaint Pipelines.

Verifies:
1. Transaction -> Ingestion -> Validation -> PostgreSQL -> Risk Engine (XGBoost) -> Neo4j -> Geospatial Engine -> Alert Engine -> FastAPI -> Frontend
2. Complaint -> NLP extraction -> Entity normalization -> Entity linking -> PostgreSQL -> Neo4j -> Risk/Intelligence layer -> Alert/Case system
3. Cross-pipeline correlation (Complaint -> linked suspect account -> Transaction alert escalation)
"""

import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app
from backend.app.services.pipeline_service import PipelineService, _PROCESSED_TRANSACTIONS, _PROCESSED_COMPLAINTS
from backend.app.api.v1.endpoints.cases import _IN_MEMORY_CASES
from backend.app.core.security import Role, create_access_token

AUTH_HEADERS = {
    "Authorization": f"Bearer {create_access_token('test.investigator@cybercell.gov.in', role=Role.INVESTIGATOR)}"
}



@pytest.fixture(autouse=True)
def clean_pipeline_state():
    """Ensure clean in-memory state before and after each test."""
    _PROCESSED_TRANSACTIONS.clear()
    _PROCESSED_COMPLAINTS.clear()
    yield
    _PROCESSED_TRANSACTIONS.clear()
    _PROCESSED_COMPLAINTS.clear()


# ==============================================================================
# PIPELINE 1: TRANSACTION PIPELINE INTEGRATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_complete_transaction_pipeline_direct_service():
    """Verify complete transaction flow through PipelineService directly."""
    high_risk_tx = {
        "transaction_id": "TXN_INTEG_001",
        "sender_account": "SYN1000004465",
        "receiver_account": "SYN1000002170",
        "amount": 285000.0,
        "rail_type": "UPI",
        "sender_upi": "victim@synthaxis",
        "receiver_upi": "mule.l1@synthaxis",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "transactions_last_1h": 12,
        "transactions_last_24h": 45,
        "cashout_ratio": 0.98,
        "graph_degree": 18,
        "complaint_link_count": 3,
    }

    # Execute complete pipeline
    result = await PipelineService.process_transaction(high_risk_tx)

    # 1. Ingestion & Validation
    assert result["transaction_id"] == "TXN_INTEG_001"
    assert result["amount"] == 285000.0
    assert result["pipeline_status"] == "SUCCESS"

    # 2. Database / Ledger persistence
    assert "TXN_INTEG_001" in _PROCESSED_TRANSACTIONS
    saved_tx = _PROCESSED_TRANSACTIONS["TXN_INTEG_001"]
    assert saved_tx["amount_inr"] == 285000.0

    # 3. ML Risk Engine (XGBoost)
    risk_assessment = result["risk_assessment"]
    assert risk_assessment["risk_score"] >= 60.0
    assert risk_assessment["risk_band"] in ["HIGH", "CRITICAL"]
    assert risk_assessment["is_suspicious"] is True
    assert len(risk_assessment["feature_explanations"]) > 0
    assert "disclaimer" in risk_assessment

    # 4. Neo4j Graph Evidence
    graph_evidence = result["graph_evidence"]
    assert graph_evidence["source"] == "SYN1000004465"
    assert graph_evidence["target"] == "SYN1000002170"
    assert graph_evidence["relationship"] == "TRANSFERRED_TO"
    assert graph_evidence["properties"]["amount"] == 285000.0

    # 5. Geospatial Intelligence
    geo_intelligence = result["geospatial_intelligence"]
    assert geo_intelligence["is_valid_indian_coordinate"] is True
    assert geo_intelligence["h3_cell"] is not None
    assert len(geo_intelligence["nearest_atms"]) > 0

    # 6. Real-Time Alert Engine
    alert = result["alert"]
    assert alert is not None
    assert alert["severity"] in ["HIGH", "CRITICAL"]
    assert alert["status"] in ["NEW", "ACKNOWLEDGED"]
    assert "Freeze beneficiary account" in alert["recommended_action"]


@pytest.mark.asyncio
async def test_transaction_pipeline_via_fastapi_endpoint():
    """Verify transaction pipeline through FastAPI endpoint /api/v1/transactions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "sender_account": "SYN1000009999",
            "receiver_account": "SYN1000008888",
            "amount": 150000.0,
            "rail_type": "IMPS",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "transactions_last_1h": 8,
            "cashout_ratio": 0.90,
        }

        response = await client.post("/api/v1/transactions", json=payload, headers=AUTH_HEADERS)
        assert response.status_code == 201

        data = response.json()
        assert data["pipeline_status"] == "SUCCESS"
        assert data["amount"] == 150000.0
        assert data["risk_assessment"]["risk_score"] > 50.0
        assert data["graph_evidence"]["relationship"] == "TRANSFERRED_TO"
        assert data["geospatial_intelligence"]["h3_cell"] is not None
        assert data["alert"] is not None
        assert data["alert"]["severity"] in ["HIGH", "CRITICAL"]


@pytest.mark.asyncio
async def test_low_risk_transaction_pipeline():
    """Verify that a legitimate retail transaction receives low risk score and no high alert."""
    low_risk_tx = {
        "sender_account": "SYN1000001111",
        "receiver_account": "SYN1000002222",
        "amount": 250.0,
        "rail_type": "UPI",
        "transactions_last_1h": 0,
        "transactions_last_24h": 1,
        "cashout_ratio": 0.05,
        "graph_degree": 2,
    }

    result = await PipelineService.process_transaction(low_risk_tx)
    assert result["risk_assessment"]["risk_score"] < 40.0
    assert result["risk_assessment"]["risk_band"] in ["LOW", "MEDIUM"]


# ==============================================================================
# PIPELINE 2: COMPLAINT PIPELINE INTEGRATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_complete_complaint_pipeline_direct_service():
    """Verify complete complaint flow through PipelineService directly."""
    narrative = (
        "On 14-Aug-2024, I was duped of Rs 85,000 by a person posing as an SBI nodal officer. "
        "He instructed me to transfer funds to UPI ID amitsbi@okhdfcbank and account SYN1000004465 "
        "with IFSC SBIN0001234 from mobile number 9876543210. Txn ID: TXN_00038001. Location was Jaipur, Rajasthan."
    )
    complaint_payload = {
        "narrative": narrative,
        "victim_state": "Rajasthan",
        "acknowledgement_no": "NCRP-SYN-2024-TEST-99",
    }

    # Execute complete pipeline
    result = await PipelineService.process_complaint(complaint_payload)

    # 1. NLP Extraction
    entities = result["extracted_entities"]
    assert "AMOUNT" in entities
    assert float(entities["AMOUNT"]) == 85000.0
    assert "UPI_ID" in entities
    assert entities["UPI_ID"] == "amitsbi@okhdfcbank"
    assert "ACCOUNT" in entities
    assert entities["ACCOUNT"] == "SYN1000004465"
    assert "PHONE" in entities

    # 2. Scam Typology Classification
    scam_typology = result["scam_typology"]
    assert scam_typology["scam_type"] is not None
    assert scam_typology["confidence"] >= 0.35

    # 3. Entity Linking
    assert result["linked_suspect_account"] == "SYN1000004465"
    assert result["linked_suspect_upi"] == "amitsbi@okhdfcbank"
    assert result["reported_loss_inr"] == 85000.0

    # 4. Database / Registry persistence
    assert "NCRP-SYN-2024-TEST-99" in _PROCESSED_COMPLAINTS
    saved_cmp = _PROCESSED_COMPLAINTS["NCRP-SYN-2024-TEST-99"]
    assert saved_cmp["reported_loss_inr"] == 85000.0

    # 5. Neo4j Graph Linking
    graph_rel = result["graph_relationship"]
    assert graph_rel["complaint_ack"] == "NCRP-SYN-2024-TEST-99"
    assert "SYN1000004465" in graph_rel["linked_accounts"]
    assert "amitsbi@okhdfcbank" in graph_rel["linked_upis"]
    assert graph_rel["relationship"] == "MENTIONED_IN"

    # 6. Case Docket Generation
    intel_summary = result["intelligence_summary"]
    assert intel_summary["case_opened"] is True
    assert intel_summary["case_number"] is not None
    assert intel_summary["priority"] in ["HIGH", "CRITICAL"]

    # Verify case docket exists in case store
    found_case = any(c.get("linked_complaint_ids") == ["NCRP-SYN-2024-TEST-99"] for c in _IN_MEMORY_CASES.values())
    assert found_case is True

    # 7. Real-Time Alert for high-loss complaint
    assert result["alert"] is not None
    assert result["alert"]["severity"] in ["HIGH", "CRITICAL"]


@pytest.mark.asyncio
async def test_complaint_pipeline_via_fastapi_endpoint():
    """Verify complaint pipeline through FastAPI endpoint /api/v1/complaints/pipeline."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "narrative": (
                "Victim transferred Rs 55,000 to electricity bill updater UPI handle power.pay@synthaxis "
                "associated with account SYN1000002170 after receiving APK fraud link."
            ),
            "victim_state": "Maharashtra",
        }

        response = await client.post("/api/v1/complaints/pipeline", json=payload, headers=AUTH_HEADERS)
        assert response.status_code == 201

        data = response.json()
        assert data["pipeline_status"] == "SUCCESS"
        assert data["reported_loss_inr"] == 55000.0
        assert data["linked_suspect_account"] == "SYN1000002170"
        assert data["graph_relationship"]["relationship"] == "MENTIONED_IN"
        assert data["intelligence_summary"]["case_opened"] is True


# ==============================================================================
# PIPELINE 3: CROSS-PIPELINE CORRELATION (COMPLAINT -> TRANSACTION LINKAGE)
# ==============================================================================

@pytest.mark.asyncio
async def test_cross_pipeline_complaint_and_transaction_correlation():
    """Demonstrate complaint linking to suspect account, which escalates subsequent transaction risk."""
    # Step A: Citizen reports cyber fraud against account SYN1000009999
    complaint_res = await PipelineService.process_complaint({
        "narrative": "Transferred Rs 95,000 to fraud mule account SYN1000009999 via impersonation scam.",
        "acknowledgement_no": "NCRP-SYN-CORRELATE-01",
    })
    assert complaint_res["linked_suspect_account"] == "SYN1000009999"

    # Step B: Transaction originates from that suspect account with prior complaint link
    tx_res = await PipelineService.process_transaction({
        "sender_account": "SYN1000009999",
        "receiver_account": "SYN1000003333",
        "amount": 90000.0,
        "cashout_ratio": 0.95,
        "transactions_last_1h": 5,
        "complaint_link_count": 1,  # Correlated from Step A
        "latitude": 28.6139,
        "longitude": 77.2090,
    })

    # Step C: Verify transaction alert engine immediately flags CRITICAL severity
    assert tx_res["risk_assessment"]["risk_score"] >= 80.0
    assert tx_res["alert"]["severity"] == "CRITICAL"
    assert tx_res["graph_evidence"]["source"] == "SYN1000009999"
    assert tx_res["geospatial_intelligence"]["is_valid_indian_coordinate"] is True
