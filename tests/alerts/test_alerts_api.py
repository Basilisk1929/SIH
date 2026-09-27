"""Integration tests for Alert Engine REST API, WebSockets, and SSE streams."""

from fastapi.testclient import TestClient
from starlette.requests import Request
import pytest

from backend.app.alerts.constants import (
    ALERT_DISCLAIMER,
    SEVERITY_CRITICAL,
    STATE_ACKNOWLEDGED,
    STATE_FALSE_POSITIVE,
    STATE_INVESTIGATING,
    STATE_NEW,
    STATE_RESOLVED,
)
from backend.app.alerts.broadcaster import AlertBroadcaster
from backend.app.alerts.engine import alert_engine
from backend.app.alerts.rate_limiter import rate_limiter
from backend.app.core.security import create_access_token
from backend.app.main import app

client = TestClient(app)

# Auth headers for test requests (ADMIN role to access all endpoints)
_admin_token = create_access_token(subject="admin@cybercell.gov.in", role="ADMIN")
AUTH_HEADERS = {"Authorization": f"Bearer {_admin_token}"}


@pytest.fixture(autouse=True)
def reset_alert_engine():
    alert_engine.clear()
    rate_limiter.reset()


def test_post_alerts_create_and_deduplication():
    payload = {
        "event": {
            "transaction_id": "TXN_API_001",
            "account_id": "SYN_API_ACC_10",
            "receiver_account": "SYN_API_ACC_20",
            "amount": 75000.0,
            "ml_risk_score": 93.5,
            "transactions_last_1h": 7,
            "cashout_ratio": 0.89,
            "complaint_link_count": 2,
        },
        "dedup_window_seconds": 300,
    }

    # 1. Create alert
    res = client.post("/alerts", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 201
    data = res.json()
    assert data["alert_id"].startswith("ALT_")
    assert data["severity"] == SEVERITY_CRITICAL
    assert data["status"] == STATE_NEW
    assert data["risk_score"] >= 85.0
    assert data["is_deduplicated"] is False
    assert data["duplicate_count"] == 1
    assert data["disclaimer"] == ALERT_DISCLAIMER

    # 2. Duplicate submission within 300s window
    res_dup = client.post("/alerts", json=payload, headers=AUTH_HEADERS)
    assert res_dup.status_code == 201
    data_dup = res_dup.json()
    assert data_dup["alert_id"] == data["alert_id"]
    assert data_dup["is_deduplicated"] is True
    assert data_dup["duplicate_count"] == 2


def test_get_alerts_list_and_filters():
    # Insert two alerts
    p1 = {
        "event": {
            "transaction_id": "TXN_LST_01",
            "account_id": "ACC_LST_1",
            "amount": 50000.0,
            "ml_risk_score": 90.0,
            "complaint_link_count": 2,
        }
    }
    p2 = {
        "event": {
            "transaction_id": "TXN_LST_02",
            "account_id": "ACC_LST_2",
            "amount": 500.0,
            "ml_risk_score": 10.0,
        }
    }
    client.post("/alerts", json=p1, headers=AUTH_HEADERS)
    client.post("/alerts", json=p2, headers=AUTH_HEADERS)

    # List all
    res = client.get("/alerts", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Filter by severity
    res_sev = client.get("/alerts?severity=CRITICAL", headers=AUTH_HEADERS)
    assert res_sev.status_code == 200
    assert res_sev.json()["total"] == 1

    # Invalid filter returns 400
    res_bad = client.get("/alerts?severity=INVALID_TIER", headers=AUTH_HEADERS)
    assert res_bad.status_code == 400


def test_get_alert_by_id_and_not_found():
    payload = {
        "event": {
            "transaction_id": "TXN_SINGLE_01",
            "account_id": "ACC_SINGLE",
            "amount": 25000.0,
            "ml_risk_score": 70.0,
        }
    }
    create_res = client.post("/alerts", json=payload, headers=AUTH_HEADERS)
    alert_id = create_res.json()["alert_id"]
    sys_id = create_res.json()["id"]

    # Lookup by business alert_id
    res1 = client.get(f"/alerts/{alert_id}", headers=AUTH_HEADERS)
    assert res1.status_code == 200
    assert res1.json()["alert_id"] == alert_id

    # Lookup by UUID
    res2 = client.get(f"/alerts/{sys_id}", headers=AUTH_HEADERS)
    assert res2.status_code == 200
    assert res2.json()["id"] == sys_id

    # 404 for unknown
    res_404 = client.get("/alerts/NON_EXISTENT_ID", headers=AUTH_HEADERS)
    assert res_404.status_code == 404


def test_patch_alert_status_workflow():
    payload = {
        "event": {
            "transaction_id": "TXN_STATUS_01",
            "account_id": "ACC_STATUS",
            "amount": 30000.0,
            "ml_risk_score": 65.0,
        }
    }
    create_res = client.post("/alerts", json=payload, headers=AUTH_HEADERS)
    alert_id = create_res.json()["alert_id"]

    # 1. NEW -> ACKNOWLEDGED
    patch1 = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": STATE_ACKNOWLEDGED, "investigator_id": "AGENT_007"},
        headers=AUTH_HEADERS,
    )
    assert patch1.status_code == 200
    assert patch1.json()["status"] == STATE_ACKNOWLEDGED
    assert patch1.json()["investigator_id"] == "AGENT_007"

    # 2. ACKNOWLEDGED -> INVESTIGATING
    patch2 = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": STATE_INVESTIGATING, "resolution_notes": "Case #42 opened"},
        headers=AUTH_HEADERS,
    )
    assert patch2.status_code == 200
    assert patch2.json()["status"] == STATE_INVESTIGATING

    # 3. INVESTIGATING -> RESOLVED
    patch3 = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": STATE_RESOLVED, "resolution_notes": "Lien hold confirmed by bank"},
        headers=AUTH_HEADERS,
    )
    assert patch3.status_code == 200
    assert patch3.json()["status"] == STATE_RESOLVED

    # 4. Invalid status string returns 422 / 400
    patch_bad = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": "INVALID_STATE"},
        headers=AUTH_HEADERS,
    )
    assert patch_bad.status_code in [400, 422]


