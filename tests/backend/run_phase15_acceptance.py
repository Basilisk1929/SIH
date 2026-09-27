"""CyberShield-Intel Phase 15 Final SIH Acceptance Test Suite.

Executes live end-to-end verification across all 16 acceptance test criteria
against the live running application at http://127.0.0.1:8000 and ws://127.0.0.1:8000.
"""

import asyncio
import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional
import requests
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sih.acceptance")

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"

results: List[Dict[str, Any]] = []


def record_result(section: str, check_name: str, passed: bool, details: str = "") -> None:
    status = "PASS" if passed else "FAIL"
    results.append({
        "section": section,
        "check": check_name,
        "status": status,
        "details": details,
    })
    icon = "✅" if passed else "❌"
    print(f"{icon} [{section}] {check_name} -> {status} ({details})")


# ==============================================================================
# 1. CLEAN START & HEALTH
# ==============================================================================
def test_clean_start():
    print("\n--- SECTION 1: CLEAN START & HEALTH ---")
    try:
        res = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = res.status_code == 200 and res.json().get("status") == "healthy"
        record_result("Clean Start", "Liveness Probe (/health)", passed, f"Status: {res.status_code}")
    except Exception as e:
        record_result("Clean Start", "Liveness Probe (/health)", False, str(e))

    try:
        res = requests.get(f"{BASE_URL}/api/v1/health/ready", timeout=5)
        data = res.json()
        services = data.get("services", {})
        pg_ok = services.get("postgresql") == "connected"
        neo_ok = services.get("neo4j") == "connected"
        redis_ok = services.get("redis") == "connected"
        all_ok = res.status_code == 200 and pg_ok and neo_ok and redis_ok
        record_result(
            "Clean Start",
            "Readiness Probe (/api/v1/health/ready)",
            all_ok,
            f"PG={services.get('postgresql')}, Neo4j={services.get('neo4j')}, Redis={services.get('redis')}",
        )
    except Exception as e:
        record_result("Clean Start", "Readiness Probe (/api/v1/health/ready)", False, str(e))


# ==============================================================================
# 2. AUTHENTICATION & RBAC
# ==============================================================================
TOKENS: Dict[str, str] = {}


def test_authentication():
    print("\n--- SECTION 2: AUTHENTICATION & RBAC ---")
    roles_credentials = [
        ("ADMIN", "admin@cybercell.gov.in", "AdminSecure@2024!", "127.0.0.101"),
        ("SUPERVISOR", "supervisor@cybercell.gov.in", "Supervisor@2024!", "127.0.0.102"),
        ("INVESTIGATOR", "investigator@cybercell.gov.in", "Investigate@2024!", "127.0.0.103"),
        ("ANALYST", "analyst@cybercell.gov.in", "AnalystPass@2024!", "127.0.0.104"),
    ]

    for role_name, email, password, ip in roles_credentials:
        try:
            res = requests.post(
                f"{BASE_URL}/api/v1/auth/login-json",
                json={"email": email, "password": password},
                headers={"X-Forwarded-For": ip},
                timeout=5,
            )
            if res.status_code == 200:
                data = res.json()
                TOKENS[role_name] = data["access_token"]
                record_result("Authentication", f"Login {role_name}", True, f"Token received, exp in {data.get('expires_in_seconds')}s")
            else:
                record_result("Authentication", f"Login {role_name}", False, f"Status: {res.status_code}")
        except Exception as e:
            record_result("Authentication", f"Login {role_name}", False, str(e))

    # Invalid login test
    try:
        res = requests.post(
            f"{BASE_URL}/api/v1/auth/login-json",
            json={"email": "admin@cybercell.gov.in", "password": "WrongPassword123!"},
            headers={"X-Forwarded-For": "127.0.0.105"},
            timeout=5,
        )
        passed = res.status_code == 401
        record_result("Authentication", "Invalid Password Rejection", passed, f"Expected 401, got {res.status_code}")
    except Exception as e:
        record_result("Authentication", "Invalid Password Rejection", False, str(e))

    # Tampered / Invalid token rejection
    try:
        res = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token.here"},
            timeout=5,
        )
        passed = res.status_code == 401
        record_result("Authentication", "Invalid Token Signature Rejection", passed, f"Expected 401, got {res.status_code}")
    except Exception as e:
        record_result("Authentication", "Invalid Token Signature Rejection", False, str(e))

    # RBAC Restriction: ANALYST trying to access demo reset (which requires ADMIN or SUPERVISOR)
    try:
        analyst_token = TOKENS.get("ANALYST")
        res = requests.post(
            f"{BASE_URL}/api/v1/demo/reset",
            headers={"Authorization": f"Bearer {analyst_token}"},
            timeout=5,
        )
        passed = res.status_code == 403
        record_result("Authentication", "RBAC Analyst Denied Admin Reset", passed, f"Expected 403, got {res.status_code}")
    except Exception as e:
        record_result("Authentication", "RBAC Analyst Denied Admin Reset", False, str(e))

    # Logout / Token Revocation test
    try:
        temp_login = requests.post(
            f"{BASE_URL}/api/v1/auth/login-json",
            json={"email": "investigator@cybercell.gov.in", "password": "Investigate@2024!"},
            headers={"X-Forwarded-For": "127.0.0.106"},
            timeout=5,
        ).json()
        temp_token = temp_login["access_token"]
        # Logout
        logout_res = requests.post(
            f"{BASE_URL}/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {temp_token}"},
            timeout=5,
        )
        # Try accessing /auth/me with revoked token
        verify_res = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {temp_token}"},
            timeout=5,
        )
        passed = logout_res.status_code == 200 and verify_res.status_code == 401
        record_result("Authentication", "Logout & Token Revocation", passed, f"Logout={logout_res.status_code}, Subsequent={verify_res.status_code}")
    except Exception as e:
        record_result("Authentication", "Logout & Token Revocation", False, str(e))


