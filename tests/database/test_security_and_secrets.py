"""Tests verifying password hashing security, secret protection, and credential handling."""

import uuid
import pytest
from backend.app.core.security import get_password_hash, verify_password
from backend.app.models.user import User


def test_password_is_cryptographically_hashed_not_plaintext():
    """Verify passwords are never stored in plaintext and use salted bcrypt hashes."""
    raw_secret = "Investigate@2024!ComplexSecret"
    hashed = get_password_hash(raw_secret)

    # Hashed must never equal raw password
    assert hashed != raw_secret

    # Must start with standard bcrypt prefix ($2b$ or $2a$)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # Length of standard modular crypt format bcrypt hash is 60 chars
    assert len(hashed) == 60


def test_unique_salts_generated_for_identical_passwords():
    """Verify that hashing identical passwords generates different hashes due to CSPRNG salts."""
    pwd = "SecurePoliceOfficerPassword#99"
    hash1 = get_password_hash(pwd)
    hash2 = get_password_hash(pwd)

    assert hash1 != hash2
    assert verify_password(pwd, hash1) is True
    assert verify_password(pwd, hash2) is True


def test_verify_password_rejects_invalid_credentials():
    """Verify password verification correctly rejects incorrect attempts and tampering."""
    correct_pwd = "Investigate@2024!"
    wrong_pwd = "Investigate@2024?"

    hashed = get_password_hash(correct_pwd)
    assert verify_password(correct_pwd, hashed) is True
    assert verify_password(wrong_pwd, hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password("gibberish", "invalid_hash_string") is False


def test_user_model_instantiation_uses_hashed_password():
    """Verify User model instance stores hashed_password without leaking raw text."""
    raw_pwd = "SuperSecretAdminPassword#42"
    hashed = get_password_hash(raw_pwd)

    user = User(
        id=uuid.uuid4(),
        email="test_officer@cybercell.gov.in",
        hashed_password=hashed,
        full_name="Officer Test",
        department="Anti-Mule Cell",
    )

    assert user.hashed_password == hashed
    assert raw_pwd not in user.hashed_password
    assert verify_password(raw_pwd, user.hashed_password) is True