def test_get_alerts_stats():
    payload = {
        "event": {
            "transaction_id": "TXN_STATS_01",
            "account_id": "ACC_STATS",
            "amount": 50000.0,
            "ml_risk_score": 92.0,
            "complaint_link_count": 2,
        }
    }
    client.post("/alerts", json=payload, headers=AUTH_HEADERS)

    res = client.get("/alerts/stats", headers=AUTH_HEADERS)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_alerts"] == 1
    assert stats["by_severity"]["CRITICAL"] == 1
    assert stats["by_status"]["NEW"] == 1


@pytest.mark.asyncio
async def test_sse_endpoint_and_broadcaster():
    # Verify SSE stream delivers initial handshake and real-time broadcasts
    b = AlertBroadcaster()
    gen = b.subscribe_sse()
    handshake = await anext(gen)
    assert "CONNECTED" in handshake
    assert "Golden-Hour" in handshake

    # Broadcast test event
    await b.broadcast({"event_type": "ALERT_CREATED", "alert_id": "ALT-TEST-999"})
    broadcast_msg = await anext(gen)
    assert "ALT-TEST-999" in broadcast_msg
    await gen.aclose()


def test_websocket_requires_auth_token():
    """WebSocket connections without a valid JWT token must be rejected."""
    # Connection without token should fail
    with pytest.raises(Exception):
        with client.websocket_connect("/alerts/ws") as websocket:
            websocket.send_text("ping")

    # Connection with valid token should work
    with client.websocket_connect(f"/alerts/ws?token={_admin_token}") as websocket:
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert "PONG" in response


def test_rate_limiting_enforcement():
    # Test rate limiter logic directly
    limiter = rate_limiter
    limiter.max_requests = 3
    limiter.window_seconds = 60

    assert limiter.is_allowed("test_client") is True
    assert limiter.is_allowed("test_client") is True
    assert limiter.is_allowed("test_client") is True
    assert limiter.is_allowed("test_client") is False


def test_unauthenticated_alert_access_rejected():
    """Verify that alert endpoints reject unauthenticated requests."""
    res = client.get("/alerts")
    assert res.status_code == 401

    res = client.get("/alerts/stats")
    assert res.status_code == 401

    res = client.post("/alerts", json={"event": {"transaction_id": "test"}})
    assert res.status_code == 401