# ==============================================================================
# 3. DASHBOARD & ANALYTICS
# ==============================================================================
def test_dashboard():
    print("\n--- SECTION 3: DASHBOARD & ANALYTICS ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}"}
    try:
        res = requests.get(f"{BASE_URL}/api/v1/analytics/overview", headers=headers, timeout=5)
        data = res.json()
        passed = res.status_code == 200 and "total_complaints_reported" in data and "active_mule_rings_detected" in data
        record_result("Dashboard", "Analytics Overview (/api/v1/analytics/overview)", passed, f"Complaints: {data.get('total_complaints_reported')}")
    except Exception as e:
        record_result("Dashboard", "Analytics Overview (/api/v1/analytics/overview)", False, str(e))

    try:
        res = requests.get(f"{BASE_URL}/api/v1/analytics/category-distribution", headers=headers, timeout=5)
        data = res.json()
        categories = data.get("categories", [])
        passed = res.status_code == 200 and len(categories) > 0
        record_result("Dashboard", "Category Distribution (/api/v1/analytics/category-distribution)", passed, f"Found {len(categories)} categories")
    except Exception as e:
        record_result("Dashboard", "Category Distribution (/api/v1/analytics/category-distribution)", False, str(e))

    try:
        res = requests.get(f"{BASE_URL}/api/v1/analytics/state-distribution", headers=headers, timeout=5)
        data = res.json()
        states = data.get("states", [])
        passed = res.status_code == 200 and len(states) > 0
        record_result("Dashboard", "State Distribution (/api/v1/analytics/state-distribution)", passed, f"Found {len(states)} states")
    except Exception as e:
        record_result("Dashboard", "State Distribution (/api/v1/analytics/state-distribution)", False, str(e))


# ==============================================================================
# 4. TRANSACTION -> RISK PIPELINE
# ==============================================================================
LAST_PIPELINE_RESULT: Dict[str, Any] = {}


def test_transaction_risk():
    print("\n--- SECTION 4: TRANSACTION -> RISK PIPELINE ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}"}
    payload = {
        "sender_account": "SYN1000004465",
        "receiver_account": "SYN1000002170",
        "amount": 165000.0,
        "rail_type": "IMPS",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "transactions_last_1h": 9,
        "cashout_ratio": 0.92,
    }
    try:
        res = requests.post(f"{BASE_URL}/api/v1/transactions", json=payload, headers=headers, timeout=5)
        data = res.json()
        passed = (
            res.status_code == 201
            and data.get("pipeline_status") == "SUCCESS"
            and data.get("risk_assessment", {}).get("risk_score", 0) > 50.0
            and data.get("alert") is not None
        )
        if passed:
            LAST_PIPELINE_RESULT.update(data)
        record_result(
            "Transaction Risk",
            "Transaction Ingestion -> XGBoost Risk Scoring",
            passed,
            f"Score: {data.get('risk_assessment', {}).get('risk_score')}, Band: {data.get('risk_assessment', {}).get('risk_band')}",
        )
    except Exception as e:
        record_result("Transaction Risk", "Transaction Ingestion -> XGBoost Risk Scoring", False, str(e))


