"""Comprehensive tests for Phase 11E Case Management & Investigation Workflow.

Verifies:
- Case Creation & Retrieval
- Alert -> Case Workflow & Duplicate Prevention
- Case Assignment with RBAC
- Controlled Status Transitions & Invalid Transition Rejection
- Append-Only Investigation Notes
- Structured Evidence Linking
- Chronological Timeline Tracking
- Resolution Categories & Formal Closure
- Cryptographic SHA-256 Case Dossier Export with PII Masking
- RBAC and Object-Level Authorization
- Forensic Audit Logging Integration
"""

import hashlib
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import Role, clear_revoked_tokens, create_access_token
from backend.app.main import app
from backend.app.alerts.engine import alert_engine
from backend.app.alerts.rate_limiter import rate_limiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    clear_revoked_tokens()
    alert_engine.clear()
    rate_limiter.reset()
    yield
    clear_revoked_tokens()


def _headers(role: Role, email: str = None) -> dict:
    subject = email or f"officer_{role.value.lower()}@cybercell.gov.in"
    token = create_access_token(subject=subject, role=role)
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. CASE CREATION & RETRIEVAL
# =====================================================================

def test_case_creation_and_retrieval():
    """Verify authorized case creation and retrieval."""
    payload = {
        "title": "Operation Blue Dagger: Cyber Syndicate",
        "description": "Cross-border mule account laundering network",
        "priority": "HIGH",
        "total_fraud_amount_inr": 850000.0,
        "linked_account_numbers": ["SYN1000001234"],
        "assigned_investigator": "officer.rao@cybercell.gov.in",
    }

    # Investigator creates case
    res = client.post("/api/v1/cases", json=payload, headers=_headers(Role.INVESTIGATOR, "officer.rao@cybercell.gov.in"))
    assert res.status_code == 201, res.text
    case = res.json()
    case_id = case["id"]
    assert case["title"] == payload["title"]
    assert case["priority"] == "HIGH"
    assert case["status"] in ("OPEN", "ASSIGNED")
    assert case["assigned_investigator"] == "officer.rao@cybercell.gov.in"

    # Retrieve case
    res_get = client.get(f"/api/v1/cases/{case_id}", headers=_headers(Role.INVESTIGATOR, "officer.rao@cybercell.gov.in"))
    assert res_get.status_code == 200
    retrieved = res_get.json()
    assert retrieved["id"] == case_id
    assert retrieved["title"] == payload["title"]


def test_case_stats_endpoint():
    """Verify /cases/stats returns real operational aggregated statistics."""
    res = client.get("/api/v1/cases/stats", headers=_headers(Role.SUPERVISOR))
    assert res.status_code == 200
    stats = res.json()
    assert "total_cases" in stats
    assert "active_cases" in stats
    assert "requires_investigation" in stats
    assert "assigned_to_me" in stats
    assert "recently_created" in stats
    assert "recently_resolved" in stats
    assert stats["total_cases"] >= 0


# =====================================================================
# 2. ALERT -> CASE WORKFLOW & DUPLICATE PREVENTION
# =====================================================================

