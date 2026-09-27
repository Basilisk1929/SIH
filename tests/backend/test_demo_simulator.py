"""Comprehensive tests for Phase 11F End-to-End SIH Demo Simulator.

Verifies:
- Demo scenario execution through full live platform:
  Synthetic Ingestion -> Validation -> ML Risk Assessment -> Neo4j Graph ->
  H3 Spatial Intelligence -> Phase 11C Cash-Out Predictor -> Alert Engine -> Case Workflow.
- Synthetic NCRP Complaint -> spaCy NLP extraction -> Entity Linking.
- Realistic but strictly synthetic data demarcation (SYN_DEMO_*, DEMO_TXN_*, DEMO-NCRP-*).
- Case creation linked to demo alert.
- Safe demo reset mechanism (purges ONLY demo data; preserves baseline data).
- RBAC role enforcement (Admin, Supervisor, Investigator).
- Forensic audit logging (DEMO_SIMULATION_STARTED, DEMO_SIMULATION_COMPLETED, DEMO_DATA_RESET).
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.alerts.engine import alert_engine
from backend.app.alerts.rate_limiter import rate_limiter
from backend.app.core.security import Role, clear_revoked_tokens, create_access_token
from backend.app.main import app
from backend.app.services.audit_service import AuditAction, audit_service
from backend.app.services.case_service import case_service

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def setup_teardown():
    clear_revoked_tokens()
    rate_limiter.reset()
    yield
    clear_revoked_tokens()


def _headers(role: Role, email: str = None) -> dict:
    subject = email or f"officer_{role.value.lower()}@cybercell.gov.in"
    token = create_access_token(subject=subject, role=role)
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. END-TO-END DEMO SCENARIO ORCHESTRATION
# =====================================================================

def test_demo_scenario_creation_full_pipeline(client):
    """Verify live multi-subsystem simulation through real backend pipelines."""
    headers = _headers(Role.INVESTIGATOR)
    response = client.post("/api/v1/demo/simulate-fraud", headers=headers)

    assert response.status_code == 201, f"Simulation failed: {response.text}"
    data = response.json()

    # Core Identifiers & Demarcation
    assert data["scenario_id"].startswith("SCENARIO_SIH_")
    assert data["status"] == "COMPLETED"
    assert data["is_demo"] is True
    assert "SYNTHETIC" in data["disclaimer"] or "SIH DEMONSTRATION" in data["disclaimer"]
    assert data["victim_account"] == "SYN_DEMO_VICTIM_4011"
    assert data["mule_account"] == "SYN_DEMO_MULE_9088"
    assert data["amount_inr"] == 85000.0

    # 1. NCRP Complaint & NLP Verification
    complaint = data.get("complaint")
    assert complaint is not None
    assert complaint["acknowledgement_no"].startswith("DEMO-NCRP-")
    assert "extracted_entities" in complaint
    assert "scam_typology" in complaint
    entities = complaint["extracted_entities"]
    assert isinstance(entities, dict)

    # 2. Transaction Pipeline Verification
    txn = data.get("transaction")
    assert txn is not None
    assert txn["transaction_id"].startswith("DEMO_TXN_")
    assert txn["sender_account"] == "SYN_DEMO_VICTIM_4011"
    assert txn["receiver_account"] == "SYN_DEMO_MULE_9088"

    # 3. XGBoost ML Risk Engine Verification
    risk = data.get("ml_risk_assessment")
    assert risk is not None
    assert 0.0 <= risk["risk_score"] <= 100.0
    assert risk["risk_score"] >= 70.0  # High-velocity fraud scenario
    assert risk["risk_band"] in ["HIGH", "CRITICAL"]
    assert risk["is_suspicious"] is True
    assert "feature_explanations" in risk

    # 4. Neo4j Graph Linking Evidence
    graph = data.get("graph_evidence")
    assert graph is not None
    assert graph.get("source") == "SYN_DEMO_VICTIM_4011"
    assert graph.get("target") == "SYN_DEMO_MULE_9088"
    assert graph.get("relationship") == "TRANSFERRED_TO"

    # 5. Phase 11C Predictive Cash-Out Location Engine
    cashout = data.get("cashout_prediction")
    assert cashout is not None
    assert cashout["account_id"] == "SYN_DEMO_MULE_9088"
    assert len(cashout["predicted_atms"]) >= 1
    top_atm = cashout["predicted_atms"][0]
    assert "atm_id" in top_atm
    assert "distance_km" in top_atm
    assert "prediction_score" in top_atm
    assert cashout["urgency_level"] in ["STANDARD", "ELEVATED", "HIGH", "CRITICAL"]

    # 6. Real-Time Alert Engine Verification
    alert = data.get("alert")
    assert alert is not None
    assert alert["alert_id"].startswith("ALT_")
    assert alert["severity"] in ["HIGH", "CRITICAL"]
    assert alert["status"] == "NEW"
    assert "threat_factors" in alert


# =====================================================================
# 2. CASE CREATION LINKED TO DEMO ALERT
# =====================================================================

def test_case_creation_from_demo_alert(client):
    """Verify an investigator can escalate the demo alert into an official case docket."""
    # First, run simulation to generate live alert
    inv_headers = _headers(Role.INVESTIGATOR)
    sim_res = client.post("/api/v1/demo/simulate-fraud", headers=inv_headers)
    assert sim_res.status_code == 201
    sim_data = sim_res.json()
    alert_id = sim_data["alert"]["alert_id"]

    # Escalate to Case Docket
    case_payload = {
        "alert_id": alert_id,
        "title": f"DEMO: Operation Utility Shield - Alert {alert_id}",
        "priority": "CRITICAL",
        "initial_notes": "Immediate golden-hour freeze notice initiated for suspect mule account.",
    }
    case_res = client.post("/api/v1/cases/from-alert", json=case_payload, headers=inv_headers)
    assert case_res.status_code == 201
    case_data = case_res.json()

    assert case_data["case_number"].startswith("CASE-")
    assert alert_id in case_data["linked_alert_ids"]
    assert case_data["status"] == "OPEN"


# =====================================================================
# 3. DEMO STATUS & SAFE PURGE RESET MECHANISM
# =====================================================================

def test_demo_status_and_clean_reset(client):
    """Verify demo status inspection and that reset removes ONLY demo data while preserving baseline records."""
    admin_headers = _headers(Role.ADMIN)
    inv_headers = _headers(Role.INVESTIGATOR)

    # 1. Create a non-demo baseline case to prove selective preservation
    baseline_payload = {
        "title": "Legitimate Baseline Investigation 101",
        "description": "Non-demo operational file",
        "priority": "LOW",
        "total_fraud_amount_inr": 5000.0,
        "linked_account_numbers": ["REGULAR_ACC_12345"],
    }
    baseline_res = client.post("/api/v1/cases", json=baseline_payload, headers=inv_headers)
    assert baseline_res.status_code == 201
    baseline_case_num = baseline_res.json()["case_number"]

    # 2. Trigger demo simulation
    sim_res = client.post("/api/v1/demo/simulate-fraud", headers=inv_headers)
    assert sim_res.status_code == 201

    # 3. Inspect demo status before reset
    status_res = client.get("/api/v1/demo/status", headers=inv_headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["active_demo_alerts_count"] >= 1
    assert status_data["is_demo_mode_enabled"] is True

    # 4. Perform Clean Demo Reset
    reset_res = client.post("/api/v1/demo/reset", headers=admin_headers)
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["status"] == "SUCCESS"
    assert reset_data["purged_alerts"] >= 1

    # 5. Verify demo records are 0
    post_status_res = client.get("/api/v1/demo/status", headers=inv_headers)
    post_status = post_status_res.json()
    assert post_status["active_demo_alerts_count"] == 0

    # 6. Verify non-demo baseline case was PRESERVED
    check_baseline = client.get(f"/api/v1/cases/{baseline_case_num}", headers=inv_headers)
    assert check_baseline.status_code == 200
    assert check_baseline.json()["title"] == "Legitimate Baseline Investigation 101"


# =====================================================================
# 4. RBAC & SECURITY AUTHORIZATION
# =====================================================================

def test_demo_rbac_authorization(client):
    """Verify demo endpoints enforce strict RBAC and reject unauthorized roles."""
    # 1. Unauthenticated request rejected
    res_unauth = client.post("/api/v1/demo/simulate-fraud")
    assert res_unauth.status_code == 401

    # 2. Analyst role cannot simulate demo (only Admin, Supervisor, Investigator)
    analyst_headers = _headers(Role.ANALYST)
    res_analyst_sim = client.post("/api/v1/demo/simulate-fraud", headers=analyst_headers)
    assert res_analyst_sim.status_code == 403

    # 3. Analyst cannot reset demo (only Admin or Supervisor)
    res_analyst_reset = client.post("/api/v1/demo/reset", headers=analyst_headers)
    assert res_analyst_reset.status_code == 403

    # 4. Investigator cannot reset demo (only Admin or Supervisor)
    inv_headers = _headers(Role.INVESTIGATOR)
    res_inv_reset = client.post("/api/v1/demo/reset", headers=inv_headers)
    assert res_inv_reset.status_code == 403

    # 5. Supervisor CAN reset demo
    sup_headers = _headers(Role.SUPERVISOR)
    res_sup_reset = client.post("/api/v1/demo/reset", headers=sup_headers)
    assert res_sup_reset.status_code == 200


# =====================================================================
# 5. FORENSIC AUDIT LOGGING
# =====================================================================

def test_demo_audit_logging(client):
    """Verify simulation events and reset actions generate immutable forensic audit log records."""
    admin_headers = _headers(Role.ADMIN, email="auditor_admin@cybercell.gov.in")

    # Run simulation
    sim_res = client.post("/api/v1/demo/simulate-fraud", headers=admin_headers)
    assert sim_res.status_code == 201
    sim_data = sim_res.json()
    scenario_id = sim_data["scenario_id"]

    # Run reset
    reset_res = client.post("/api/v1/demo/reset", headers=admin_headers)
    assert reset_res.status_code == 200

    # Inspect audit events in memory
    audit_logs_res = audit_service.list_logs(limit=50)
    audit_events = audit_logs_res["logs"]
    actions = [e["action"] for e in audit_events]

    assert AuditAction.DEMO_SIMULATION_STARTED.value in actions
    assert AuditAction.DEMO_SIMULATION_COMPLETED.value in actions
    assert AuditAction.DEMO_DATA_RESET.value in actions

    # Verify scenario ID in audit details
    matching_event = next(
        (e for e in audit_events if e["action"] == AuditAction.DEMO_SIMULATION_COMPLETED.value and e["resource_id"] == scenario_id),
        None,
    )
    assert matching_event is not None
    assert matching_event["actor_id"] == "auditor_admin@cybercell.gov.in"