# ==============================================================================
# 5. GRAPH INVESTIGATION
# ==============================================================================
def test_graph_investigation():
    print("\n--- SECTION 5: GRAPH INVESTIGATION ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}"}
    try:
        res = requests.get(f"{BASE_URL}/api/v1/graph/subgraph/SYN1000004465?depth=2", headers=headers, timeout=5)
        data = res.json()
        nodes = data.get("nodes", [])
        links = data.get("links", [])
        passed = res.status_code == 200 and len(nodes) > 0
        record_result("Graph Investigation", "Mule Account Subgraph (/api/v1/graph/subgraph)", passed, f"Nodes: {len(nodes)}, Links: {len(links)}")
    except Exception as e:
        record_result("Graph Investigation", "Mule Account Subgraph (/api/v1/graph/subgraph)", False, str(e))

    try:
        res = requests.get(f"{BASE_URL}/api/v1/graph/connected-accounts/SYN1000004465", headers=headers, timeout=5)
        data = res.json()
        passed = res.status_code == 200 and ("evidence" in data or "connected_accounts" in data)
        record_result("Graph Investigation", "Connected Accounts Exploration", passed, f"Status: {res.status_code}")
    except Exception as e:
        record_result("Graph Investigation", "Connected Accounts Exploration", False, str(e))


# ==============================================================================
# 6. GEOSPATIAL INTELLIGENCE
# ==============================================================================
def test_geospatial_intelligence():
    print("\n--- SECTION 6: GEOSPATIAL INTELLIGENCE ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}"}
    try:
        payload = {"latitude": 28.6139, "longitude": 77.2090, "resolution": 8}
        res = requests.post(f"{BASE_URL}/api/v1/geo/coordinate-analysis", json=payload, headers=headers, timeout=5)
        data = res.json()
        passed = res.status_code == 200 and "h3_cell" in data and len(data.get("h3_cell", "")) > 10
        record_result("Geo Intelligence", "Coordinate H3 Resolution (/api/v1/geo/coordinate-analysis)", passed, f"H3 Cell: {data.get('h3_cell')}")
    except Exception as e:
        record_result("Geo Intelligence", "Coordinate H3 Resolution (/api/v1/geo/coordinate-analysis)", False, str(e))

    try:
        res = requests.get(f"{BASE_URL}/api/v1/geo/hotspots", headers=headers, timeout=5)
        data = res.json()
        clusters = data.get("clusters", [])
        passed = res.status_code == 200 and len(clusters) > 0
        record_result("Geo Intelligence", "DBSCAN Crime Hotspots (/api/v1/geo/hotspots)", passed, f"Found {len(clusters)} hotspot clusters")
    except Exception as e:
        record_result("Geo Intelligence", "DBSCAN Crime Hotspots (/api/v1/geo/hotspots)", False, str(e))

    try:
        res = requests.get(f"{BASE_URL}/api/v1/geo/nearest-atms?lat=28.6139&lng=77.2090&top_k=5", headers=headers, timeout=5)
        data = res.json()
        atms = data.get("nearest_atms", [])
        passed = res.status_code == 200 and len(atms) > 0
        record_result("Geo Intelligence", "RBI ATM Registry Query (/api/v1/geo/nearest-atms)", passed, f"Found {len(atms)} operational ATMs")
    except Exception as e:
        record_result("Geo Intelligence", "RBI ATM Registry Query (/api/v1/geo/nearest-atms)", False, str(e))


