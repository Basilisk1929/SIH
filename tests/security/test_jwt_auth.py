"""Tests verifying JWT token lifecycle, bcrypt hashing, rotation, expiration, and revocation."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from backend.app.core.config import settings
from backend.app.core.security import (
    Role,
    clear_revoked_tokens,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_token,
    get_password_hash,
    revoke_token,
    validate_password_strength,
    verify_password,
)
from backend.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    clear_revoked_tokens()
    yield
    clear_revoked_tokens()


def test_password_hashing_and_strength_validation():
    """Verify bcrypt hashing with unique salts and complexity validation."""
    pwd = "Investigate@2024!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert hashed.startswith("$2b$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False

    # Unique salt per hash
    hashed2 = get_password_hash(pwd)
    assert hashed != hashed2
    assert verify_password(pwd, hashed2) is True

    # Weak password rejection
    with pytest.raises(ValueError, match="at least 8 characters"):
        validate_password_strength("short")
    with pytest.raises(ValueError, match="too common"):
        validate_password_strength("password")


def test_jwt_access_and_refresh_token_generation():
    """Verify JWT tokens carry required claims and enforce type."""
    access_tok = create_access_token(subject="officer@cybercell.gov.in", role=Role.INVESTIGATOR)
    claims = decode_access_token(access_tok)
    assert claims["sub"] == "officer@cybercell.gov.in"
    assert claims["role"] == "INVESTIGATOR"
    assert claims["type"] == "access"
    assert "exp" in claims
    assert "jti" in claims

    refresh_tok = create_refresh_token(subject="officer@cybercell.gov.in", role=Role.INVESTIGATOR)
    ref_claims = decode_token(refresh_tok, expected_type="refresh")
    assert ref_claims["sub"] == "officer@cybercell.gov.in"
    assert ref_claims["role"] == "INVESTIGATOR"
    assert ref_claims["type"] == "refresh"


def test_jwt_token_expiration_rejection():
    """Verify expired tokens are rejected with HTTP 401."""
    expired_tok = create_access_token(
        subject="officer@cybercell.gov.in",
        role=Role.ANALYST,
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(Exception) as excinfo:
        decode_access_token(expired_tok)
    assert "expired" in str(excinfo.value).lower()


def test_jwt_algorithm_none_and_tampered_secret_rejection():
    """Verify that unverified or 'none' algorithm tokens are unconditionally rejected."""
    # Fake token with none algorithm
    fake_header = {"alg": "none", "typ": "JWT"}
    fake_payload = {
        "sub": "admin@cybercell.gov.in",
        "role": "ADMIN",
        "type": "access",
        "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
    }
    none_token = f"{jwt.api_jws.base64url_encode(str(fake_header).encode()).decode()}.{jwt.api_jws.base64url_encode(str(fake_payload).encode()).decode()}."

    with pytest.raises(Exception):
        decode_access_token(none_token)

    # Token signed with forged secret
    forged_token = jwt.encode(fake_payload, "completely_wrong_attacker_secret_key", algorithm="HS256")
    with pytest.raises(Exception):
        decode_access_token(forged_token)


def test_jwt_token_revocation_upon_logout():
    """Verify that token revocation immediately blocks subsequent access."""
    tok = create_access_token(subject="officer@cybercell.gov.in", role=Role.INVESTIGATOR)
    assert decode_access_token(tok)["sub"] == "officer@cybercell.gov.in"

    # Revoke token
    revoke_token(tok)
    with pytest.raises(Exception) as excinfo:
        decode_access_token(tok)
    assert "revoked" in str(excinfo.value).lower()


def test_auth_login_json_and_refresh_flow():
    """Test full login, me, refresh, and logout flow via HTTP API."""
    # 1. Login with JSON credentials
    login_res = client.post(
        "/api/v1/auth/login-json",
        json={"email": "investigator@cybercell.gov.in", "password": "Investigate@2024!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # 2. Access /me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "investigator@cybercell.gov.in"
    assert me_data["role"] == "INVESTIGATOR"

    # 3. Refresh token
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    new_access_token = new_data["access_token"]

    # 4. Logout (revokes access_token)
    logout_res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_access_token}"})
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "SUCCESS"

    # 5. Subsequent access with revoked token is denied (401)
    denied_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert denied_res.status_code == 401
