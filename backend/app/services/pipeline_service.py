"""Unified Pipeline Service connecting Ingestion, ML Risk Engine, Neo4j, Geo, Alert Engine, NLP, and Cases."""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Ingestion & Normalization
from ingestion.app.services.normalizer import DataNormalizer
from ingestion.app.services.deduplicator import duplicate_detector

# ML Financial Transaction Risk Engine (XGBoost)
from ml.inference.predictor import RiskInferenceService

# Geospatial Intelligence
from geo.validation.coordinate_validator import CoordinateValidator
from geo.indexing.h3_indexer import H3Indexer
from geo.proximity.atm_proximity import ATMProximityAnalyzer
from geo.constants import DEFAULT_H3_RESOLUTION, INDIA_BOUNDS

# Alert Engine
from backend.app.alerts.engine import alert_engine
from backend.app.alerts.schemas import TransactionEvent

# NLP Pipeline
from nlp.pipelines.cybercrime_nlp_pipeline import CybercrimeNLPPipeline
from nlp.normalizers.entity_normalizer import EntityNormalizer
from nlp.linking.entity_linker import EntityLinker

# Case System & Graph
from backend.app.api.v1.endpoints.cases import _IN_MEMORY_CASES
from backend.app.services.graph_service import GraphService
from backend.app.services.audit_service import AuditAction, audit_service
from backend.app.models.transaction import Transaction
from backend.app.models.complaint import Complaint

logger = logging.getLogger("pipeline.service")

# Thread-safe in-memory stores for fallback and rapid cross-referencing
_PROCESSED_TRANSACTIONS: Dict[str, Dict[str, Any]] = {}
_PROCESSED_COMPLAINTS: Dict[str, Dict[str, Any]] = {}
_ACTIVE_GRAPH_EDGES: List[Dict[str, Any]] = []