# ==============================================================================
# 7. CASH-OUT PREDICTION (PHASE 11C)
# ==============================================================================
def test_cashout_prediction():
    print("\n--- SECTION 7: CASH-OUT PREDICTION ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}"}
    payload = {
        "account_id": "SYN1000004465",
        "current_latitude": 28.6139,
        "current_longitude": 77.2090,
        "candidate_radius_km": 15.0,
        "top_k": 3,
    }
    try:
        res = requests.post(f"{BASE_URL}/api/v1/geo/predict-cashout-location", json=payload, headers=headers, timeout=5)
        data = res.json()
        predicted = data.get("predicted_atms", [])
        passed = (
            res.status_code == 200
            and len(predicted) > 0
            and "disclaimer" in data
        )
        top_name = predicted[0].get("bank_name", "Unknown") if predicted else "None"
        top_score = predicted[0].get("prediction_score", 0) if predicted else 0
        record_result(
            "Cash-out Prediction",
            "ATM Cash-Out Likelihood Ranking",
            passed,
            f"Ranked {len(predicted)} ATMs, Top: {top_name} (Score: {top_score})",
        )
    except Exception as e:
        record_result("Cash-out Prediction", "ATM Cash-Out Likelihood Ranking", False, str(e))


# ==============================================================================
# 8. ALERT ENGINE & WORKFLOW
# ==============================================================================
GENERATED_ALERT_ID: Optional[str] = None


def test_alert_engine():
    global GENERATED_ALERT_ID
    print("\n--- SECTION 8: ALERT ENGINE & WORKFLOW ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}"}
    alert_payload = {
        "event": {
            "transaction_id": f"TX_ACCEPTANCE_{int(time.time()*1000)}",
            "account_id": "SYN1000004465",
            "receiver_account": "SYN1000002170",
            "amount": 185000.0,
            "ml_risk_score": 94.5,
            "transactions_last_1h": 12,
            "cashout_ratio": 0.96,
            "complaint_link_count": 3,
        }
    }
    try:
        res = requests.post(f"{BASE_URL}/alerts", json=alert_payload, headers=headers, timeout=5)
        data = res.json()
        passed = res.status_code == 201 and data.get("severity") in ["HIGH", "CRITICAL"]
        if passed:
            GENERATED_ALERT_ID = data["alert_id"]
        record_result("Alert Engine", "High-Risk Alert Generation", passed, f"Alert ID: {GENERATED_ALERT_ID}, Severity: {data.get('severity')}")
    except Exception as e:
        record_result("Alert Engine", "High-Risk Alert Generation", False, str(e))

    # Alert status progression
    if GENERATED_ALERT_ID:
        try:
            patch_res = requests.patch(
                f"{BASE_URL}/alerts/{GENERATED_ALERT_ID}/status",
                json={
                    "status": "INVESTIGATING",
                    "investigator_id": "inspector.sharma@cybercell.gov.in",
                    "resolution_notes": "Forensic case docket opened for multi-layer rapid cashout.",
                },
                headers=headers,
                timeout=5,
            )
            data = patch_res.json()
            passed = patch_res.status_code == 200 and data.get("status") == "INVESTIGATING"
            record_result("Alert Engine", "Alert Status Transition (NEW -> INVESTIGATING)", passed, f"New Status: {data.get('status')}")
        except Exception as e:
            record_result("Alert Engine", "Alert Status Transition (NEW -> INVESTIGATING)", False, str(e))


# ==============================================================================
# 9. REAL-TIME ALERT STREAMING (WEBSOCKET / SSE)
# ==============================================================================
async def _test_ws_auth():
    # 1. Unauthenticated WS should be rejected by server
    try:
        async with websockets.connect(f"{WS_URL}/alerts/ws") as ws:
            msg = await ws.recv()
            record_result("Real-time Alerts", "Unauthenticated WebSocket Rejection", False, f"Connected unexpectedly: {msg}")
    except Exception as e:
        err_str = str(e).lower()
        passed = "403" in err_str or "4001" in err_str or "rejected" in err_str
        record_result("Real-time Alerts", "Unauthenticated WebSocket Rejection", passed, f"Rejected cleanly: {e}")

    # 2. Authenticated WS with valid token
    try:
        token = TOKENS.get("INVESTIGATOR")
        async with websockets.connect(f"{WS_URL}/alerts/ws?token={token}") as ws:
            await ws.send("ping")
            response = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(response)
            passed = data.get("type") == "PONG"
            record_result("Real-time Alerts", "Authenticated WebSocket Ping/Pong Stream", passed, f"Received: {response}")
    except Exception as e:
        record_result("Real-time Alerts", "Authenticated WebSocket Ping/Pong Stream", False, str(e))


def test_realtime_alerts():
    print("\n--- SECTION 9: REAL-TIME ALERT STREAMING ---")
    asyncio.run(_test_ws_auth())


