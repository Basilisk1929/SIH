"""Tests verifying that all 8 mandatory audit actions are logged without sensitive data leakage."""

from fastapi.testclient import TestClient
import pytest
from backend.app.core.security import Role, clear_revoked_tokens, create_access_token
from backend.app.main import app
from backend.app.services.audit_service import AuditAction, audit_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_audit():
    audit_service.clear()
    clear_revoked_tokens()
    yield
    audit_service.clear()
    clear_revoked_tokens()


def _get_headers_for(role: Role) -> dict:
    tok = create_access_token(subject=f"test_{role.value.lower()}@cybercell.gov.in", role=role)
    return {"Authorization": f"Bearer {tok}"}


def test_all_eight_mandatory_audit_actions_captured():
    """Verify that all 8 mandatory regulatory actions generate audit trail records:

    LOGIN, LOGOUT, VIEW_ALERT, VIEW_ACCOUNT, CREATE_CASE, UPDATE_CASE, EXPORT_DATA, ADMIN_ACTION.
    """
    # 1. LOGIN
    login_res = client.post(
        "/api/v1/auth/login-json",
        json={"email": "investigator@cybercell.gov.in", "password": "Investigate@2024!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    inv_headers = {"Authorization": f"Bearer {token}"}

    # 2. LOGOUT
    logout_res = client.post("/api/v1/auth/logout", headers=inv_headers)
    assert logout_res.status_code == 200

    # Fresh token for subsequent actions
    active_inv_headers = _get_headers_for(Role.INVESTIGATOR)

    # 3. VIEW_ALERT
    # First create an alert to view
    alert_payload = {
        "event": {
            "transaction_id": "TX_AUDIT_101",
            "account_id": "SYN1122334455",
            "amount": 75000.0,
            "ml_risk_score": 85.0,
        }
    }
    create_alert_res = client.post("/alerts", json=alert_payload, headers=active_inv_headers)
    assert create_alert_res.status_code == 201
    alert_id = create_alert_res.json()["alert_id"]

    view_alert_res = client.get(f"/alerts/{alert_id}", headers=active_inv_headers)
    assert view_alert_res.status_code == 200

    # 4. VIEW_ACCOUNT
    view_acct_res = client.get("/api/v1/accounts/SYN1122334455", headers=active_inv_headers)
    assert view_acct_res.status_code == 200

    # 5. CREATE_CASE
    case_payload = {
        "title": "Operation Audit Trail Test",
        "description": "Cross-jurisdiction fraud probe",
        "priority": "HIGH",
        "total_fraud_amount_inr": 150000.0,
    }
    create_case_res = client.post("/api/v1/cases", json=case_payload, headers=active_inv_headers)
    assert create_case_res.status_code == 201
    case_num = create_case_res.json()["case_number"]

    # 6. UPDATE_CASE
    update_case_res = client.patch(
        f"/api/v1/cases/{case_num}",
        json={"status": "UNDER_REVIEW", "investigation_notes": "Forensic evidence gathered"},
        headers=active_inv_headers,
    )
    assert update_case_res.status_code == 200

    # 7. EXPORT_DATA
    export_res = client.get(f"/api/v1/cases/{case_num}/export", headers=active_inv_headers)
    assert export_res.status_code == 200

    # 8. ADMIN_ACTION
    admin_headers = _get_headers_for(Role.ADMIN)
    user_payload = {
        "email": "audit_analyst@cybercell.gov.in",
        "password": "PasswordSecure@2024!",
        "full_name": "Analyst Audit",
        "role": "ANALYST",
    }
    create_user_res = client.post("/api/v1/auth/users", json=user_payload, headers=admin_headers)
    assert create_user_res.status_code == 200

    # Query audit logs as SUPERVISOR
    sup_headers = _get_headers_for(Role.SUPERVISOR)
    audit_res = client.get("/api/v1/audit/logs", headers=sup_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()["logs"]

    # Extract all recorded action types
    recorded_actions = {entry["action"] for entry in logs}

    required_actions = {
        "LOGIN",
        "LOGOUT",
        "VIEW_ALERT",
        "VIEW_ACCOUNT",
        "CREATE_CASE",
        "UPDATE_CASE",
        "EXPORT_DATA",
        "ADMIN_ACTION",
    }

    for action in required_actions:
        assert action in recorded_actions, f"Missing required audit action: {action}"


def test_audit_logs_never_contain_passwords_or_tokens():
    """Verify that passwords, JWT tokens, and sensitive keys are scrubbed from audit logs."""
    # Attempt login with secret password
    secret_pwd = "MySuperSecretPlainPassword123!"
    client.post(
        "/api/v1/auth/login-json",
        json={"email": "investigator@cybercell.gov.in", "password": secret_pwd},
    )

    sup_headers = _get_headers_for(Role.SUPERVISOR)
    audit_res = client.get("/api/v1/audit/logs", headers=sup_headers)
    assert audit_res.status_code == 200

    import json
    logs_text = json.dumps(audit_res.json())

    # Raw password must never appear
    assert secret_pwd not in logs_text
    # Bearer tokens or JWTs must not appear in details
    assert "Bearer " not in logs_text