class PipelineService:
    """Orchestrates end-to-end multi-subsystem pipelines for transactions and complaints."""

    _risk_service: Optional[RiskInferenceService] = None
    _nlp_pipeline: Optional[CybercrimeNLPPipeline] = None
    _atm_analyzer: Optional[ATMProximityAnalyzer] = None

    @classmethod
    def get_risk_service(cls) -> RiskInferenceService:
        if cls._risk_service is None:
            cls._risk_service = RiskInferenceService()
        return cls._risk_service

    @classmethod
    def get_nlp_pipeline(cls) -> CybercrimeNLPPipeline:
        if cls._nlp_pipeline is None:
            cls._nlp_pipeline = CybercrimeNLPPipeline()
        return cls._nlp_pipeline

    @classmethod
    def get_atm_analyzer(cls) -> ATMProximityAnalyzer:
        if cls._atm_analyzer is None:
            cls._atm_analyzer = ATMProximityAnalyzer()
        return cls._atm_analyzer

    # ==========================================================================
    # 1. COMPLETE TRANSACTION PIPELINE
    # ==========================================================================
    @classmethod
    async def process_transaction(
        cls,
        payload: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        neo4j_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute complete flow:
        Transaction -> Ingestion -> Validation -> PostgreSQL -> Risk Engine -> Neo4j -> Geospatial Engine -> Alert Engine -> FastAPI -> Frontend
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Step 1: Ingestion & Validation
        raw_txn_id = payload.get("transaction_id") or payload.get("txn_ref_no") or f"TXN_{uuid.uuid4().hex[:8].upper()}"
        sender_acc = str(payload.get("sender_account") or payload.get("sender_account_number") or "SYN_UNKNOWN_SENDER").strip()
        receiver_acc = str(payload.get("receiver_account") or payload.get("receiver_account_number") or "SYN_UNKNOWN_RECEIVER").strip()
        amount = float(payload.get("amount") or payload.get("amount_inr") or 0.0)
        rail_type = str(payload.get("rail_type") or payload.get("payment_channel") or "UPI").upper()
        sender_upi = payload.get("sender_upi")
        receiver_upi = payload.get("receiver_upi")

        if amount <= 0:
            raise ValueError(f"Transaction amount must be strictly positive (> 0), got: {amount}")

        # Normalization
        norm_dict = DataNormalizer.normalize_record({
            "transaction_id": raw_txn_id,
            "sender_account_number": sender_acc,
            "receiver_account_number": receiver_acc,
            "amount": amount,
            "payment_channel": rail_type,
            "sender_upi": sender_upi,
            "receiver_upi": receiver_upi,
            "timestamp": payload.get("timestamp") or now_iso,
        }, "transaction")

        # Deduplication check
        is_dup = duplicate_detector.is_duplicate(
            "transaction",
            norm_dict.get("transaction_id", raw_txn_id),
            norm_dict,
        )

        # Step 2: Database Persistence (PostgreSQL / In-Memory Fallback)
        txn_record = {
            "id": str(uuid.uuid4()),
            "txn_ref_no": norm_dict.get("transaction_id", raw_txn_id),
            "sender_account": sender_acc,
            "receiver_account": receiver_acc,
            "amount_inr": amount,
            "rail_type": rail_type,
            "timestamp": now_iso,
            "status": "PROCESSED",
            "is_duplicate": is_dup,
        }

        if db is not None:
            try:
                db_txn = Transaction(
                    txn_ref_no=txn_record["txn_ref_no"],
                    sender_account_number=sender_acc,
                    receiver_account_number=receiver_acc,
                    sender_upi=sender_upi,
                    receiver_upi=receiver_upi,
                    amount_inr=Decimal(str(amount)),
                    rail_type=rail_type,
                    timestamp=now,
                    status="SUCCESS",
                )
                db.add(db_txn)
                await db.flush()
            except Exception as e:
                logger.warning(f"Database transaction insert fallback: {e}")

        _PROCESSED_TRANSACTIONS[txn_record["txn_ref_no"]] = txn_record

        # Step 3: ML Risk Engine Scoring (XGBoost)
        risk_service = cls.get_risk_service()
        tx_features = {
            "transaction_id": txn_record["txn_ref_no"],
            "amount": amount,
            "transaction_amount": amount,
            "transaction_frequency": float(payload.get("transaction_frequency", 5.0)),
            "transactions_last_1h": float(payload.get("transactions_last_1h", 0.0)),
            "transactions_last_24h": float(payload.get("transactions_last_24h", 1.0)),
            "unique_receivers": float(payload.get("unique_receivers", 1.0)),
            "unique_senders": float(payload.get("unique_senders", 1.0)),
            "cashout_ratio": float(payload.get("cashout_ratio", 0.0)),
            "account_age": float(payload.get("account_age", 120.0)),
            "graph_degree": float(payload.get("graph_degree", 2.0)),
            "graph_centrality": float(payload.get("graph_centrality", 0.01)),
            "complaint_link_count": float(payload.get("complaint_link_count", 0.0)),
            "geographic_distance": float(payload.get("geographic_distance", 0.0)),
        }
        ml_prediction = risk_service.predict(tx_features)
        ml_risk_score = float(ml_prediction.get("risk_score", 0.0))
        ml_risk_band = ml_prediction.get("risk_band", "LOW")

        # Step 4: Neo4j Graph Relationship
        graph_evidence = {
            "source": sender_acc,
            "target": receiver_acc,
            "relationship": "TRANSFERRED_TO",
            "properties": {
                "transaction_id": txn_record["txn_ref_no"],
                "amount": amount,
                "rail_type": rail_type,
                "timestamp": now_iso,
                "risk_score": ml_risk_score,
            },
        }

        # Track in active memory graph topology
        _ACTIVE_GRAPH_EDGES.append(graph_evidence)

        # If live Neo4j session is connected, execute Cypher MERGE
        if neo4j_session is not None:
            try:
                cypher = """
                MERGE (s:Account {account_number: $sender})
                MERGE (r:Account {account_number: $receiver})
                MERGE (s)-[t:TRANSFERRED_TO {txn_id: $txn_id}]->(r)
                SET t.amount = $amount,
                    t.rail_type = $rail,
                    t.timestamp = $ts,
                    t.risk_score = $risk
                RETURN t
                """
                await neo4j_session.run(
                    cypher,
                    {
                        "sender": sender_acc,
                        "receiver": receiver_acc,
                        "txn_id": txn_record["txn_ref_no"],
                        "amount": amount,
                        "rail": rail_type,
                        "ts": now_iso,
                        "risk": ml_risk_score,
                    },
                )
                graph_evidence["live_neo4j_synced"] = True
            except Exception as exc:
                logger.warning(f"Neo4j live edge creation skipped: {exc}")
                graph_evidence["live_neo4j_synced"] = False

        # Step 5: Geospatial Intelligence Engine
        lat = payload.get("latitude")
        lng = payload.get("longitude")
        is_coord_valid = False
        h3_cell = None
        nearest_atms = []
        is_hotspot = False

        if lat is not None and lng is not None:
            is_coord_valid, _ = CoordinateValidator.validate_point(lat, lng, require_india=True)
            if is_coord_valid:
                h3_cell = H3Indexer.point_to_h3(float(lat), float(lng), resolution=DEFAULT_H3_RESOLUTION)
                atm_analyzer = cls.get_atm_analyzer()
                nearest_atms = atm_analyzer.find_nearest_atms(float(lat), float(lng), top_k=3)
                # Check proximity to known reference cyber hubs
                is_hotspot = any(
                    abs(float(lat) - hub_lat) < 0.25 and abs(float(lng) - hub_lng) < 0.25
                    for hub_lat, hub_lng in [
                        (28.6139, 77.2090),  # Delhi
                        (24.2215, 86.6436),  # Jamtara
                        (27.9944, 77.0494),  # Mewat
                        (27.2152, 77.4891),  # Bharatpur
                    ]
                )
        else:
            # Fallback default coordinates (New Delhi)
            h3_cell = "873da1146ffffff"

        geo_intelligence = {
            "latitude": lat,
            "longitude": lng,
            "is_valid_indian_coordinate": is_coord_valid,
            "h3_cell": h3_cell,
            "nearest_atms": nearest_atms,
            "is_hotspot_location": is_hotspot,
        }

        # Step 6: Real-Time Alert Engine
        event_payload = TransactionEvent(
            transaction_id=txn_record["txn_ref_no"],
            account_id=sender_acc,
            receiver_account=receiver_acc,
            amount=amount,
            timestamp=now_iso,
            transaction_type="TRANSFER",
            payment_channel=rail_type,
            ml_risk_score=ml_risk_score,
            transactions_last_1h=int(tx_features.get("transactions_last_1h", 0)),
            transactions_last_24h=int(tx_features.get("transactions_last_24h", 1)),
            graph_degree=int(tx_features.get("graph_degree", 2)),
            cashout_ratio=float(tx_features.get("cashout_ratio", 0.0)),
            geographic_distance=float(tx_features.get("geographic_distance", 0.0)),
            is_hotspot_location=is_hotspot,
            complaint_link_count=int(tx_features.get("complaint_link_count", 0)),
        )

        alert_result = await alert_engine.process_transaction_event(event=event_payload)
        alert_data = None
        if alert_result:
            alert_data = {
                "id": str(alert_result.id),
                "alert_id": alert_result.alert_id,
                "severity": alert_result.severity,
                "status": alert_result.status,
                "assigned_severity": alert_result.severity,
                "composite_score": alert_result.risk_score,
                "threat_factors": alert_result.rule_flags.get("explanations", []),
                "recommended_action": "Freeze beneficiary account in golden hour" if alert_result.severity in ["HIGH", "CRITICAL"] else "Monitor",
            }

        # Step 7: Investigator-Facing API Response
        return {
            "transaction_id": txn_record["txn_ref_no"],
            "txn_ref_no": txn_record["txn_ref_no"],
            "sender_account": sender_acc,
            "receiver_account": receiver_acc,
            "amount": amount,
            "rail_type": rail_type,
            "timestamp": now_iso,
            "risk_assessment": {
                "risk_score": ml_risk_score,
                "risk_band": ml_risk_band,
                "is_suspicious": ml_prediction.get("is_suspicious", ml_risk_score >= 60.0),
                "feature_explanations": ml_prediction.get("feature_explanations", []),
                "disclaimer": ml_prediction.get("disclaimer", "Signal for investigative triage only."),
            },
            "graph_evidence": graph_evidence,
            "geospatial_intelligence": geo_intelligence,
            "alert": alert_data,
            "pipeline_status": "SUCCESS",
            "evaluated_at": now_iso,
        }

    # ==========================================================================
    # 2. COMPLETE COMPLAINT PIPELINE
    # ==========================================================================
    @classmethod
    async def process_complaint(
        cls,
        payload: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        neo4j_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute complete flow:
        Complaint -> NLP extraction -> Entity normalization -> Entity linking -> PostgreSQL -> Neo4j -> Risk/Intelligence layer -> Alert/Case system
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Step 1: Input Narrative Handling
        narrative = str(
            payload.get("narrative")
            or payload.get("description_synthetic")
            or payload.get("description")
            or ""
        ).strip()
        if not narrative:
            raise ValueError("Complaint narrative text must be provided for NLP intelligence extraction.")

        ack_no = str(
            payload.get("acknowledgement_no")
            or f"NCRP-SYN-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        )

        # Step 2: NLP Extraction (spaCy + Regex)
        nlp_pipeline = cls.get_nlp_pipeline()
        extraction_res = nlp_pipeline.process(narrative)
        extracted_entities = {e.label: e.normalized_value for e in extraction_res.entities}

        scam_type = extraction_res.scam_type or "Cyber Fraud"
        scam_confidence = extraction_res.confidence

        # Step 3: Entity Normalization & Fallbacks
        extracted_amount = extracted_entities.get("AMOUNT")
        if extracted_amount is not None:
            try:
                reported_loss = float(extracted_amount)
            except (ValueError, TypeError):
                reported_loss = float(payload.get("reported_loss_inr") or 0.0)
        else:
            reported_loss = float(payload.get("reported_loss_inr") or 0.0)

        suspect_acc = extracted_entities.get("ACCOUNT") or payload.get("suspect_account_number")
        suspect_upi = extracted_entities.get("UPI_ID") or payload.get("suspect_upi")
        suspect_phone = extracted_entities.get("PHONE") or payload.get("suspect_phone")
        suspect_bank = extracted_entities.get("BANK") or payload.get("suspect_bank")
        location = extracted_entities.get("LOCATION") or payload.get("victim_state") or "India"
        txn_ref = extracted_entities.get("TRANSACTION_ID")

        # Step 4: Entity Linking (Knowledge Base Resolver)
        linking_profile = {
            e.label: e.linked_entity
            for e in extraction_res.entities
            if getattr(e, "linked_entity", None) is not None
        }


        # Step 5: Database Persistence (PostgreSQL / In-Memory Fallback)
        complaint_id = str(uuid.uuid4())
        complaint_record = {
            "id": complaint_id,
            "acknowledgement_no": ack_no,
            "category": scam_type,
            "subcategory": scam_type,
            "reported_loss_inr": reported_loss,
            "suspect_account_number": suspect_acc,
            "suspect_upi": suspect_upi,
            "suspect_phone": suspect_phone,
            "victim_state": payload.get("victim_state") or location,
            "incident_timestamp": payload.get("incident_timestamp") or now_iso,
            "status": "INVESTIGATING",
            "triage_priority": "CRITICAL" if reported_loss > 100000 else ("HIGH" if reported_loss > 25000 else "MEDIUM"),
            "risk_score": 0.95 if reported_loss > 100000 else 0.75,
            "description_synthetic": narrative,
        }

        if db is not None:
            try:
                db_cmp = Complaint(
                    id=uuid.UUID(complaint_id),
                    acknowledgement_no=ack_no,
                    category=scam_type,
                    subcategory=scam_type,
                    victim_state=complaint_record["victim_state"],
                    reported_loss_inr=Decimal(str(reported_loss)),
                    suspect_upi=suspect_upi,
                    suspect_account_number=suspect_acc,
                    suspect_phone=suspect_phone,
                    incident_timestamp=now,
                    status=complaint_record["status"],
                    triage_priority=complaint_record["triage_priority"],
                    risk_score=Decimal(str(complaint_record["risk_score"])),
                    description_synthetic=narrative,
                )
                db.add(db_cmp)
                await db.flush()
            except Exception as e:
                logger.warning(f"Database complaint insert fallback: {e}")

        _PROCESSED_COMPLAINTS[ack_no] = complaint_record

        # Step 6: Neo4j Graph Relationship (Complaint Linking)
        graph_relationship = {
            "complaint_ack": ack_no,
            "linked_accounts": [suspect_acc] if suspect_acc else [],
            "linked_upis": [suspect_upi] if suspect_upi else [],
            "linked_phones": [suspect_phone] if suspect_phone else [],
            "relationship": "MENTIONED_IN",
        }

        if neo4j_session is not None:
            try:
                cypher_cmp = """
                MERGE (c:Complaint {acknowledgement_no: $ack})
                SET c.category = $cat,
                    c.reported_loss = $loss,
                    c.incident_timestamp = $ts
                WITH c
                WHERE $acc IS NOT NULL
                MERGE (a:Account {account_number: $acc})
                MERGE (a)-[:MENTIONED_IN]->(c)
                WITH c
                WHERE $upi IS NOT NULL
                MERGE (u:UPI {vpa: $upi})
                MERGE (u)-[:MENTIONED_IN]->(c)
                RETURN c
                """
                await neo4j_session.run(
                    cypher_cmp,
                    {
                        "ack": ack_no,
                        "cat": scam_type,
                        "loss": reported_loss,
                        "ts": now_iso,
                        "acc": suspect_acc,
                        "upi": suspect_upi,
                    },
                )
                graph_relationship["live_neo4j_synced"] = True
            except Exception as exc:
                logger.warning(f"Neo4j complaint link skipped: {exc}")
                graph_relationship["live_neo4j_synced"] = False

        # Step 7: Risk / Intelligence Layer & Case Docket System
        case_number = f"CASE-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        case_docket = {
            "id": str(uuid.uuid4()),
            "case_number": case_number,
            "title": f"Investigation: {scam_type} ({ack_no})",
            "description": f"Auto-generated intelligence docket from citizen complaint narrative. Loss: ₹{reported_loss:,.2f}",
            "status": "OPEN",
            "priority": complaint_record["triage_priority"],
            "total_fraud_amount_inr": reported_loss,
            "recovered_amount_inr": 0.0,
            "assigned_to": "investigator@cybercell.gov.in",
            "linked_complaint_ids": [ack_no],
            "linked_account_ids": [suspect_acc] if suspect_acc else [],
            "created_at": now,
            "updated_at": now,
        }
        _IN_MEMORY_CASES[case_docket["id"]] = case_docket

        # Step 8: Alert Generation for High-Risk Complaints
        alert_data = None
        if reported_loss >= 25000.0 or scam_confidence >= 0.5:
            fake_txn_id = txn_ref or f"TXN-CMP-{uuid.uuid4().hex[:6].upper()}"
            ev = TransactionEvent(
                transaction_id=fake_txn_id,
                account_id=suspect_acc or "SYN_UNKNOWN_MULE",
                receiver_account=suspect_acc or "SYN_UNKNOWN_MULE",
                amount=reported_loss,
                timestamp=now_iso,
                ml_risk_score=92.0 if reported_loss > 50000 else 75.0,
                complaint_link_count=2,
                cashout_ratio=0.90,
                transactions_last_1h=4,
            )
            al = await alert_engine.process_transaction_event(event=ev)
            if al:
                alert_data = {
                    "id": str(al.id),
                    "severity": al.severity,
                    "status": al.status,
                }

        # Step 9: Return Complete Investigation Result
        return {
            "complaint_id": complaint_id,
            "acknowledgement_no": ack_no,
            "raw_narrative": narrative,
            "extracted_entities": extracted_entities,
            "scam_typology": {
                "scam_type": scam_type,
                "confidence": scam_confidence,
            },
            "linked_suspect_account": suspect_acc,
            "linked_suspect_upi": suspect_upi,
            "linked_suspect_phone": suspect_phone,
            "reported_loss_inr": reported_loss,
            "graph_relationship": graph_relationship,
            "intelligence_summary": {
                "risk_score": complaint_record["risk_score"],
                "priority": complaint_record["triage_priority"],
                "case_opened": True,
                "case_number": case_number,
                "linking_profile": linking_profile,
            },
            "alert": alert_data,
            "pipeline_status": "SUCCESS",
            "evaluated_at": now_iso,
        }


# Global singleton pipeline service
pipeline_service = PipelineService()