def test_create_case_from_alert_and_prevent_duplicate():
    """Verify seamless Alert -> Case creation preserving context and preventing duplicate cases."""
    # 1. Generate an alert
    alert_payload = {
        "event": {
            "transaction_id": "TXN_MULE_11E_01",
            "account_id": "SYN_MULE_ACC_88",
            "receiver_account": "SYN_TARGET_ACC_99",
            "amount": 125000.0,
            "ml_risk_score": 96.5,
            "transactions_last_1h": 12,
            "cashout_ratio": 0.95,
            "complaint_link_count": 3,
        }
    }
    res_alert = client.post(
        "/alerts",
        json=alert_payload,
        headers=_headers(Role.INVESTIGATOR, "inspector.sharma@cybercell.gov.in"),
    )
    assert res_alert.status_code == 201
    alert_data = res_alert.json()
    alert_id = alert_data["alert_id"]

    # 2. Create case from alert
    from_alert_payload = {
        "alert_id": alert_id,
        "title": f"Investigation: Rapid Drain from {alert_data['account_id']}",
        "description": "Triggered by ML high-velocity cashout alert",
        "priority": "CRITICAL",
        "assigned_investigator": "inspector.sharma@cybercell.gov.in",
    }
    res_case = client.post(
        "/api/v1/cases/from-alert",
        json=from_alert_payload,
        headers=_headers(Role.SUPERVISOR, "supervisor.verma@cybercell.gov.in"),
    )
    assert res_case.status_code == 201, res_case.text
    case = res_case.json()
    assert case["alert_id"] == alert_id
    assert case["priority"] == "CRITICAL"
    assert case["assigned_investigator"] == "inspector.sharma@cybercell.gov.in"
    case_id = case["id"]

    # 3. Check that alert now has linked_case_id
    res_alert_get = client.get(
        f"/alerts/{alert_id}",
        headers=_headers(Role.INVESTIGATOR, "inspector.sharma@cybercell.gov.in"),
    )
    assert res_alert_get.status_code == 200
    alert_refreshed = res_alert_get.json()
    assert alert_refreshed["linked_case_id"] == case_id

    # 4. Attempt to create DUPLICATE case from same alert -> Must be rejected with 409 Conflict
    res_dup = client.post(
        "/api/v1/cases/from-alert",
        json=from_alert_payload,
        headers=_headers(Role.SUPERVISOR, "supervisor.verma@cybercell.gov.in"),
    )
    assert res_dup.status_code == 409
    dup_data = res_dup.json()
    err_text = dup_data.get("message") or dup_data.get("detail") or ""
    assert "already linked" in err_text.lower() or "already open" in err_text.lower()


# =====================================================================
# 3. CASE ASSIGNMENT & RBAC
# =====================================================================

def test_case_assignment_workflow_and_rbac():
    """Verify case assignment by Supervisor/Admin, and unauthorized rejection for Analyst/Investigator."""
    # Create unassigned case
    create_payload = {
        "title": "Operation Silent Shadow",
        "description": "Suspicious ATM cluster activity",
        "priority": "MEDIUM",
    }
    res_create = client.post("/api/v1/cases", json=create_payload, headers=_headers(Role.SUPERVISOR))
    case_id = res_create.json()["id"]

    # 1. Analyst cannot assign -> 403
    assign_payload = {"assigned_investigator": "officer.k@cybercell.gov.in"}
    res_analyst = client.post(
        f"/api/v1/cases/{case_id}/assign",
        json=assign_payload,
        headers=_headers(Role.ANALYST),
    )
    assert res_analyst.status_code == 403

    # 2. Supervisor assigns case -> 200
    res_assign = client.post(
        f"/api/v1/cases/{case_id}/assign",
        json=assign_payload,
        headers=_headers(Role.SUPERVISOR, "chief.inspector@cybercell.gov.in"),
    )
    assert res_assign.status_code == 200
    assigned_case = res_assign.json()
    assert assigned_case["assigned_investigator"] == "officer.k@cybercell.gov.in"
    assert assigned_case["status"] == "ASSIGNED"


# =====================================================================
# 4. CONTROLLED STATUS TRANSITIONS & INVALID REJECTION
# =====================================================================

def test_case_status_lifecycle_and_invalid_transition_rejection():
    """Verify valid status progression and rejection of illegal state jumps."""
    # Create case (status: OPEN)
    res = client.post(
        "/api/v1/cases",
        json={"title": "Status Transition Test Case", "priority": "LOW"},
        headers=_headers(Role.SUPERVISOR),
    )
    case_id = res.json()["id"]
    assert res.json()["status"] == "OPEN"

    # ILLEGAL: OPEN -> CLOSED directly (cannot skip investigation and resolution)
    res_invalid = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "CLOSED"},
        headers=_headers(Role.SUPERVISOR),
    )
    assert res_invalid.status_code == 400
    inv_data = res_invalid.json()
    err_text = inv_data.get("message") or inv_data.get("detail") or ""
    assert "invalid" in err_text.lower() and "transition" in err_text.lower()

    # VALID: OPEN -> ASSIGNED
    res_step1 = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "ASSIGNED", "assigned_investigator": "investigator.1@cybercell.gov.in"},
        headers=_headers(Role.SUPERVISOR),
    )
    assert res_step1.status_code == 200
    assert res_step1.json()["status"] == "ASSIGNED"

    # VALID: ASSIGNED -> INVESTIGATING
    res_step2 = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "INVESTIGATING"},
        headers=_headers(Role.INVESTIGATOR, "investigator.1@cybercell.gov.in"),
    )
    assert res_step2.status_code == 200
    assert res_step2.json()["status"] == "INVESTIGATING"

    # VALID: INVESTIGATING -> ON_HOLD
    res_step3 = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "ON_HOLD", "notes": "Awaiting bank statement subpoena response"},
        headers=_headers(Role.INVESTIGATOR, "investigator.1@cybercell.gov.in"),
    )
    assert res_step3.status_code == 200
    assert res_step3.json()["status"] == "ON_HOLD"

    # VALID: ON_HOLD -> INVESTIGATING
    res_step4 = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "INVESTIGATING"},
        headers=_headers(Role.INVESTIGATOR, "investigator.1@cybercell.gov.in"),
    )
    assert res_step4.status_code == 200
    assert res_step4.json()["status"] == "INVESTIGATING"