# ==============================================================================
# 10. COMPLAINT + NLP INTELLIGENCE
# ==============================================================================
def test_complaint_nlp():
    print("\n--- SECTION 10: COMPLAINT + NLP INTELLIGENCE ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}"}
    ack_no = f"NCRP-2024-SIH-{int(time.time()*1000)}"
    narrative = (
        "On 18-Aug-2024, complainant was duped of Rs 1,45,000 by a person claiming to be from electricity board. "
        "Transferred funds to UPI handle powerpay@okhdfcbank and account SYN1000004465 with IFSC SBIN0001234. "
        "Contact mobile: 9876543210. Location: Mumbai, Maharashtra."
    )
    payload = {
        "narrative": narrative,
        "victim_state": "Maharashtra",
        "acknowledgement_no": ack_no,
    }
    try:
        res = requests.post(f"{BASE_URL}/api/v1/complaints/pipeline", json=payload, headers=headers, timeout=5)
        data = res.json()
        passed = (
            res.status_code == 201
            and data.get("pipeline_status") == "SUCCESS"
            and data.get("reported_loss_inr") == 145000.0
            and data.get("linked_suspect_account") == "SYN1000004465"
            and "scam_typology" in data
        )
        record_result(
            "NLP Complaint",
            "Complaint Narrative NLP -> Entity Extraction & Typology",
            passed,
            f"Loss: Rs {data.get('reported_loss_inr')}, Account: {data.get('linked_suspect_account')}, Typology: {data.get('scam_typology', {}).get('scam_type')}",
        )
    except Exception as e:
        record_result("NLP Complaint", "Complaint Narrative NLP -> Entity Extraction & Typology", False, str(e))


# ==============================================================================
# 11. ALERT -> CASE WORKFLOW
# ==============================================================================
CREATED_CASE_ID: Optional[str] = None


def test_alert_to_case():
    global CREATED_CASE_ID
    print("\n--- SECTION 11: ALERT -> CASE WORKFLOW ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('SUPERVISOR')}"}
    if not GENERATED_ALERT_ID:
        record_result("Case Workflow", "Create Case from Alert", False, "No alert available")
        return

    # 1. Create Case from Alert
    case_payload = {
        "alert_id": GENERATED_ALERT_ID,
        "title": "Operation Rapid Cash-Out Defense (SIH Acceptance)",
        "description": "Multi-layer mule ring operating across synthetic account networks.",
        "priority": "CRITICAL",
        "assigned_investigator": "inspector.sharma@cybercell.gov.in",
    }
    try:
        res = requests.post(f"{BASE_URL}/api/v1/cases/from-alert", json=case_payload, headers=headers, timeout=5)
        data = res.json()
        passed = res.status_code == 201 and data.get("alert_id") == GENERATED_ALERT_ID
        if passed:
            CREATED_CASE_ID = data["id"]
        record_result("Case Workflow", "Create Case from Alert (/api/v1/cases/from-alert)", passed, f"Case ID: {CREATED_CASE_ID}, Case No: {data.get('case_number')}")
    except Exception as e:
        record_result("Case Workflow", "Create Case from Alert (/api/v1/cases/from-alert)", False, str(e))

    if not CREATED_CASE_ID:
        return

    # 2. Add Investigative Note
    try:
        note_res = requests.post(
            f"{BASE_URL}/api/v1/cases/{CREATED_CASE_ID}/notes",
            json={"content": "Verified bank statement. High velocity cashout confirmed within 4 minutes."},
            headers=headers,
            timeout=5,
        )
        passed = note_res.status_code == 201
        record_result("Case Workflow", "Append Forensic Note (/api/v1/cases/{id}/notes)", passed, f"Status: {note_res.status_code}")
    except Exception as e:
        record_result("Case Workflow", "Append Forensic Note (/api/v1/cases/{id}/notes)", False, str(e))

    # 3. Add Evidence Item (valid type: TRANSACTION, ACCOUNT, etc.)
    try:
        ev_res = requests.post(
            f"{BASE_URL}/api/v1/cases/{CREATED_CASE_ID}/evidence",
            json={
                "evidence_type": "ACCOUNT",
                "reference_id": "SYN1000004465",
                "title": "Mule Bank Account KYC & Ledger Extract",
                "description": "Verified suspect mule KYC discrepancy.",
                "metadata_json": {"bank": "Union Synth Bank", "risk_band": "CRITICAL"},
            },
            headers=headers,
            timeout=5,
        )
        passed = ev_res.status_code == 201
        record_result("Case Workflow", "Attach Digital Evidence Item", passed, f"Status: {ev_res.status_code}")
    except Exception as e:
        record_result("Case Workflow", "Attach Digital Evidence Item", False, str(e))

    # 4. Advance Case Status via PATCH /{id}
    try:
        status_res = requests.patch(
            f"{BASE_URL}/api/v1/cases/{CREATED_CASE_ID}",
            json={"status": "INVESTIGATING", "priority": "CRITICAL"},
            headers=headers,
            timeout=5,
        )
        data = status_res.json()
        passed = status_res.status_code == 200 and data.get("status") == "INVESTIGATING"
        record_result("Case Workflow", "Advance Case Status to INVESTIGATING", passed, f"Status: {data.get('status')}")
    except Exception as e:
        record_result("Case Workflow", "Advance Case Status to INVESTIGATING", False, str(e))

    # 5. Formally Resolve Case via POST /{id}/resolve
    try:
        resolve_res = requests.post(
            f"{BASE_URL}/api/v1/cases/{CREATED_CASE_ID}/resolve",
            json={
                "resolution_category": "CONFIRMED_FRAUD",
                "resolution_reason": "Mule account identified and frozen in Golden Hour protocol.",
                "resolution_notes": "Beneficiary account debits frozen via nodal bank mandate.",
            },
            headers=headers,
            timeout=5,
        )
        data = resolve_res.json()
        passed = resolve_res.status_code == 200 and data.get("status") == "RESOLVED"
        record_result("Case Workflow", "Formally Resolve Case Docket (Status=RESOLVED)", passed, f"Status: {data.get('status')}")
    except Exception as e:
        record_result("Case Workflow", "Formally Resolve Case Docket (Status=RESOLVED)", False, str(e))


