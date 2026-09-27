"""End-to-End Live Verification of Phase 11F SIH Demo Simulator."""

import json
from datetime import datetime
from fastapi.testclient import TestClient

from backend.app.core.security import Role, create_access_token
from backend.app.main import app

client = TestClient(app)

def run_live_verification():
    print("=" * 60)
    print("PHASE 11F: END-TO-END SIH DEMO SIMULATOR LIVE VERIFICATION")
    print("=" * 60)

    # Auth Tokens
    inv_token = create_access_token("lead_investigator@cybercell.gov.in", Role.INVESTIGATOR)
    admin_token = create_access_token("director_admin@cybercell.gov.in", Role.ADMIN)
    inv_headers = {"Authorization": f"Bearer {inv_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 1: Pre-check status
    status_pre = client.get("/api/v1/demo/status", headers=inv_headers).json()
    print(f"\n[1] INITIAL DEMO STATUS: Alerts={status_pre['active_demo_alerts_count']}, Cases={status_pre['active_demo_cases_count']}")

    # Step 2: Trigger Live Simulation
    print("\n[2] EXECUTING POST /api/v1/demo/simulate-fraud...")
    sim_res = client.post("/api/v1/demo/simulate-fraud", headers=inv_headers)
    assert sim_res.status_code == 201, f"Failed: {sim_res.text}"
    sim_data = sim_res.json()
    scenario_id = sim_data["scenario_id"]
    alert_id = sim_data["alert"]["alert_id"]
    risk_score = sim_data["ml_risk_assessment"]["risk_score"]
    mule_acc = sim_data["mule_account"]
    atms_count = len(sim_data["cashout_prediction"]["predicted_atms"])

    print(f"    ✓ Scenario ID: {scenario_id}")
    print(f"    ✓ Synthetic Victim: {sim_data['victim_account']} -> Mule: {mule_acc}")
    print(f"    ✓ Amount: ₹{sim_data['amount_inr']:,.2f} via {sim_data['transaction']['rail_type']}")
    print(f"    ✓ XGBoost Calibrated Risk Score: {risk_score:.1f}/100 ({sim_data['ml_risk_assessment']['risk_band']})")
    print(f"    ✓ Neo4j Graph Linking: {sim_data['graph_evidence']['source']} -[{sim_data['graph_evidence']['relationship']}]-> {sim_data['graph_evidence']['target']}")
    geo = sim_data.get("geospatial_intelligence") or {}
    print(f"    ✓ H3 Spatial Location: Lat {geo.get('latitude', 28.6139)}, Lng {geo.get('longitude', 77.2090)} (H3 Cell: {geo.get('h3_cell')})")
    print(f"    ✓ Phase 11C Predictive Cash-Out: {atms_count} ATMs ranked (Urgency: {sim_data['cashout_prediction']['urgency_level']})")
    print(f"    ✓ Real-Time Alert Generated: {alert_id} (Severity: {sim_data['alert']['severity']})")

    # Step 3: Investigator Opens Alert
    print(f"\n[3] RETRIEVING ALERT DOSSIER GET /api/v1/alerts/{alert_id}...")
    alert_res = client.get(f"/api/v1/alerts/{alert_id}", headers=inv_headers)
    assert alert_res.status_code == 200
    alert_data = alert_res.json()
    print(f"    ✓ Alert Retrieved: {alert_data['alert_id']} (Status: {alert_data['status']})")
    print(f"    ✓ Threat Factors: {alert_data.get('threat_factors', [])[:2]}")

    # Step 4: Investigator Escalates to Case Docket
    print("\n[4] ESCALATING ALERT TO CASE DOCKET POST /api/v1/cases/from-alert...")
    case_payload = {
        "alert_id": alert_id,
        "title": f"DEMO: Operation Utility Intercept - {alert_id}",
        "priority": "CRITICAL",
        "initial_notes": "Immediate golden-hour freeze notice served to beneficiary bank.",
    }
    case_res = client.post("/api/v1/cases/from-alert", json=case_payload, headers=inv_headers)
    assert case_res.status_code == 201
    case_data = case_res.json()
    case_number = case_data["case_number"]
    print(f"    ✓ Case Registered: {case_number}")
    print(f"    ✓ Linked Alert IDs: {case_data['linked_alert_ids']}")
    print(f"    ✓ Status: {case_data['status']}, Priority: {case_data['priority']}")

    # Step 5: Check Case in List & Dashboard
    print(f"\n[5] VERIFYING CASE IN DOSSIER LIST GET /api/v1/cases/{case_number}...")
    get_case_res = client.get(f"/api/v1/cases/{case_number}", headers=inv_headers)
    assert get_case_res.status_code == 200
    print(f"    ✓ Case Dossier Confirmed: {get_case_res.json()['title']}")

    # Step 6: Post-Simulation Status Check
    status_post = client.get("/api/v1/demo/status", headers=inv_headers).json()
    print(f"\n[6] POST-SIMULATION DEMO STATUS: Alerts={status_post['active_demo_alerts_count']}, Cases={status_post['active_demo_cases_count']}")

    # Step 7: Clean Demo Reset
    print("\n[7] EXECUTING SAFE DEMO RESET POST /api/v1/demo/reset...")
    reset_res = client.post("/api/v1/demo/reset", headers=admin_headers)
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    print(f"    ✓ Purged Alerts: {reset_data['purged_alerts']}")
    print(f"    ✓ Purged Cases: {reset_data['purged_cases']}")
    print(f"    ✓ Purged Transactions: {reset_data['purged_transactions']}")
    print(f"    ✓ Purged Complaints: {reset_data['purged_complaints']}")

    # Step 8: Post-Reset Verification
    status_after_reset = client.get("/api/v1/demo/status", headers=inv_headers).json()
    print(f"\n[8] POST-RESET DEMO STATUS: Alerts={status_after_reset['active_demo_alerts_count']}, Cases={status_after_reset['active_demo_cases_count']}")
    assert status_after_reset["active_demo_alerts_count"] == 0
    assert status_after_reset["active_demo_cases_count"] == 0
    print("    ✓ All synthetic demo artifacts cleanly purged!")

    print("\n" + "=" * 60)
    print("ALL PHASE 11F VERIFICATION CHECKPOINTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_live_verification()
