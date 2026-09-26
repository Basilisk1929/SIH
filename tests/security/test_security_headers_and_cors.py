"""Tests verifying secure HTTP defense-in-depth headers and CORS policies."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_defense_in_depth_security_headers_present():
    """Verify all mandatory defense-in-depth HTTP security headers are present on API responses."""
    res = client.get("/")
    assert res.status_code == 200

    headers = res.headers
    # Anti-sniffing
    assert headers["x-content-type-options"] == "nosniff"
    # Anti-clickjacking
    assert headers["x-frame-options"] == "DENY"
    # HSTS
    assert "max-age=31536000" in headers["strict-transport-security"]
    # CSP
    assert "default-src 'self'" in headers["content-security-policy"]
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    # Referrer
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    # Permissions
    assert "geolocation=()" in headers["permissions-policy"]


def test_cache_control_headers_on_authenticated_api_routes():
    """Verify Cache-Control: no-store prevents caching of sensitive intelligence views."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert "no-store" in res.headers["cache-control"]
    assert "no-cache" in res.headers["cache-control"]


def test_cors_preflight_and_origin_allowlist():
    """Verify CORS allowlist and headers."""
    # Preflight from allowed origin
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization,Content-Type",
    }
    res = client.options("/api/v1/auth/login", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"

    # Preflight from untrusted origin
    bad_headers = {
        "Origin": "http://evil-attacker-site.com",
        "Access-Control-Request-Method": "POST",
    }
    res_bad = client.options("/api/v1/auth/login", headers=bad_headers)
    assert res_bad.headers.get("access-control-allow-origin") is None