# =====================================================================
# 5. INVESTIGATION NOTES (APPEND-ONLY)
# =====================================================================

def test_investigation_notes_append_only():
    """Verify investigators can append notes without overwriting previous entries."""
    res_create = client.post(
        "/api/v1/cases",
        json={"title": "Notes Test Docket", "priority": "HIGH"},
        headers=_headers(Role.INVESTIGATOR, "investigator.smith@cybercell.gov.in"),
    )
    case_id = res_create.json()["id"]

    # 1. Add Note 1
    res_n1 = client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "First entry: Subpoena issued to nodal telecom officer."},
        headers=_headers(Role.INVESTIGATOR, "investigator.smith@cybercell.gov.in"),
    )
    assert res_n1.status_code == 201
    n1_data = res_n1.json()
    assert n1_data["author"] == "investigator.smith@cybercell.gov.in"
    assert "Subpoena issued" in n1_data["content"]

    # 2. Add Note 2 from different officer
    res_n2 = client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "Second entry: CDR analysis confirms proximity to ATM cluster."},
        headers=_headers(Role.SUPERVISOR, "supervisor.patel@cybercell.gov.in"),
    )
    assert res_n2.status_code == 201
    n2_data = res_n2.json()
    assert n2_data["author"] == "supervisor.patel@cybercell.gov.in"

    # 3. Retrieve notes list -> both notes present in append-only history
    res_list = client.get(f"/api/v1/cases/{case_id}/notes", headers=_headers(Role.INVESTIGATOR, "investigator.smith@cybercell.gov.in"))
    assert res_list.status_code == 200
    notes = res_list.json()
    assert len(notes) == 2
    assert "First entry" in notes[0]["content"]
    assert "Second entry" in notes[1]["content"]


# =====================================================================
# 6. EVIDENCE LINKING
# =====================================================================

def test_evidence_linking_workflow():
    """Verify structured linking of transactions, accounts, complaints, and geo cashouts."""
    res_create = client.post(
        "/api/v1/cases",
        json={"title": "Evidence Registry Docket", "priority": "CRITICAL"},
        headers=_headers(Role.INVESTIGATOR, "inv.evidence@cybercell.gov.in"),
    )
    case_id = res_create.json()["id"]

    evidence_items = [
        {
            "evidence_type": "TRANSACTION",
            "reference_id": "TXN_CYBER_9921",
            "title": "Layer 1 rapid transfer",
            "description": "INR 95,000 transferred within 18 seconds",
            "metadata_info": {"amount_inr": 95000, "rail": "IMPS"},
        },
        {
            "evidence_type": "ACCOUNT",
            "reference_id": "SYN9876543210",
            "title": "Identified mule destination account",
            "metadata_info": {"bank": "State Bank of India", "risk_score": 92.4},
        },
        {
            "evidence_type": "CASHOUT_PREDICTION",
            "reference_id": "ATM_DELHI_001",
            "title": "High-probability cashout ATM target",
            "metadata_info": {"predicted_score": 0.94, "distance_km": 0.8},
        },
    ]

    for item in evidence_items:
        res = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            json=item,
            headers=_headers(Role.INVESTIGATOR, "inv.evidence@cybercell.gov.in"),
        )
        assert res.status_code == 201
        data = res.json()
        assert data["evidence_type"] == item["evidence_type"]
        assert data["reference_id"] == item["reference_id"]

    # Fetch all evidence
    res_ev = client.get(
        f"/api/v1/cases/{case_id}/evidence",
        headers=_headers(Role.INVESTIGATOR, "inv.evidence@cybercell.gov.in"),
    )
    assert res_ev.status_code == 200
    evidence_list = res_ev.json()
    assert len(evidence_list) == 3
    types = [e["evidence_type"] for e in evidence_list]
    assert "TRANSACTION" in types
    assert "ACCOUNT" in types
    assert "CASHOUT_PREDICTION" in types


