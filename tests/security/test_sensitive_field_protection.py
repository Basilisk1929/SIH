"""Tests verifying sensitive field protection, masking, and automated log redaction."""

from fastapi.testclient import TestClient
from backend.app.core.sanitizer import (
    mask_account_number,
    mask_email,
    mask_phone,
    mask_sensitive_dict,
    mask_upi,
    sanitize_for_logging,
)
from backend.app.core.security import Role, create_access_token
from backend.app.main import app

client = TestClient(app)


def test_account_number_masking():
    """Verify bank account numbers have middle digits masked while preserving prefix/suffix."""
    assert mask_account_number("SYN1122334455") == "SYN******4455"
    assert mask_account_number("123456789012") == "1234****9012"
    assert mask_account_number("") == ""


def test_phone_number_masking():
    """Verify Indian mobile numbers have middle digits masked."""
    assert mask_phone("+919876543210") == "+91******3210"
    assert mask_phone("9876543210") == "98****3210"
    assert mask_phone("") == ""


def test_email_and_upi_masking():
    """Verify email and UPI handle username masking."""
    assert mask_email("investigator@cybercell.gov.in") == "i**********r@cybercell.gov.in"
    assert mask_upi("suspect99@synthaxis") == "s*******9@synthaxis"


def test_sanitize_for_logging_scrubs_secrets():
    """Verify log sanitizer scrubs passwords, bearer tokens, JWTs, and full account numbers."""
    raw_log = (
        'User login payload: password="SecretPlainPassword123!" '
        'Authorization: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.dummy" '
        'account=SYN1122334455 transfer initiated'
    )
    sanitized = sanitize_for_logging(raw_log)

    assert "SecretPlainPassword123!" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized
    assert "Bearer eyJhbGci" not in sanitized
    assert "SYN1122334455" not in sanitized
    assert "SYN11****4455" in sanitized


def test_mask_sensitive_dict_recursive():
    """Verify dictionary payloads with nested credentials have sensitive keys redacted."""
    payload = {
        "user": {"email": "agent@gov.in", "password": "PlainSecretPassword!"},
        "token": "eyJhbGciOi...",
        "account_number": "SYN1122334455",
        "nested": {"suspect_phone": "+919876543210", "safe_field": 42},
    }
    masked = mask_sensitive_dict(payload)

    assert masked["user"]["password"] == "[REDACTED]"
    assert masked["token"] == "[REDACTED]"
    assert masked["account_number"] == "SYN******4455"
    assert masked["nested"]["suspect_phone"] == "+91******3210"
    assert masked["nested"]["safe_field"] == 42


def test_role_sensitive_account_masking_in_api():
    """Verify ANALYST sees masked accounts while INVESTIGATOR sees full accounts."""
    tok_analyst = create_access_token(subject="analyst@cybercell.gov.in", role=Role.ANALYST)
    tok_inv = create_access_token(subject="investigator@cybercell.gov.in", role=Role.INVESTIGATOR)

    # 1. Analyst view -> account is masked
    res_analyst = client.get(
        "/api/v1/accounts/SYN1122334455",
        headers={"Authorization": f"Bearer {tok_analyst}"},
    )
    assert res_analyst.status_code == 200
    assert res_analyst.json()["account_number"] == "SYN******4455"

    # 2. Investigator view -> account is unmasked for lawful investigation
    res_inv = client.get(
        "/api/v1/accounts/SYN1122334455",
        headers={"Authorization": f"Bearer {tok_inv}"},
    )
    assert res_inv.status_code == 200
    assert res_inv.json()["account_number"] == "SYN1122334455"
