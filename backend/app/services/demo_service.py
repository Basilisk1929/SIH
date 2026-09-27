"""SIH End-to-End Demo Simulation Service.

Orchestrates controlled, deterministic synthetic fraud scenarios passing through
the COMPLETE real platform:
Synthetic Transaction
  -> Ingestion & Validation
  -> PostgreSQL / Synced In-Memory
  -> XGBoost Financial Risk Engine
  -> Neo4j Graph Topology
  -> H3 Geospatial Intelligence & Proximity
  -> Phase 11C Cash-Out Location Predictor
  -> Real-Time Alert Engine
  -> WebSocket / SSE Broadcaster
  -> React Investigation Dashboard

Also executes Complaint -> spaCy NLP extraction -> Entity Linking -> Graph Evidence.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from backend.app.alerts.broadcaster import alert_broadcaster
from backend.app.alerts.engine import alert_engine
from backend.app.models.complaint import Complaint
from backend.app.models.transaction import Transaction
from backend.app.models.case import Case, CaseEvidence, CaseNote, CaseTimelineEvent
from backend.app.schemas.demo import DemoResetResponse, DemoSimulateResponse, DemoStatusResponse
from backend.app.services.audit_service import AuditAction, audit_service
from backend.app.services.case_service import case_service
from backend.app.services.pipeline_service import (
    PipelineService,
    _ACTIVE_GRAPH_EDGES,
    _PROCESSED_COMPLAINTS,
    _PROCESSED_TRANSACTIONS,
)
from geo.prediction.predictor import CashoutLocationPredictor
from geo.prediction.schemas import CashoutPredictionRequest

logger = logging.getLogger("demo.service")


class DemoService:
    """Manages synthetic demonstration fraud scenarios and clean reset mechanisms."""

    @classmethod
    async def simulate_fraud_scenario(
        cls,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
        neo4j_session: Optional[Any] = None,
    ) -> DemoSimulateResponse:
        """Execute a complete, live multi-subsystem fraud simulation scenario."""
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        scenario_id = f"SCENARIO_SIH_{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"

        # 1. Audit Log: DEMO_SIMULATION_STARTED
        await audit_service.log_event(
            action=AuditAction.DEMO_SIMULATION_STARTED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="DEMO_SCENARIO",
            resource_id=scenario_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={"scenario_id": scenario_id, "timestamp": now_iso},
        )

        # 2. Synthetic Account & Identity Entities (Explicitly marked DEMO)
        victim_acc = "SYN_DEMO_VICTIM_4011"
        mule_acc = "SYN_DEMO_MULE_9088"
        victim_upi = "victim.demo@synthaxis"
        mule_upi = "mule.demo@synthaxis"
        amount = 85000.00
        lat = 28.6139  # New Delhi Cyber Crime Reference Center
        lng = 77.2090

        # 3. STEP A: NCRP Complaint Ingestion & spaCy NLP Pipeline
        complaint_ack = f"DEMO-NCRP-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        complaint_narrative = (
            f"Complainant received an urgent fraudulent call from a suspect claiming to be an "
            f"electricity department executive threatening immediate power disconnection unless an "
            f"outstanding amount of INR 85000 is remitted to UPI handle {mule_upi} linked to "
            f"State Bank of India account {mule_acc}."
        )

        complaint_res = await PipelineService.process_complaint(
            payload={
                "acknowledgement_no": complaint_ack,
                "narrative": complaint_narrative,
                "reported_loss_inr": amount,
                "victim_state": "Delhi",
                "victim_district": "New Delhi",
                "suspect_account_number": mule_acc,
                "suspect_upi": mule_upi,
                "suspect_bank": "State Bank of India",
            },
            db=db,
            neo4j_session=neo4j_session,
        )

        # 4. STEP B: High-Velocity Fraudulent Transaction through Unified Pipeline
        txn_ref = f"DEMO_TXN_{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"
        txn_res = await PipelineService.process_transaction(
            payload={
                "transaction_id": txn_ref,
                "sender_account": victim_acc,
                "receiver_account": mule_acc,
                "amount": amount,
                "rail_type": "UPI",
                "sender_upi": victim_upi,
                "receiver_upi": mule_upi,
                "latitude": lat,
                "longitude": lng,
                "transaction_frequency": 14.0,
                "transactions_last_1h": 8.0,
                "transactions_last_24h": 12.0,
                "unique_receivers": 4.0,
                "unique_senders": 1.0,
                "cashout_ratio": 0.94,
                "account_age": 15.0,  # Young account
                "graph_degree": 4.0,
                "graph_centrality": 0.08,
                "complaint_link_count": 1.0,
                "geographic_distance": 0.45,
            },
            db=db,
            neo4j_session=neo4j_session,
        )

        # 5. STEP C: Phase 11C Predictive Cash-Out Location Ranking Engine
        predictor = CashoutLocationPredictor()
        prediction_req = CashoutPredictionRequest(
            account_id=mule_acc,
            current_latitude=lat,
            current_longitude=lng,
            candidate_radius_km=15.0,
            top_k=3,
            account_risk_score=float(txn_res["risk_assessment"]["risk_score"]),
            cashout_ratio=0.94,
            transactions_last_1h=8,
            recent_transactions=[
                {
                    "transaction_id": txn_ref,
                    "latitude": lat,
                    "longitude": lng,
                    "amount": amount,
                    "transaction_type": "TRANSFER",
                    "timestamp": now_iso,
                }
            ],
        )
        prediction_res = predictor.predict(prediction_req)
        cashout_prediction_dict = prediction_res.model_dump()

        # 6. Audit Log: DEMO_SIMULATION_COMPLETED
        await audit_service.log_event(
            action=AuditAction.DEMO_SIMULATION_COMPLETED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="DEMO_SCENARIO",
            resource_id=scenario_id,
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "scenario_id": scenario_id,
                "transaction_id": txn_ref,
                "alert_id": txn_res["alert"]["alert_id"] if txn_res.get("alert") else None,
                "risk_score": txn_res["risk_assessment"]["risk_score"],
            },
        )

        narrative_summary = (
            f"End-to-End Simulation: High-velocity UPI fraud of ₹{amount:,.2f} detected from {victim_acc} "
            f"to suspected mule {mule_acc}. XGBoost calibrated risk score: {txn_res['risk_assessment']['risk_score']:.1f}/100 ({txn_res['risk_assessment']['risk_band']}). "
            f"Real-Time Alert Engine generated {txn_res['alert']['alert_id'] if txn_res.get('alert') else 'N/A'}. "
            f"Phase 11C Cash-Out Predictor identified {len(prediction_res.predicted_atms)} candidate withdrawal ATMs."
        )

        return DemoSimulateResponse(
            scenario_id=scenario_id,
            status="COMPLETED",
            is_demo=True,
            narrative_summary=narrative_summary,
            victim_account=victim_acc,
            mule_account=mule_acc,
            amount_inr=amount,
            complaint=complaint_res,
            transaction=txn_res,
            ml_risk_assessment=txn_res.get("risk_assessment"),
            graph_evidence=txn_res.get("graph_evidence"),
            geospatial_intelligence=txn_res.get("geospatial_intelligence"),
            cashout_prediction=cashout_prediction_dict,
            alert=txn_res.get("alert"),
            created_at=now_iso,
        )

    @classmethod
    async def reset_demo_data(
        cls,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> DemoResetResponse:
        """Purge all synthetic demonstration records from memory and database tables."""
        now = datetime.now(timezone.utc)
        purged_alerts = 0
        purged_transactions = 0
        purged_complaints = 0
        purged_cases = 0
        purged_graph_edges = 0

        # 1. Purge Demo Alerts from Alert Engine
        with alert_engine._lock:
            alert_ids_to_remove = []
            for alert_id, alert in list(alert_engine._alerts_by_id.items()):
                if (
                    alert.account_id.startswith("SYN_DEMO_")
                    or alert.alert_id.startswith("ALT_DEMO_")
                    or "DEMO" in str(alert.triggered_entity_id)
                ):
                    alert_ids_to_remove.append(alert_id)

            for aid in alert_ids_to_remove:
                alert_obj = alert_engine._alerts_by_id.pop(aid, None)
                if alert_obj and alert_obj.alert_id in alert_engine._alerts_by_business_id:
                    alert_engine._alerts_by_business_id.pop(alert_obj.alert_id, None)
                purged_alerts += 1

        # 2. Purge Demo Transactions from memory pipeline
        for k in list(_PROCESSED_TRANSACTIONS.keys()):
            if k.startswith("DEMO_") or "DEMO" in k or _PROCESSED_TRANSACTIONS[k].get("sender_account", "").startswith("SYN_DEMO_"):
                _PROCESSED_TRANSACTIONS.pop(k, None)
                purged_transactions += 1

        # 3. Purge Demo Complaints from memory pipeline
        for k in list(_PROCESSED_COMPLAINTS.keys()):
            if k.startswith("DEMO-") or "DEMO" in k:
                _PROCESSED_COMPLAINTS.pop(k, None)
                purged_complaints += 1

        # 4. Purge Demo Graph Edges
        global _ACTIVE_GRAPH_EDGES
        initial_edge_count = len(_ACTIVE_GRAPH_EDGES)
        _ACTIVE_GRAPH_EDGES = [
            e for e in _ACTIVE_GRAPH_EDGES
            if not (
                str(e.get("source", "")).startswith("SYN_DEMO_")
                or str(e.get("target", "")).startswith("SYN_DEMO_")
                or "DEMO" in str(e.get("properties", {}).get("transaction_id", ""))
            )
        ]
        purged_graph_edges = initial_edge_count - len(_ACTIVE_GRAPH_EDGES)

        # 5. Purge Demo Cases from case_service
        case_keys_to_remove = []
        for c_key, c_val in list(case_service._MEMORY_CASES.items()):
            if (
                "DEMO" in c_val.get("title", "")
                or any(acc.startswith("SYN_DEMO_") for acc in c_val.get("linked_account_numbers", []))
                or str(c_val.get("alert_id", "")).startswith("ALT_DEMO_")
            ):
                case_keys_to_remove.append(c_key)

        for ck in set(case_keys_to_remove):
            case_service._MEMORY_CASES.pop(ck, None)
            purged_cases += 1
        purged_cases = purged_cases // 2 if purged_cases > 0 else 0  # Deduplicate duplicate keys

        # 6. Database Purging if active session
        if db is not None:
            try:
                # Delete demo transactions
                await db.execute(delete(Transaction).where(Transaction.txn_ref_no.like("DEMO_%")))
                # Delete demo complaints
                await db.execute(delete(Complaint).where(Complaint.acknowledgement_no.like("DEMO-%")))
                await db.commit()
            except Exception as e:
                logger.warning(f"Database demo reset fallback: {e}")

        # 7. Broadcast DEMO_DATA_RESET Event to Connected UIs
        await alert_broadcaster.broadcast({
            "event_type": "DEMO_DATA_RESET",
            "purged_alerts": purged_alerts,
            "purged_cases": purged_cases,
            "timestamp": now.isoformat(),
        })

        # 8. Forensic Audit Log: DEMO_DATA_RESET
        await audit_service.log_event(
            action=AuditAction.DEMO_DATA_RESET,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="DEMO_SYSTEM",
            resource_id="GLOBAL",
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "purged_alerts": purged_alerts,
                "purged_transactions": purged_transactions,
                "purged_complaints": purged_complaints,
                "purged_cases": purged_cases,
            },
        )

        return DemoResetResponse(
            status="SUCCESS",
            purged_alerts=purged_alerts,
            purged_transactions=purged_transactions,
            purged_complaints=purged_complaints,
            purged_cases=purged_cases,
            purged_graph_edges=purged_graph_edges,
            message="Synthetic demonstration artifacts successfully purged from active intelligence stores.",
            reset_at=now,
        )

    @classmethod
    def get_demo_status(cls) -> DemoStatusResponse:
        """Inspect count of demo records currently loaded in memory."""
        demo_alerts = 0
        for alert in alert_engine._alerts_by_id.values():
            if alert.account_id.startswith("SYN_DEMO_") or "DEMO" in alert.alert_id:
                demo_alerts += 1

        demo_cases = 0
        seen_case_nums = set()
        for c in case_service._MEMORY_CASES.values():
            c_num = c.get("case_number")
            if c_num and c_num not in seen_case_nums:
                seen_case_nums.add(c_num)
                if "DEMO" in c.get("title", "") or any(acc.startswith("SYN_DEMO_") for acc in c.get("linked_account_numbers", [])):
                    demo_cases += 1

        demo_txns = sum(1 for k in _PROCESSED_TRANSACTIONS if "DEMO" in k)
        demo_cmps = sum(1 for k in _PROCESSED_COMPLAINTS if "DEMO" in k)

        return DemoStatusResponse(
            is_demo_mode_enabled=True,
            active_demo_alerts_count=demo_alerts,
            active_demo_cases_count=demo_cases,
            active_demo_transactions_count=demo_txns,
            active_demo_complaints_count=demo_cmps,
            disclaimer="SIH Demonstration Mode active.",
        )


demo_service = DemoService()