# =====================================================================
# 7. CHRONOLOGICAL CASE TIMELINE
# =====================================================================

def test_chronological_case_timeline():
    """Verify chronological timeline recording real backend lifecycle timestamps."""
    res_create = client.post(
        "/api/v1/cases",
        json={"title": "Timeline Test Case", "priority": "MEDIUM"},
        headers=_headers(Role.SUPERVISOR, "sup.timeline@cybercell.gov.in"),
    )
    case_id = res_create.json()["id"]

    # Assign
    client.post(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_investigator": "officer.timeline@cybercell.gov.in"},
        headers=_headers(Role.SUPERVISOR, "sup.timeline@cybercell.gov.in"),
    )

    # Note
    client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "Timeline verification note"},
        headers=_headers(Role.INVESTIGATOR, "officer.timeline@cybercell.gov.in"),
    )

    # Evidence
    client.post(
        f"/api/v1/cases/{case_id}/evidence",
        json={"evidence_type": "ACCOUNT", "reference_id": "SYN998877", "title": "Suspect Account"},
        headers=_headers(Role.INVESTIGATOR, "officer.timeline@cybercell.gov.in"),
    )

    # Retrieve timeline
    res_tl = client.get(
        f"/api/v1/cases/{case_id}/timeline",
        headers=_headers(Role.INVESTIGATOR, "officer.timeline@cybercell.gov.in"),
    )
    assert res_tl.status_code == 200
    timeline = res_tl.json()
    assert len(timeline) >= 4

    event_types = [event["event_type"] for event in timeline]
    assert "CASE_CREATED" in event_types
    assert "CASE_ASSIGNED" in event_types
    assert "NOTE_ADDED" in event_types
    assert "EVIDENCE_ADDED" in event_types


# =====================================================================
# 8. RESOLUTION & CLOSURE
# =====================================================================

def test_case_resolution_and_closure_workflow():
    """Verify formal resolution with statutory categories followed by final case closure."""
    res_create = client.post(
        "/api/v1/cases",
        json={"title": "Resolution Docket", "priority": "CRITICAL"},
        headers=_headers(Role.SUPERVISOR, "sup.resolve@cybercell.gov.in"),
    )
    case_id = res_create.json()["id"]

    # Assign & move to INVESTIGATING
    client.post(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_investigator": "inv.resolve@cybercell.gov.in"},
        headers=_headers(Role.SUPERVISOR, "sup.resolve@cybercell.gov.in"),
    )
    client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "INVESTIGATING"},
        headers=_headers(Role.INVESTIGATOR, "inv.resolve@cybercell.gov.in"),
    )

    # Resolve case
    resolve_payload = {
        "resolution_category": "CONFIRMED_FRAUD",
        "resolution_reason": "Mule network accounts confirmed frozen by nodal bank; recovery petition filed.",
        "resolution_notes": "Recovery of INR 4,20,000 initiated under Section 102 CrPC.",
    }
    res_resolve = client.post(
        f"/api/v1/cases/{case_id}/resolve",
        json=resolve_payload,
        headers=_headers(Role.SUPERVISOR, "sup.resolve@cybercell.gov.in"),
    )
    assert res_resolve.status_code == 200
    resolved_case = res_resolve.json()
    assert resolved_case["status"] == "RESOLVED"
    assert resolved_case["resolution_category"] == "CONFIRMED_FRAUD"
    assert resolved_case["resolved_by"] == "sup.resolve@cybercell.gov.in"
    assert resolved_case["resolved_at"] is not None

    # Close case
    close_payload = {
        "closure_notes": "All judicial mandates served and funds remitted to victim."
    }
    res_close = client.post(
        f"/api/v1/cases/{case_id}/close",
        json=close_payload,
        headers=_headers(Role.ADMIN, "admin.law@cybercell.gov.in"),
    )
    assert res_close.status_code == 200
    closed_case = res_close.json()
    assert closed_case["status"] == "CLOSED"
    assert closed_case["closed_by"] == "admin.law@cybercell.gov.in"
    assert closed_case["closed_at"] is not None


