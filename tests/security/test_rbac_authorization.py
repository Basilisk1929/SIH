"""Tests verifying Role-Based Access Control (RBAC) authorization matrix across all roles."""

from fastapi.testclient import TestClient
import pytest
from backend.app.core.security import Role, clear_revoked_tokens, create_access_token
from backend.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    clear_revoked_tokens()
    yield
    clear_revoked_tokens()


def _get_headers_for(role: Role) -> dict:
    tok = create_access_token(subject=f"test_{role.value.lower()}@cybercell.gov.in", role=role)
    return {"Authorization": f"Bearer {tok}"}


def test_unauthenticated_request_rejected():
    """Verify endpoints requiring authentication reject unauthenticated calls with HTTP 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_admin_user_management_rbac():
    """Verify POST /api/v1/auth/users is restricted strictly to ADMIN."""
    payload = {
        "email": "new_operative@cybercell.gov.in",
        "password": "SecurePassword#999!",
        "full_name": "Agent S. Verma",
        "role": "ANALYST",
    }

    # 1. ANALYST -> 403 Forbidden
    res_analyst = client.post("/api/v1/auth/users", json=payload, headers=_get_headers_for(Role.ANALYST))
    assert res_analyst.status_code == 403

    # 2. INVESTIGATOR -> 403 Forbidden
    res_inv = client.post("/api/v1/auth/users", json=payload, headers=_get_headers_for(Role.INVESTIGATOR))
    assert res_inv.status_code == 403

    # 3. SUPERVISOR -> 403 Forbidden
    res_sup = client.post("/api/v1/auth/users", json=payload, headers=_get_headers_for(Role.SUPERVISOR))
    assert res_sup.status_code == 403

    # 4. ADMIN -> 200 OK
    res_admin = client.post("/api/v1/auth/users", json=payload, headers=_get_headers_for(Role.ADMIN))
    assert res_admin.status_code == 200
    assert res_admin.json()["email"] == "new_operative@cybercell.gov.in"


def test_audit_log_query_rbac():
    """Verify GET /api/v1/audit/logs is accessible by ADMIN and SUPERVISOR, but denied to others."""
    # 1. ANALYST -> 403
    res_analyst = client.get("/api/v1/audit/logs", headers=_get_headers_for(Role.ANALYST))
    assert res_analyst.status_code == 403

    # 2. INVESTIGATOR -> 403
    res_inv = client.get("/api/v1/audit/logs", headers=_get_headers_for(Role.INVESTIGATOR))
    assert res_inv.status_code == 403

    # 3. SUPERVISOR -> 200 OK
    res_sup = client.get("/api/v1/audit/logs", headers=_get_headers_for(Role.SUPERVISOR))
    assert res_sup.status_code == 200
    assert "logs" in res_sup.json()

    # 4. ADMIN -> 200 OK
    res_admin = client.get("/api/v1/audit/logs", headers=_get_headers_for(Role.ADMIN))
    assert res_admin.status_code == 200
    assert "logs" in res_admin.json()


def test_case_creation_and_update_rbac():
    """Verify case docket management permissions."""
    case_payload = {
        "title": "Operation Swift Recovery",
        "description": "Cross-border mule account ring",
        "priority": "HIGH",
        "total_fraud_amount_inr": 250000.0,
    }

    # 1. ANALYST cannot create cases -> 403
    res_analyst = client.post("/api/v1/cases", json=case_payload, headers=_get_headers_for(Role.ANALYST))
    assert res_analyst.status_code == 403

    # 2. INVESTIGATOR can create case -> 201
    res_inv = client.post("/api/v1/cases", json=case_payload, headers=_get_headers_for(Role.INVESTIGATOR))
    assert res_inv.status_code == 201
    created_case = res_inv.json()
    case_num = created_case["case_number"]

    # 3. ANALYST cannot update cases -> 403
    patch_payload = {"status": "UNDER_REVIEW", "investigation_notes": "Review initiated"}
    res_patch_analyst = client.patch(
        f"/api/v1/cases/{case_num}",
        json=patch_payload,
        headers=_get_headers_for(Role.ANALYST),
    )
    assert res_patch_analyst.status_code == 403

    # 4. SUPERVISOR can update cases -> 200
    res_patch_sup = client.patch(
        f"/api/v1/cases/{case_num}",
        json=patch_payload,
        headers=_get_headers_for(Role.SUPERVISOR),
    )
    assert res_patch_sup.status_code == 200
    assert res_patch_sup.json()["status"] == "UNDER_REVIEW"