# ==============================================================================
# 12. CASE SECURITY & OBJECT AUTHORIZATION
# ==============================================================================
def test_case_security():
    print("\n--- SECTION 12: CASE SECURITY & OBJECT AUTHORIZATION ---")
    # Analyst role should NOT be permitted to create a case
    try:
        res = requests.post(
            f"{BASE_URL}/api/v1/cases",
            json={"title": "Unauthorized Case Creation", "priority": "HIGH"},
            headers={"Authorization": f"Bearer {TOKENS.get('ANALYST')}"},
            timeout=5,
        )
        passed = res.status_code == 403
        record_result("Case Security", "Analyst Blocked from Case Creation", passed, f"Expected 403, got {res.status_code}")
    except Exception as e:
        record_result("Case Security", "Analyst Blocked from Case Creation", False, str(e))

    # Unauthenticated access rejected
    try:
        res = requests.get(f"{BASE_URL}/api/v1/cases", timeout=5)
        passed = res.status_code == 401
        record_result("Case Security", "Unauthenticated Case Listing Rejected", passed, f"Expected 401, got {res.status_code}")
    except Exception as e:
        record_result("Case Security", "Unauthenticated Case Listing Rejected", False, str(e))


# ==============================================================================
# 13. DEMO SIMULATOR & CLEAN RESET
# ==============================================================================
def test_demo_simulator():
    print("\n--- SECTION 13: DEMO SIMULATOR & CLEAN RESET ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('SUPERVISOR')}"}
    try:
        res = requests.post(f"{BASE_URL}/api/v1/demo/simulate-fraud", headers=headers, timeout=10)
        data = res.json()
        passed = (
            res.status_code == 201
            and data.get("status") == "COMPLETED"
            and "transaction" in data
            and "alert" in data
            and "cashout_prediction" in data
        )
        record_result(
            "Demo Simulator",
            "End-to-End SIH Fraud Simulation",
            passed,
            f"Scenario ID: {data.get('scenario_id')}, Alert: {data.get('alert', {}).get('alert_id')}",
        )
    except Exception as e:
        record_result("Demo Simulator", "End-to-End SIH Fraud Simulation", False, str(e))

    # Demo Reset (as ADMIN)
    try:
        admin_headers = {"Authorization": f"Bearer {TOKENS.get('ADMIN')}"}
        res = requests.post(f"{BASE_URL}/api/v1/demo/reset", headers=admin_headers, timeout=10)
        data = res.json()
        passed = res.status_code == 200 and data.get("status") == "SUCCESS"
        record_result(
            "Demo Simulator",
            "Non-Destructive Demo Data Reset",
            passed,
            f"Status: {data.get('status')}, Message: {data.get('message')}",
        )
    except Exception as e:
        record_result("Demo Simulator", "Non-Destructive Demo Data Reset", False, str(e))