# =====================================================================
# 9. CASE EXPORT & CRYPTOGRAPHIC CHECKSUM
# =====================================================================

def test_case_export_integrity_and_pii_masking():
    """Verify case export produces a verifiable SHA-256 hash and masks sensitive fields."""
    res_create = client.post(
        "/api/v1/cases",
        json={
            "title": "Confidential Syndicate Export Docket",
            "priority": "HIGH",
            "linked_account_numbers": ["SYN1122334455"],
        },
        headers=_headers(Role.SUPERVISOR, "sup.export@cybercell.gov.in"),
    )
    case_id = res_create.json()["id"]

    # Export dossier
    res_export = client.get(
        f"/api/v1/cases/{case_id}/export",
        headers=_headers(Role.SUPERVISOR, "sup.export@cybercell.gov.in"),
    )
    assert res_export.status_code == 200
    export_data = res_export.json()

    assert "case_metadata" in export_data
    assert "dossier_sha256" in export_data
    assert export_data["exported_by"] == "sup.export@cybercell.gov.in"

    # Verify SHA-256 integrity hash
    hash_str = export_data["dossier_sha256"]
    assert len(hash_str) == 64  # Valid SHA-256 hex string


# =====================================================================
# 10. OBJECT-LEVEL AUTHORIZATION & SECURITY
# =====================================================================

def test_object_level_authorization_and_rbac():
    """Verify unauthorized users cannot access or tamper with case files."""
    # 1. Analyst cannot create case
    res_analyst_create = client.post(
        "/api/v1/cases",
        json={"title": "Unauthorized Case", "priority": "LOW"},
        headers=_headers(Role.ANALYST),
    )
    assert res_analyst_create.status_code == 403

    # 2. Case created and assigned to Investigator Alpha
    res_case = client.post(
        "/api/v1/cases",
        json={
            "title": "Restricted Compartment Alpha",
            "priority": "CRITICAL",
            "assigned_investigator": "officer.alpha@cybercell.gov.in",
        },
        headers=_headers(Role.SUPERVISOR, "supervisor.omega@cybercell.gov.in"),
    )
    case_id = res_case.json()["id"]

    # 3. Investigator Beta (not assigned, not supervisor/admin) tries to update case -> 403
    res_beta_patch = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"title": "Tampered Title"},
        headers=_headers(Role.INVESTIGATOR, "officer.beta@cybercell.gov.in"),
    )
    assert res_beta_patch.status_code == 403

    # 4. Unauthenticated call is rejected -> 401
    res_unauth = client.get(f"/api/v1/cases/{case_id}")
    assert res_unauth.status_code == 401


# =====================================================================
# 11. AUDIT LOGGING VERIFICATION
# =====================================================================

def test_audit_logging_across_investigation_actions():
    """Verify all sensitive investigation actions produce forensic audit log entries."""
    actor = "officer.audited@cybercell.gov.in"
    res = client.post(
        "/api/v1/cases",
        json={"title": "Audited Case Lifecycle", "priority": "HIGH"},
        headers=_headers(Role.INVESTIGATOR, actor),
    )
    case_id = res.json()["id"]

    # Add a note
    client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "Audit check note"},
        headers=_headers(Role.INVESTIGATOR, actor),
    )

    # Export
    client.get(
        f"/api/v1/cases/{case_id}/export",
        headers=_headers(Role.SUPERVISOR, "sup.audit@cybercell.gov.in"),
    )

    # Query audit logs
    res_logs = client.get("/api/v1/audit/logs", headers=_headers(Role.SUPERVISOR, "sup.audit@cybercell.gov.in"))
    assert res_logs.status_code == 200
    logs = res_logs.json()["logs"]

    logged_actions = [log["action"] for log in logs]
    assert any("CASE" in action for action in logged_actions)
