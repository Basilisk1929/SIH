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
from backend.app.main import app

client = TestClient(app)


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
    res = client.post("/alerts", json=payload)
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
    res_dup = client.post("/alerts", json=payload)
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
    client.post("/alerts", json=p1)
    client.post("/alerts", json=p2)

    # List all
    res = client.get("/alerts")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Filter by severity
    res_sev = client.get("/alerts?severity=CRITICAL")
    assert res_sev.status_code == 200
    assert res_sev.json()["total"] == 1

    # Invalid filter returns 400
    res_bad = client.get("/alerts?severity=INVALID_TIER")
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
    create_res = client.post("/alerts", json=payload)
    alert_id = create_res.json()["alert_id"]
    sys_id = create_res.json()["id"]

    # Lookup by business alert_id
    res1 = client.get(f"/alerts/{alert_id}")
    assert res1.status_code == 200
    assert res1.json()["alert_id"] == alert_id

    # Lookup by UUID
    res2 = client.get(f"/alerts/{sys_id}")
    assert res2.status_code == 200
    assert res2.json()["id"] == sys_id

    # 404 for unknown
    res_404 = client.get("/alerts/NON_EXISTENT_ID")
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
    create_res = client.post("/alerts", json=payload)
    alert_id = create_res.json()["alert_id"]

    # 1. NEW -> ACKNOWLEDGED
    patch1 = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": STATE_ACKNOWLEDGED, "investigator_id": "AGENT_007"},
    )
    assert patch1.status_code == 200
    assert patch1.json()["status"] == STATE_ACKNOWLEDGED
    assert patch1.json()["investigator_id"] == "AGENT_007"

    # 2. ACKNOWLEDGED -> INVESTIGATING
    patch2 = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": STATE_INVESTIGATING, "resolution_notes": "Case #42 opened"},
    )
    assert patch2.status_code == 200
    assert patch2.json()["status"] == STATE_INVESTIGATING

    # 3. INVESTIGATING -> RESOLVED
    patch3 = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": STATE_RESOLVED, "resolution_notes": "Lien hold confirmed by bank"},
    )
    assert patch3.status_code == 200
    assert patch3.json()["status"] == STATE_RESOLVED

    # 4. Invalid status string returns 422 / 400
    patch_bad = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": "INVALID_STATE"},
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
    client.post("/alerts", json=payload)

    res = client.get("/alerts/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_alerts"] == 1
    assert stats["by_severity"]["CRITICAL"] == 1
    assert stats["by_status"]["NEW"] == 1


@pytest.mark.asyncio
async def test_sse_endpoint_and_broadcaster():
    # 1. Verify direct route handler returns StreamingResponse with proper media-type and headers
    from backend.app.api.v1.endpoints.alerts import sse_alert_feed
    fake_req = Request(scope={"type": "http", "method": "GET", "path": "/alerts/sse", "headers": []})
    response = await sse_alert_feed(fake_req)
    assert response.media_type == "text/event-stream"
    assert "no-cache" in response.headers["cache-control"]

    # 2. Verify SSE stream delivers initial handshake and real-time broadcasts
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


def test_websocket_ping_pong():
    with client.websocket_connect("/alerts/ws") as websocket:
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert "PONG" in response


def test_rate_limiting_enforcement():
    # Make requests up to limit
    limiter = rate_limiter
    limiter.max_requests = 3
    limiter.window_seconds = 60

    # 3 requests allowed
    res1 = client.get("/alerts")
    assert res1.status_code == 200
    res2 = client.get("/alerts")
    assert res2.status_code == 200

    # Test rate limiter logic
    assert limiter.is_allowed("test_client") is True
    assert limiter.is_allowed("test_client") is True
    assert limiter.is_allowed("test_client") is True
    assert limiter.is_allowed("test_client") is False