# ==============================================================================
# 14. EXPORT SECURITY & FORENSIC AUDIT
# ==============================================================================
def test_export_audit():
    print("\n--- SECTION 14: EXPORT SECURITY & FORENSIC AUDIT ---")
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}"}
    if not CREATED_CASE_ID:
        record_result("Export & Audit", "Forensic Dossier Export", False, "No case available")
        return

    try:
        res = requests.get(f"{BASE_URL}/api/v1/cases/{CREATED_CASE_ID}/export", headers=headers, timeout=5)
        data = res.json()
        passed = (
            res.status_code == 200
            and "chain_of_custody_hash" in data
            and "case_data" in data
        )
        record_result(
            "Export & Audit",
            "Cryptographic SHA-256 Case Dossier Export",
            passed,
            f"Hash: {data.get('chain_of_custody_hash')[:16]}..., Export ID: {data.get('export_id')}",
        )
    except Exception as e:
        record_result("Export & Audit", "Cryptographic SHA-256 Case Dossier Export", False, str(e))

    # Unauthorized export rejection (ANALYST role)
    try:
        res = requests.get(
            f"{BASE_URL}/api/v1/cases/{CREATED_CASE_ID}/export",
            headers={"Authorization": f"Bearer {TOKENS.get('ANALYST')}"},
            timeout=5,
        )
        passed = res.status_code == 403
        record_result("Export & Audit", "Analyst Blocked from Case Dossier Export", passed, f"Expected 403, got {res.status_code}")
    except Exception as e:
        record_result("Export & Audit", "Analyst Blocked from Case Dossier Export", False, str(e))


# ==============================================================================
# 15. FAILURE TESTING & GRACEFUL DEGRADATION
# ==============================================================================
def test_failure_handling():
    print("\n--- SECTION 15: FAILURE TESTING & GRACEFUL DEGRADATION ---")
    # 1. Nonexistent endpoint
    res = requests.get(f"{BASE_URL}/api/v1/nonexistent-route-xyz", timeout=5)
    record_result("Failure Handling", "Non-Existent Endpoint Returns 404", res.status_code == 404, f"Got: {res.status_code}")

    # 2. Malformed JSON Body
    headers = {"Authorization": f"Bearer {TOKENS.get('INVESTIGATOR')}", "Content-Type": "application/json"}
    res = requests.post(f"{BASE_URL}/api/v1/transactions", data="not-valid-json", headers=headers, timeout=5)
    record_result("Failure Handling", "Malformed JSON Returns 422 Unprocessable", res.status_code in [400, 422], f"Got: {res.status_code}")

    # 3. Missing Required Fields
    res = requests.post(f"{BASE_URL}/api/v1/transactions", json={"amount": -100.0}, headers=headers, timeout=5)
    record_result("Failure Handling", "Validation Constraint Violation Returns 422", res.status_code == 422, f"Got: {res.status_code}")


# ==============================================================================
# MAIN RUNNER
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CYBERSHIELD-INTEL: PHASE 15 SIH FINAL ACCEPTANCE TEST RUNNER")
    print("=" * 80)

    test_clean_start()
    test_authentication()
    test_dashboard()
    test_transaction_risk()
    test_graph_investigation()
    test_geospatial_intelligence()
    test_cashout_prediction()
    test_alert_engine()
    test_realtime_alerts()
    test_complaint_nlp()
    test_alert_to_case()
    test_case_security()
    test_demo_simulator()
    test_export_audit()
    test_failure_handling()

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed

    print("\n" + "=" * 80)
    print(f"ACCEPTANCE TEST SUMMARY: Total={total} | Passed={passed} | Failed={failed}")
    print("=" * 80)

    if failed > 0:
        print("\nFAILED CHECKS:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"❌ [{r['section']}] {r['check']}: {r['details']}")
        sys.exit(1)
    else:
        print("\nALL ACCEPTANCE TESTS PASSED ACCORDING TO SPECIFICATION!")
        sys.exit(0)
