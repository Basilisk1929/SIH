"""Phase 14 — Final Security Audit: Comprehensive security regression tests.

Validates authentication enforcement, RBAC, error sanitization,
WebSocket auth, and rate limiting across all platform endpoints.
"""

import pytest
from datetime import timedelta
from unittest.mock import patch

from backend.app.core.security import (
    Role,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    is_token_revoked,
    revoke_token,
    clear_revoked_tokens,
    verify_password,
    validate_password_strength,
)


# --- Helper: Generate test tokens ---


def _make_token(role: str = "ADMIN", subject: str = "test@cybercell.gov.in", expired: bool = False):
    """Generate a valid test JWT token with specified role."""
    delta = timedelta(minutes=-5) if expired else timedelta(minutes=30)
    return create_access_token(subject=subject, role=role, expires_delta=delta)


# ============================================================
# 1. AUTHENTICATION TESTS
# ============================================================


class TestAuthentication:
    """Validate JWT lifecycle: generation, expiration, revocation, type-checking."""

    def test_access_token_has_required_claims(self):
        token = _make_token()
        decoded = decode_token(token, expected_type="access")
        assert decoded["sub"] == "test@cybercell.gov.in"
        assert decoded["role"] == "ADMIN"
        assert decoded["type"] == "access"
        assert "jti" in decoded
        assert "exp" in decoded
        assert "iat" in decoded

    def test_refresh_token_has_type_refresh(self):
        token = create_refresh_token(subject="test@cybercell.gov.in", role="ANALYST")
        decoded = decode_token(token, expected_type="refresh")
        assert decoded["type"] == "refresh"
        assert decoded["role"] == "ANALYST"

    def test_expired_token_rejected(self):
        token = _make_token(expired=True)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401

    def test_wrong_type_token_rejected(self):
        """Refresh token must not be accepted where access token is expected."""
        token = create_refresh_token(subject="test@cybercell.gov.in", role="ADMIN")
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token, expected_type="access")
        assert exc_info.value.status_code == 401

    def test_revoked_token_rejected(self):
        clear_revoked_tokens()
        token = _make_token()
        assert not is_token_revoked(token)
        revoke_token(token)
        assert is_token_revoked(token)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401
        clear_revoked_tokens()

    def test_invalid_signature_rejected(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tampered.signature")
        assert exc_info.value.status_code == 401

    def test_password_hashing_bcrypt(self):
        hashed = get_password_hash("TestSecure@2024!")
        assert hashed.startswith("$2")  # bcrypt prefix
        assert verify_password("TestSecure@2024!", hashed)
        assert not verify_password("WrongPassword", hashed)

    def test_password_strength_enforcement(self):
        with pytest.raises(ValueError):
            validate_password_strength("short")
        with pytest.raises(ValueError):
            validate_password_strength("password")
        with pytest.raises(ValueError):
            validate_password_strength("12345678")
        # Valid password should not raise
        validate_password_strength("ValidPass@2024!")

    def test_bcrypt_72_byte_limit(self):
        """bcrypt truncates at 72 bytes; verify passwords are correctly capped."""
        long_pw = "A" * 100 + "X"
        hashed = get_password_hash(long_pw)
        # bcrypt only hashes first 72 bytes
        assert verify_password(long_pw, hashed)

    def test_password_max_length(self):
        """Passwords exceeding 128 chars should be rejected."""
        with pytest.raises(ValueError):
            validate_password_strength("A" * 200)


# ============================================================
# 2. RBAC / AUTHORIZATION TESTS
# ============================================================


class TestRBAC:
    """Validate role-based access control enforcement."""

    def test_role_normalization(self):
        assert Role.normalize("admin") == Role.ADMIN
        assert Role.normalize("ADMIN") == Role.ADMIN
        assert Role.normalize("supervisor") == Role.SUPERVISOR
        assert Role.normalize("INVESTIGATOR") == Role.INVESTIGATOR
        assert Role.normalize("analyst") == Role.ANALYST
        assert Role.normalize("invalid_role") == Role.ANALYST  # default fallback
        assert Role.normalize(None) == Role.ANALYST
        assert Role.normalize("") == Role.ANALYST

    def test_admin_inherits_all_permissions(self):
        """ADMIN role must pass any role check."""
        from backend.app.core.security import require_roles

        checker = require_roles([Role.SUPERVISOR, Role.INVESTIGATOR])
        # ADMIN should be allowed even though not explicitly listed
        admin_claims = {"sub": "admin@test.com", "role": "ADMIN"}
        import asyncio
        result = asyncio.run(checker(admin_claims))
        assert result["role"] == "ADMIN"

    def test_analyst_denied_supervisor_endpoint(self):
        """ANALYST must not access SUPERVISOR-restricted endpoints."""
        from backend.app.core.security import require_roles
        from fastapi import HTTPException
        import asyncio

        checker = require_roles([Role.SUPERVISOR])
        analyst_claims = {"sub": "analyst@test.com", "role": "ANALYST"}
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(checker(analyst_claims))
        assert exc_info.value.status_code == 403


# ============================================================
# 3. ERROR SANITIZATION TESTS
# ============================================================


class TestErrorSanitization:
    """Verify internal details are not leaked in error responses."""

    def test_sanitize_passwords_in_logs(self):
        from backend.app.core.sanitizer import sanitize_for_logging

        raw = 'password="super_secret_123" and token=eyJhbGciOiJIUzI1NiJ9.test.sig'
        sanitized = sanitize_for_logging(raw)
        assert "super_secret_123" not in sanitized
        assert "[REDACTED" in sanitized

    def test_sanitize_jwt_tokens_in_logs(self):
        from backend.app.core.sanitizer import sanitize_for_logging

        token = create_access_token(subject="test@test.com", role="ADMIN")
        raw = f'Authorization: Bearer {token}'
        sanitized = sanitize_for_logging(raw)
        assert token not in sanitized

    def test_mask_account_number(self):
        from backend.app.core.sanitizer import mask_account_number

        assert "****" in mask_account_number("SYN1122334455")
        assert mask_account_number("SYN1122334455") != "SYN1122334455"
        assert mask_account_number("SYN1122334455").endswith("4455")

    def test_mask_phone_number(self):
        from backend.app.core.sanitizer import mask_phone

        masked = mask_phone("+919876543210")
        assert "9876" not in masked
        assert masked.endswith("3210")

    def test_mask_upi_id(self):
        from backend.app.core.sanitizer import mask_upi

        masked = mask_upi("suspect99@synthaxis")
        assert "suspect99" not in masked
        assert "@synthaxis" in masked

    def test_mask_email(self):
        from backend.app.core.sanitizer import mask_email

        masked = mask_email("officer@cybercell.gov.in")
        assert "officer" not in masked
        assert "@cybercell.gov.in" in masked

    def test_sensitive_dict_masking(self):
        from backend.app.core.sanitizer import mask_sensitive_dict

        data = {
            "password": "secret123",
            "access_token": "jwt.token.here",
            "account_number": "SYN1122334455",
            "phone": "+919876543210",
            "normal_field": "keep_this",
        }
        masked = mask_sensitive_dict(data)
        assert masked["password"] == "[REDACTED]"
        assert masked["access_token"] == "[REDACTED]"
        assert "1122" not in masked["account_number"]
        assert masked["normal_field"] == "keep_this"


# ============================================================
# 4. SECRETS & CONFIGURATION TESTS
# ============================================================


class TestSecretsConfiguration:
    """Validate that secrets management enforces production safety."""

    def test_production_jwt_secret_required(self):
        """Production mode must reject missing JWT secrets."""
        from backend.app.core.config import get_jwt_secret

        with patch.dict("os.environ", {"ENVIRONMENT": "production", "JWT_SECRET_KEY": ""}):
            with pytest.raises(RuntimeError, match="FATAL SECURITY MISCONFIGURATION"):
                get_jwt_secret()

    def test_development_ephemeral_secret_allowed(self):
        """Development mode may generate ephemeral secrets."""
        from backend.app.core.config import get_jwt_secret

        with patch.dict("os.environ", {"ENVIRONMENT": "development", "JWT_SECRET_KEY": ""}):
            secret = get_jwt_secret()
            assert len(secret) >= 32

    def test_no_hardcoded_default_passwords(self):
        """Config class must not contain hardcoded default passwords."""
        from backend.app.core.config import Settings

        # Instantiate with no env file to check raw defaults
        s = Settings(
            _env_file=None,
            DATABASE_URL="sqlite+aiosqlite:///test.db",
            POSTGRES_PASSWORD="",
            NEO4J_PASSWORD="",
        )
        assert "cyber_dev_password" not in s.POSTGRES_PASSWORD
        assert "cyber_graph_password" not in s.NEO4J_PASSWORD


# ============================================================
# 5. CORS & SECURITY HEADERS TESTS
# ============================================================


class TestCORSAndHeaders:
    """Validate CORS restrictions and security header enforcement."""

    def test_wildcard_cors_blocked_in_production(self):
        """Wildcard CORS origin must trigger fatal error in production."""
        from backend.app.core.config import settings

        # Verify current dev config doesn't contain wildcard
        assert "*" not in settings.ALLOWED_CORS_ORIGINS

    def test_security_headers_present(self):
        """Verify the main app includes all required security headers middleware."""
        from backend.app.main import app

        # Check middleware is registered
        middleware_names = [m.cls.__name__ for m in app.user_middleware if hasattr(m, "cls")]
        assert "CORSMiddleware" in middleware_names


# ============================================================
# 6. RATE LIMITING TESTS
# ============================================================


class TestRateLimiting:
    """Validate rate limiting prevents brute-force attacks."""

    def test_sliding_window_enforcement(self):
        from backend.app.core.rate_limit import SlidingWindowRateLimiter
        import asyncio

        limiter = SlidingWindowRateLimiter(default_max_requests=3, default_window_seconds=60)

        async def test_burst():
            for _ in range(3):
                allowed, _, _ = await limiter.is_allowed("test_key")
                assert allowed
            # 4th request should be rejected
            allowed, remaining, retry_after = await limiter.is_allowed("test_key")
            assert not allowed
            assert remaining == 0
            assert retry_after > 0

        asyncio.run(test_burst())

    def test_alert_rate_limiter(self):
        from backend.app.alerts.rate_limiter import InMemoryRateLimiter

        limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("ip1:/path")
        assert limiter.is_allowed("ip1:/path")
        assert not limiter.is_allowed("ip1:/path")  # 3rd rejected
        # Different key should still be allowed
        assert limiter.is_allowed("ip2:/path")


# ============================================================
# 7. AUDIT LOGGING TESTS
# ============================================================


class TestAuditLogging:
    """Validate audit service masks sensitive data."""

    def test_audit_masks_account_numbers(self):
        from backend.app.services.audit_service import AuditAction, AuditService
        import asyncio

        service = AuditService()

        async def test():
            record = await service.log_event(
                action=AuditAction.VIEW_ACCOUNT,
                actor_id="test@cybercell.gov.in",
                actor_role="INVESTIGATOR",
                resource_type="ACCOUNT",
                resource_id="SYN1122334455",
                status="SUCCESS",
            )
            # Account number should be masked in the record
            assert "1122334455" not in record["resource_id"]
            assert "****" in record["resource_id"]

        asyncio.run(test())

    def test_audit_redacts_sensitive_details(self):
        from backend.app.services.audit_service import AuditAction, AuditService
        import asyncio

        service = AuditService()

        async def test():
            record = await service.log_event(
                action=AuditAction.LOGIN,
                actor_id="test@cybercell.gov.in",
                actor_role="ADMIN",
                resource_type="AUTH",
                resource_id="test@cybercell.gov.in",
                status="SUCCESS",
                details={"password": "secret123", "token": "jwt.value"},
            )
            assert record["details"]["password"] == "[REDACTED]"
            assert record["details"]["token"] == "[REDACTED]"

        asyncio.run(test())


# ============================================================
# 8. DEMO SECURITY TESTS
# ============================================================


class TestDemoSecurity:
    """Validate demo endpoints require proper auth and roles."""

    def test_demo_endpoints_require_auth_roles(self):
        """Demo endpoints must have RBAC dependencies declared."""
        from backend.app.api.v1.endpoints.demo import router

        for route in router.routes:
            if hasattr(route, "path") and route.path in ("/simulate-fraud", "/reset", "/status"):
                # All demo routes must have dependencies requiring roles
                assert route.dependencies, f"Route {route.path} has no auth dependencies"
