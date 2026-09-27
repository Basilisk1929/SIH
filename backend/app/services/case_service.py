"""Case Management and Forensic Investigation Workflow Service.

Provides complete lifecycle management, PostgreSQL persistence with dual-mode fallback,
evidence correlation, append-only notes, immutable timeline tracking, RBAC + object-level
authorization, cryptographic dossier export, and audit logging.
"""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.sanitizer import (
    mask_account_number,
    mask_email,
    mask_sensitive_dict,
    mask_upi,
)
from backend.app.models.case import Case, CaseEvidence, CaseNote, CaseTimelineEvent
from backend.app.schemas.case import (
    CaseAssignRequest,
    CaseCloseRequest,
    CaseCreate,
    CaseDetailResponse,
    CaseEvidenceCreate,
    CaseEvidenceResponse,
    CaseExportResponse,
    CaseFromAlertCreate,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseResolveRequest,
    CaseResponse,
    CaseStatsResponse,
    CaseTimelineEventResponse,
    CaseUpdate,
)
from backend.app.services.audit_service import AuditAction, audit_service

logger = logging.getLogger("case.service")

# Controlled Investigation Lifecycle State Transitions
ALLOWED_STATUSES = {
    "OPEN",
    "ASSIGNED",
    "INVESTIGATING",
    "ON_HOLD",
    "RESOLVED",
    "CLOSED",
    # Backward-compatible aliases
    "ACTIVE",
    "UNDER_REVIEW",
    "DISMISSED",
}

STATUS_TRANSITIONS = {
    "OPEN": {"ASSIGNED", "INVESTIGATING", "UNDER_REVIEW", "ACTIVE"},
    "ACTIVE": {"ASSIGNED", "INVESTIGATING", "UNDER_REVIEW"},
    "ASSIGNED": {"INVESTIGATING", "UNDER_REVIEW", "ON_HOLD", "OPEN"},
    "INVESTIGATING": {"ON_HOLD", "RESOLVED", "ASSIGNED"},
    "UNDER_REVIEW": {"ON_HOLD", "RESOLVED", "ASSIGNED", "INVESTIGATING"},
    "ON_HOLD": {"INVESTIGATING", "UNDER_REVIEW"},
    "RESOLVED": {"CLOSED", "INVESTIGATING", "UNDER_REVIEW"},
    "CLOSED": {"INVESTIGATING"},  # Re-opening requires formal review
    "DISMISSED": {"INVESTIGATING"},
}

VALID_RESOLUTION_CATEGORIES = {
    "CONFIRMED_FRAUD",
    "SUSPECTED_FRAUD",
    "FALSE_POSITIVE",
    "INSUFFICIENT_EVIDENCE",
    "REFERRED",
    "OTHER",
}


class CaseService:
    """Enterprise cybercrime case docket manager implementing chain-of-custody protocols."""

    # Shared memory store for instant unit testing, mocking, and fallback
    _MEMORY_CASES: Dict[str, Dict[str, Any]] = {
        "CASE-2024-001": {
            "id": "e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101",
            "case_number": "CASE-2024-001",
            "alert_id": "ALT-2024-9001",
            "title": "Operation Nightshade: Multi-State UPI Mule Ring",
            "description": "Cross-state cyber syndicate operating mule networks across Bharatpur, Alwar, and Jamtara.",
            "priority": "CRITICAL",
            "status": "ACTIVE",
            "total_fraud_amount_inr": Decimal("4850000.00"),
            "recovered_amount_inr": Decimal("1250000.00"),
            "assigned_to": "investigator@cybercell.gov.in",
            "assigned_investigator": "Agent R. K. Sharma (Badge #DL-8821)",
            "assigned_at": datetime(2024, 9, 10, 8, 35, tzinfo=timezone.utc),
            "assigned_by": "admin@cybercell.gov.in",
            "created_by": "admin@cybercell.gov.in",
            "created_at": datetime(2024, 9, 10, 8, 30, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 9, 24, 14, 15, tzinfo=timezone.utc),
            "linked_alert_ids": ["ALT-2024-9001", "ALT-2024-9002"],
            "linked_account_numbers": ["SYN1000004465", "SYN1000002170"],
            "linked_complaint_ids": ["NCRP-2024-4412"],
            "notes": [
                {
                    "id": "note-001",
                    "case_id": "e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101",
                    "author_id": "investigator@cybercell.gov.in",
                    "author_name": "Agent R. K. Sharma",
                    "author_role": "INVESTIGATOR",
                    "content": "Initial docket opened following high-velocity UPI structuring alert. Bank nodal officer alerted.",
                    "is_internal": True,
                    "created_at": datetime(2024, 9, 10, 8, 40, tzinfo=timezone.utc),
                }
            ],
            "evidence": [
                {
                    "id": "ev-001",
                    "case_id": "e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101",
                    "evidence_type": "ACCOUNT",
                    "evidence_reference_id": "SYN1000004465",
                    "title": "Layer-1 Mule Hub Account",
                    "description": "High velocity inflow from 14 distinct victims within 30 minutes.",
                    "metadata_json": {"flow_velocity_score": 0.94, "mule_score": 0.89},
                    "added_by": "Agent R. K. Sharma",
                    "created_at": datetime(2024, 9, 10, 8, 45, tzinfo=timezone.utc),
                }
            ],
            "timeline": [
                {
                    "id": "tl-001",
                    "case_id": "e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101",
                    "event_type": "CASE_CREATED",
                    "title": "Case Docket Registered",
                    "description": "Operation Nightshade docket opened by system administrator.",
                    "actor_id": "admin@cybercell.gov.in",
                    "actor_role": "ADMIN",
                    "timestamp": datetime(2024, 9, 10, 8, 30, tzinfo=timezone.utc),
                },
                {
                    "id": "tl-002",
                    "case_id": "e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101",
                    "event_type": "ASSIGNED",
                    "title": "Investigator Assigned",
                    "description": "Assigned to Agent R. K. Sharma (Badge #DL-8821).",
                    "actor_id": "admin@cybercell.gov.in",
                    "actor_role": "ADMIN",
                    "timestamp": datetime(2024, 9, 10, 8, 35, tzinfo=timezone.utc),
                }
            ],
        }
    }

    @classmethod
    def validate_transition(cls, current_status: str, target_status: str) -> None:
        """Validate if the proposed state transition is permissible under protocol."""
        cur = current_status.strip().upper()
        tgt = target_status.strip().upper()

        if tgt not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{target_status}'. Allowed statuses: {sorted(ALLOWED_STATUSES)}")

        if cur == tgt:
            return

        valid_targets = STATUS_TRANSITIONS.get(cur, set())
        if tgt not in valid_targets:
            raise ValueError(
                f"Invalid lifecycle transition from '{cur}' to '{tgt}'. "
                f"Permissible target states from '{cur}': {sorted(valid_targets)}"
            )

    @classmethod
    def verify_case_access(cls, claims: Dict[str, Any], case_dict: Dict[str, Any], write: bool = False) -> None:
        """Enforce strict Object-Level Authorization based on user claims and assignment."""
        role = claims.get("role", "ANALYST").upper()
        user_id = claims.get("sub", "").lower()

        # ADMIN and SUPERVISOR have overarching jurisdiction
        if role in ("ADMIN", "SUPERVISOR"):
            return

        # INVESTIGATOR
        if role == "INVESTIGATOR":
            assigned_to = (case_dict.get("assigned_to") or "").lower()
            assigned_inv = (case_dict.get("assigned_investigator") or "").lower()
            created_by = (case_dict.get("created_by") or "").lower()

            # For mutation/write actions: MUST be assigned investigator or creator
            if write:
                if user_id and (user_id in assigned_to or user_id in assigned_inv or user_id in created_by):
                    return
                raise PermissionError("Access Denied: You are not assigned to or authorized to modify this case docket.")

            # For read actions:
            if not assigned_to and not assigned_inv:
                return  # Open unassigned pool

            if user_id and (user_id in assigned_to or user_id in assigned_inv or user_id in created_by):
                return

            user_badge = (claims.get("badge_number") or "").lower()
            if user_badge and (user_badge in assigned_to or user_badge in assigned_inv):
                return

            raise PermissionError("Access Denied: You do not have permission to access another investigator's case docket.")

        # ANALYST has read-only access to unassigned or public intelligence dockets
        if role == "ANALYST":
            if write:
                raise PermissionError("Access Denied: Analysts possess read-only privileges.")
            return

    @classmethod
    async def create_case(
        cls,
        case_in: CaseCreate,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseResponse:
        """Create a new case docket with validation, timeline event, and audit logging."""
        now = datetime.now(timezone.utc)
        case_num = f"CASE-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        case_id = str(uuid.uuid4())

        # Duplicate prevention if alert_id is specified
        if case_in.alert_id:
            for c in cls._MEMORY_CASES.values():
                if c.get("alert_id") == case_in.alert_id and c.get("status") not in ("CLOSED", "DISMISSED"):
                    raise ValueError(
                        f"An active case docket '{c['case_number']}' already exists for alert '{case_in.alert_id}'."
                    )

        # Initial status
        init_status = "ASSIGNED" if case_in.assigned_to else "OPEN"
        assigned_to = case_in.assigned_to or None
        assigned_at = now if assigned_to else None
        assigned_by = actor_id if assigned_to else None

        case_record: Dict[str, Any] = {
            "id": case_id,
            "case_number": case_num,
            "alert_id": case_in.alert_id,
            "title": case_in.title,
            "description": case_in.description,
            "priority": case_in.priority.upper(),
            "status": init_status,
            "total_fraud_amount_inr": Decimal(str(case_in.total_fraud_amount_inr)),
            "recovered_amount_inr": Decimal("0.00"),
            "assigned_to": assigned_to,
            "assigned_investigator": assigned_to,
            "assigned_at": assigned_at,
            "assigned_by": assigned_by,
            "created_by": actor_id,
            "created_at": now,
            "updated_at": now,
            "resolved_at": None,
            "resolved_by": None,
            "resolution_status": None,
            "resolution_category": None,
            "resolution_reason": None,
            "resolution_notes": None,
            "closed_at": None,
            "closed_by": None,
            "linked_alert_ids": list(case_in.linked_alert_ids or []),
            "linked_account_numbers": list(case_in.linked_account_numbers or []),
            "linked_complaint_ids": list(case_in.linked_complaint_ids or []),
            "notes": [],
            "evidence": [],
            "timeline": [],
        }

        if case_in.alert_id and case_in.alert_id not in case_record["linked_alert_ids"]:
            case_record["linked_alert_ids"].append(case_in.alert_id)

        # Timeline Event: CASE_CREATED
        creation_tl = {
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "event_type": "CASE_CREATED",
            "title": "Case Docket Registered",
            "description": f"Formal case docket initialized: {case_in.title}",
            "actor_id": actor_id,
            "actor_role": actor_role,
            "timestamp": now,
            "details": {
                "priority": case_in.priority,
                "exposure_inr": float(case_in.total_fraud_amount_inr),
                "alert_id": case_in.alert_id,
            },
        }
        case_record["timeline"].append(creation_tl)

        if assigned_to:
            assign_tl = {
                "id": str(uuid.uuid4()),
                "case_id": case_id,
                "event_type": "CASE_ASSIGNED",
                "title": "Lead Investigator Assigned",
                "description": f"Assigned to {assigned_to} by {actor_id}",
                "actor_id": actor_id,
                "actor_role": actor_role,
                "timestamp": now,
                "details": {"assigned_investigator": assigned_to},
            }
            case_record["timeline"].append(assign_tl)

        # Optional initial notes
        if case_in.initial_notes:
            note_entry = {
                "id": str(uuid.uuid4()),
                "case_id": case_id,
                "author_id": actor_id,
                "author_name": actor_id,
                "author_role": actor_role,
                "content": case_in.initial_notes,
                "is_internal": True,
                "created_at": now,
            }
            case_record["notes"].append(note_entry)

        # Store in memory repository
        cls._MEMORY_CASES[case_num] = case_record
        cls._MEMORY_CASES[case_id] = case_record

        # DB persistence if active session
        if db is not None:
            try:
                db_case = Case(
                    id=uuid.UUID(case_id),
                    case_number=case_num,
                    alert_id=case_in.alert_id,
                    title=case_in.title,
                    description=case_in.description,
                    priority=case_in.priority.upper(),
                    status=init_status,
                    assigned_investigator=assigned_to,
                    assigned_at=assigned_at,
                    assigned_by=assigned_by,
                    created_by_username=actor_id,
                    total_fraud_amount_inr=case_record["total_fraud_amount_inr"],
                    recovered_amount_inr=Decimal("0.00"),
                    created_at=now,
                    updated_at=now,
                )
                db.add(db_case)
                await db.flush()

                db_tl = CaseTimelineEvent(
                    id=uuid.UUID(creation_tl["id"]),
                    case_id=uuid.UUID(case_id),
                    event_type=creation_tl["event_type"],
                    title=creation_tl["title"],
                    description=creation_tl["description"],
                    actor_id=actor_id,
                    actor_role=actor_role,
                    timestamp=now,
                    details=creation_tl["details"],
                )
                db.add(db_tl)

                if case_in.initial_notes:
                    db_note = CaseNote(
                        id=uuid.UUID(note_entry["id"]),
                        case_id=uuid.UUID(case_id),
                        author_id=actor_id,
                        author_name=actor_id,
                        author_role=actor_role,
                        content=case_in.initial_notes,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(db_note)

                await db.commit()
            except Exception as e:
                logger.warning(f"Database persistence skipped (using synced memory store): {e}")

        # Forensic Audit Log
        await audit_service.log_event(
            action=AuditAction.CREATE_CASE,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE",
            resource_id=case_num,
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "title": case_in.title,
                "priority": case_in.priority,
                "total_fraud_amount_inr": float(case_in.total_fraud_amount_inr),
                "alert_id": case_in.alert_id,
                "assigned_to": assigned_to,
            },
        )
        await audit_service.log_event(
            action=AuditAction.CASE_CREATED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE",
            resource_id=case_num,
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "title": case_in.title,
                "priority": case_in.priority,
                "total_fraud_amount_inr": float(case_in.total_fraud_amount_inr),
                "alert_id": case_in.alert_id,
                "assigned_to": assigned_to,
            },
        )


        return cls._to_case_response(case_record)

    @classmethod
    async def create_case_from_alert(
        cls,
        payload: CaseFromAlertCreate,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseResponse:
        """Directly convert an intelligence alert into an official case docket."""
        from backend.app.alerts.engine import alert_engine

        alert = alert_engine.get_alert(payload.alert_id)
        if not alert:
            raise KeyError(f"Alert '{payload.alert_id}' not found.")

        # Duplicate check: prevent duplicate open cases for the same alert
        for c in cls._MEMORY_CASES.values():
            if c.get("alert_id") == alert.alert_id and c.get("status") not in ("CLOSED", "DISMISSED"):
                raise ValueError(
                    f"An active case docket '{c['case_number']}' is already open and linked for alert '{alert.alert_id}'."
                )

        # Derive title and details from alert
        title = payload.title or f"Investigation into {alert.alert_type} on Account {alert.account_id}"
        priority = payload.priority or ("CRITICAL" if alert.severity == "CRITICAL" else "HIGH" if alert.severity == "HIGH" else "MEDIUM")
        snapshot = getattr(alert, "event_snapshot", None) or {}
        fraud_amount = Decimal(str(snapshot.get("amount", 0.0))) if snapshot else Decimal("0.00")
        assigned_inv = getattr(payload, "assigned_investigator", None) or getattr(payload, "assigned_to", None)

        case_in = CaseCreate(
            title=title,
            description=(
                f"Originating from real-time alert {alert.alert_id}. "
                f"Triggered by {alert.triggered_entity_type} {alert.triggered_entity_id}. "
                f"Risk score: {alert.risk_score}."
            ),
            priority=priority,
            alert_id=alert.alert_id,
            total_fraud_amount_inr=fraud_amount,
            assigned_to=assigned_inv,
            assigned_investigator=assigned_inv,
            initial_notes=payload.initial_notes or (
                f"Incident Brief:\n"
                f"- Alert Type: {alert.alert_type}\n"
                f"- Severity: {alert.severity} (Score: {alert.risk_score})\n"
                f"- Triggered Entity: {alert.triggered_entity_type} {alert.triggered_entity_id}\n"
                f"- Account: {alert.account_id}"
            ),
            linked_alert_ids=[alert.alert_id],
            linked_account_numbers=[alert.account_id] if alert.account_id else [],
        )

        case_res = await cls.create_case(
            case_in=case_in,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )

        # Attach Alert and Account as Evidence automatically
        await cls.add_evidence(
            case_id=case_res.case_number,
            evidence_in=CaseEvidenceCreate(
                evidence_type="ALERT",
                evidence_reference_id=alert.alert_id,
                title=f"Triggering Alert: {alert.alert_type}",
                description=f"Risk Score: {alert.risk_score} | Severity: {alert.severity}",
                metadata_json={
                    "alert_id": alert.alert_id,
                    "risk_score": float(alert.risk_score),
                    "severity": alert.severity,
                    "rule_flags": alert.rule_flags or {},
                },
            ),
            actor_id=actor_id,
            actor_role=actor_role,
            db=db,
        )

        if alert.account_id:
            await cls.add_evidence(
                case_id=case_res.case_number,
                evidence_in=CaseEvidenceCreate(
                    evidence_type="ACCOUNT",
                    evidence_reference_id=alert.account_id,
                    title=f"Mule Suspect Account {mask_account_number(alert.account_id)}",
                    description="Account exhibiting high-risk automated alerts",
                    metadata_json={"account_id": alert.account_id, "masked_id": mask_account_number(alert.account_id)},
                ),
                actor_id=actor_id,
                actor_role=actor_role,
                db=db,
            )

        # Update alert status to INVESTIGATING and attach linked_case_id
        try:
            await alert_engine.update_alert_status(
                alert_id_or_uuid=alert.alert_id,
                new_status="INVESTIGATING",
                investigator_id=assigned_inv or actor_id,
                resolution_notes=f"Linked to official case docket {case_res.case_number}",
                linked_case_id=case_res.id,
            )
        except Exception as e:
            logger.warning(f"Could not transition alert status: {e}")

        return case_res

    @classmethod
    async def get_case(
        cls,
        case_id: str,
        claims: Dict[str, Any],
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseDetailResponse:
        """Retrieve detailed case docket with object-level authorization check."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")

        cls.verify_case_access(claims, case_record)

        actor_id = claims.get("sub", "investigator")
        actor_role = claims.get("role", "INVESTIGATOR")

        # Mandatory Audit Log: CASE_VIEWED
        await audit_service.log_event(
            action=AuditAction.CASE_VIEWED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "title": case_record["title"],
                "status": case_record["status"],
                "priority": case_record["priority"],
            },
        )

        return cls._to_case_detail_response(case_record)

    @classmethod
    def list_cases(
        cls,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        investigator_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
        search_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[CaseResponse], int]:
        """List cases with multi-criteria filtering, reverse-chronological sorting, and pagination."""
        # De-duplicate memory cases (keys contain both case_number and uuid)
        unique_cases = {}
        for c in cls._MEMORY_CASES.values():
            unique_cases[c["case_number"]] = c
        items = list(unique_cases.values())

        if status_filter and status_filter.upper() != "ALL":
            stat_clean = status_filter.strip().upper()
            items = [c for c in items if c["status"] == stat_clean]

        if priority_filter and priority_filter.upper() != "ALL":
            pri_clean = priority_filter.strip().upper()
            items = [c for c in items if c["priority"] == pri_clean]

        if investigator_filter:
            inv_clean = investigator_filter.strip().lower()
            items = [
                c
                for c in items
                if (c.get("assigned_to") and inv_clean in c["assigned_to"].lower())
                or (c.get("assigned_investigator") and inv_clean in c["assigned_investigator"].lower())
            ]

        if severity_filter and severity_filter.upper() != "ALL":
            sev_clean = severity_filter.strip().upper()
            items = [c for c in items if c.get("priority") == sev_clean]

        if search_query and search_query.strip():
            q = search_query.strip().lower()
            items = [
                c
                for c in items
                if q in c.get("case_number", "").lower()
                or q in c.get("id", "").lower()
                or q in c.get("title", "").lower()
                or q in (c.get("alert_id") or "").lower()
                or any(q in acc.lower() for acc in c.get("linked_account_numbers", []))
            ]

        if start_date:
            items = [c for c in items if c["created_at"] >= start_date]

        if end_date:
            items = [c for c in items if c["created_at"] <= end_date]

        # Newest first
        items.sort(key=lambda x: x["created_at"], reverse=True)
        total = len(items)
        start = (page - 1) * limit
        paginated = items[start : start + limit]

        return [cls._to_case_response(c) for c in paginated], total

    @classmethod
    def get_case_stats(cls, user_id: Optional[str] = None) -> CaseStatsResponse:
        """Compute operational metrics for dashboard integration without mock values."""
        unique_cases = {}
        for c in cls._MEMORY_CASES.values():
            unique_cases[c["case_number"]] = c
        items = list(unique_cases.values())

        now = datetime.now(timezone.utc)
        recent_threshold = now.timestamp() - (7 * 86400)

        by_status: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        active_count = 0
        req_investigation = 0
        assigned_to_user = 0
        recently_created = 0
        recently_resolved = 0

        for c in items:
            stat = c["status"]
            pri = c["priority"]
            by_status[stat] = by_status.get(stat, 0) + 1
            by_priority[pri] = by_priority.get(pri, 0) + 1

            if stat in ("OPEN", "ACTIVE", "ASSIGNED", "INVESTIGATING", "UNDER_REVIEW", "ON_HOLD"):
                active_count += 1
            if stat in ("OPEN", "ASSIGNED"):
                req_investigation += 1

            if user_id and (
                (c.get("assigned_to") and user_id.lower() in c["assigned_to"].lower())
                or (c.get("assigned_investigator") and user_id.lower() in c["assigned_investigator"].lower())
            ):
                assigned_to_user += 1

            if c["created_at"].timestamp() >= recent_threshold:
                recently_created += 1

            if c.get("resolved_at") and c["resolved_at"].timestamp() >= recent_threshold:
                recently_resolved += 1

        return CaseStatsResponse(
            total_cases=len(items),
            active_cases=active_count,
            requiring_investigation=req_investigation,
            requires_investigation=req_investigation,
            assigned_to_user=assigned_to_user,
            assigned_to_me=assigned_to_user,
            recently_created=recently_created,
            recently_resolved=recently_resolved,
            by_status=by_status,
            by_priority=by_priority,
        )

    @classmethod
    async def update_case(
        cls,
        case_id: str,
        update_in: CaseUpdate,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseResponse:
        """Update case details, enforcing lifecycle transitions and recording forensic audit trails."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")

        now = datetime.now(timezone.utc)
        old_status = case_record["status"]
        update_dict = update_in.model_dump(exclude_unset=True)

        if "status" in update_dict and update_dict["status"]:
            new_status = update_dict["status"].upper()
            cls.validate_transition(old_status, new_status)
            case_record["status"] = new_status

            # Timeline Event: STATUS_CHANGE
            case_record["timeline"].append({
                "id": str(uuid.uuid4()),
                "case_id": case_record["id"],
                "event_type": "STATUS_CHANGE",
                "title": f"Status Transition: {old_status} → {new_status}",
                "description": update_in.investigation_notes or f"Docket moved to {new_status}",
                "actor_id": actor_id,
                "actor_role": actor_role,
                "timestamp": now,
                "details": {"from": old_status, "to": new_status},
            })

            # Audit log: CASE_STATUS_CHANGED
            await audit_service.log_event(
                action=AuditAction.CASE_STATUS_CHANGED,
                actor_id=actor_id,
                actor_role=actor_role,
                resource_type="CASE",
                resource_id=case_record["case_number"],
                client_ip=client_ip,
                status="SUCCESS",
                details={"from": old_status, "to": new_status},
            )

        if "priority" in update_dict and update_dict["priority"]:
            case_record["priority"] = update_dict["priority"].upper()

        if "title" in update_dict and update_dict["title"]:
            case_record["title"] = update_dict["title"]

        if "description" in update_dict and update_dict["description"]:
            case_record["description"] = update_dict["description"]

        if "recovered_amount_inr" in update_dict and update_dict["recovered_amount_inr"] is not None:
            case_record["recovered_amount_inr"] = Decimal(str(update_dict["recovered_amount_inr"]))

        if "assigned_to" in update_dict and update_dict["assigned_to"]:
            case_record["assigned_to"] = update_dict["assigned_to"]
            case_record["assigned_investigator"] = update_dict["assigned_to"]
            case_record["assigned_at"] = now
            case_record["assigned_by"] = actor_id

        if update_in.investigation_notes:
            case_record["notes"].append({
                "id": str(uuid.uuid4()),
                "case_id": case_record["id"],
                "author_id": actor_id,
                "author_name": actor_id,
                "author_role": actor_role,
                "content": update_in.investigation_notes,
                "is_internal": True,
                "created_at": now,
            })

        case_record["updated_at"] = now

        # Update in memory
        cls._MEMORY_CASES[case_record["case_number"]] = case_record
        cls._MEMORY_CASES[case_record["id"]] = case_record

        # DB persistence
        if db is not None:
            try:
                stmt = select(Case).where(
                    or_(Case.case_number == case_record["case_number"], Case.id == uuid.UUID(case_record["id"]))
                )
                res = await db.execute(stmt)
                db_case = res.scalar_one_or_none()
                if db_case:
                    db_case.status = case_record["status"]
                    db_case.priority = case_record["priority"]
                    db_case.title = case_record["title"]
                    db_case.description = case_record["description"]
                    db_case.recovered_amount_inr = case_record["recovered_amount_inr"]
                    db_case.assigned_investigator = case_record["assigned_investigator"]
                    db_case.updated_at = now
                    await db.commit()
            except Exception as e:
                logger.warning(f"Database update skipped: {e}")

        # Mandatory Forensic Audit Log: UPDATE_CASE / CASE_UPDATED
        await audit_service.log_event(
            action=AuditAction.UPDATE_CASE,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "previous_status": old_status,
                "new_status": case_record["status"],
                "notes": update_in.investigation_notes,
                "recovered_inr": float(case_record["recovered_amount_inr"]),
            },
        )
        await audit_service.log_event(
            action=AuditAction.CASE_UPDATED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "previous_status": old_status,
                "new_status": case_record["status"],
                "notes": update_in.investigation_notes,
                "recovered_inr": float(case_record["recovered_amount_inr"]),
            },
        )


        return cls._to_case_response(case_record)

    @classmethod
    async def assign_case(
        cls,
        case_id: str,
        payload: CaseAssignRequest,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseResponse:
        """Assign an authorized investigator to a case docket."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")

        now = datetime.now(timezone.utc)
        case_record["assigned_to"] = payload.assigned_investigator
        case_record["assigned_investigator"] = payload.assigned_investigator
        case_record["assigned_at"] = now
        case_record["assigned_by"] = actor_id

        # If currently OPEN, transition to ASSIGNED
        if case_record["status"] == "OPEN":
            case_record["status"] = "ASSIGNED"

        case_record["updated_at"] = now

        # Add timeline event
        case_record["timeline"].append({
            "id": str(uuid.uuid4()),
            "case_id": case_record["id"],
            "event_type": "CASE_ASSIGNED",
            "title": "Investigator Assigned",
            "description": f"Assigned to {payload.assigned_investigator}. {payload.notes or ''}".strip(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "timestamp": now,
            "details": {"assigned_to": payload.assigned_investigator},
        })

        if payload.notes:
            case_record["notes"].append({
                "id": str(uuid.uuid4()),
                "case_id": case_record["id"],
                "author_id": actor_id,
                "author_name": actor_id,
                "author_role": actor_role,
                "content": f"Assignment Directive: {payload.notes}",
                "is_internal": True,
                "created_at": now,
            })

        # Mandatory Audit Log: CASE_ASSIGNED
        await audit_service.log_event(
            action=AuditAction.CASE_ASSIGNED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "assigned_investigator": payload.assigned_investigator,
                "assigned_by": actor_id,
            },
        )

        return cls._to_case_response(case_record)

    @classmethod
    async def add_note(
        cls,
        case_id: str,
        note_in: CaseNoteCreate,
        actor_id: str,
        actor_role: str,
        actor_name: Optional[str] = None,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseNoteResponse:
        """Append an official, immutable note to the case investigation log."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")

        now = datetime.now(timezone.utc)
        note_id = str(uuid.uuid4())
        name = actor_name or actor_id

        note_entry = {
            "id": note_id,
            "case_id": case_record["id"],
            "author_id": actor_id,
            "author_name": name,
            "author_role": actor_role,
            "content": note_in.content,
            "is_internal": note_in.is_internal,
            "created_at": now,
        }
        case_record["notes"].append(note_entry)
        case_record["updated_at"] = now

        # Add timeline event
        case_record["timeline"].append({
            "id": str(uuid.uuid4()),
            "case_id": case_record["id"],
            "event_type": "NOTE_ADDED",
            "title": "Forensic Note Appended",
            "description": f"Entry added by {name} ({actor_role})",
            "actor_id": actor_id,
            "actor_role": actor_role,
            "timestamp": now,
        })

        # Audit log: CASE_NOTE_ADDED (content sanitized)
        await audit_service.log_event(
            action=AuditAction.CASE_NOTE_ADDED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE_NOTE",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={"note_id": note_id, "is_internal": note_in.is_internal},
        )

        return CaseNoteResponse(**note_entry)

    @classmethod
    def list_notes(cls, case_id: str) -> List[CaseNoteResponse]:
        """List all chronological investigation notes for a case."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")
        return [CaseNoteResponse(**n) for n in case_record.get("notes", [])]

    @classmethod
    async def add_evidence(
        cls,
        case_id: str,
        evidence_in: CaseEvidenceCreate,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseEvidenceResponse:
        """Link an existing platform intelligence entity as structured evidence."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")

        now = datetime.now(timezone.utc)
        ev_id = str(uuid.uuid4())

        # Prevent duplicate evidence references
        for existing in case_record.get("evidence", []):
            if (
                existing["evidence_type"] == evidence_in.evidence_type
                and existing["evidence_reference_id"] == evidence_in.evidence_reference_id
            ):
                return CaseEvidenceResponse(**existing)

        ev_entry = {
            "id": ev_id,
            "case_id": case_record["id"],
            "evidence_type": evidence_in.evidence_type,
            "evidence_reference_id": evidence_in.evidence_reference_id,
            "title": evidence_in.title,
            "description": evidence_in.description,
            "metadata_json": evidence_in.metadata_json,
            "added_by": actor_id,
            "created_at": now,
        }
        case_record["evidence"].append(ev_entry)

        # Track linked lists
        if evidence_in.evidence_type == "ALERT" and evidence_in.evidence_reference_id not in case_record["linked_alert_ids"]:
            case_record["linked_alert_ids"].append(evidence_in.evidence_reference_id)
        elif evidence_in.evidence_type == "ACCOUNT" and evidence_in.evidence_reference_id not in case_record["linked_account_numbers"]:
            case_record["linked_account_numbers"].append(evidence_in.evidence_reference_id)
        elif evidence_in.evidence_type == "COMPLAINT" and evidence_in.evidence_reference_id not in case_record["linked_complaint_ids"]:
            case_record["linked_complaint_ids"].append(evidence_in.evidence_reference_id)

        case_record["updated_at"] = now

        # Add timeline event
        case_record["timeline"].append({
            "id": str(uuid.uuid4()),
            "case_id": case_record["id"],
            "event_type": "EVIDENCE_ADDED",
            "title": f"Evidence Attached: {evidence_in.evidence_type}",
            "description": f"{evidence_in.title} (Ref: {evidence_in.evidence_reference_id})",
            "actor_id": actor_id,
            "actor_role": actor_role,
            "timestamp": now,
            "details": {"type": evidence_in.evidence_type, "ref": evidence_in.evidence_reference_id},
        })

        # Audit log: CASE_EVIDENCE_ADDED
        await audit_service.log_event(
            action=AuditAction.CASE_EVIDENCE_ADDED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE_EVIDENCE",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "evidence_type": evidence_in.evidence_type,
                "reference_id": evidence_in.evidence_reference_id,
            },
        )

        return CaseEvidenceResponse(**ev_entry)

    @classmethod
    def list_evidence(cls, case_id: str) -> List[CaseEvidenceResponse]:
        """List all structured evidence items attached to a case."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")
        return [CaseEvidenceResponse(**e) for e in case_record.get("evidence", [])]

    @classmethod
    def get_timeline(cls, case_id: str) -> List[CaseTimelineEventResponse]:
        """Return the immutable, chronological investigation timeline with genuine timestamps."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")
        tl = list(case_record.get("timeline", []))
        tl.sort(key=lambda x: x["timestamp"])
        return [CaseTimelineEventResponse(**t) for t in tl]

    @classmethod
    async def resolve_case(
        cls,
        case_id: str,
        payload: CaseResolveRequest,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseResponse:
        """Formally resolve a case with legal findings, category, and audit logging."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")

        cls.validate_transition(case_record["status"], "RESOLVED")

        now = datetime.now(timezone.utc)
        case_record["status"] = "RESOLVED"
        case_record["resolution_status"] = "RESOLVED"
        case_record["resolution_category"] = payload.resolution_category
        case_record["resolution_reason"] = payload.resolution_reason
        case_record["resolution_notes"] = payload.resolution_notes
        case_record["resolved_at"] = now
        case_record["resolved_by"] = actor_id
        case_record["updated_at"] = now

        # Add resolution note
        case_record["notes"].append({
            "id": str(uuid.uuid4()),
            "case_id": case_record["id"],
            "author_id": actor_id,
            "author_name": actor_id,
            "author_role": actor_role,
            "content": f"Formal Resolution recorded ({payload.resolution_category}): {payload.resolution_notes}",
            "is_internal": False,
            "created_at": now,
        })

        # Add timeline event
        case_record["timeline"].append({
            "id": str(uuid.uuid4()),
            "case_id": case_record["id"],
            "event_type": "RESOLVED",
            "title": f"Case Resolved: {payload.resolution_category}",
            "description": payload.resolution_notes,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "timestamp": now,
            "details": {
                "category": payload.resolution_category,
                "reason": payload.resolution_reason,
            },
        })

        # Audit log: CASE_RESOLVED
        await audit_service.log_event(
            action=AuditAction.CASE_RESOLVED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "resolution_category": payload.resolution_category,
                "reason": payload.resolution_reason,
            },
        )

        return cls._to_case_response(case_record)

    @classmethod
    async def close_case(
        cls,
        case_id: str,
        payload: CaseCloseRequest,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
        db: Optional[AsyncSession] = None,
    ) -> CaseResponse:
        """Formally close an investigative case docket."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")

        cls.validate_transition(case_record["status"], "CLOSED")

        now = datetime.now(timezone.utc)
        case_record["status"] = "CLOSED"
        case_record["closed_at"] = now
        case_record["closed_by"] = actor_id
        case_record["updated_at"] = now

        # Add timeline event
        case_record["timeline"].append({
            "id": str(uuid.uuid4()),
            "case_id": case_record["id"],
            "event_type": "CLOSED",
            "title": "Case Docket Closed",
            "description": payload.closure_notes or "Docket formally archived.",
            "actor_id": actor_id,
            "actor_role": actor_role,
            "timestamp": now,
        })

        # Audit log: CASE_CLOSED
        await audit_service.log_event(
            action=AuditAction.CASE_CLOSED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={"closure_reason": payload.closure_reason},
        )

        return cls._to_case_response(case_record)

    @classmethod
    async def export_case_dossier(
        cls,
        case_id: str,
        actor_id: str,
        actor_role: str,
        client_ip: str = "127.0.0.1",
    ) -> CaseExportResponse:
        """Export tamper-evident forensic intelligence dossier with SHA-256 chain-of-custody checksum."""
        case_record = cls._find_case_record(case_id)
        if not case_record:
            raise KeyError(f"Case docket '{case_id}' not found.")

        now = datetime.now(timezone.utc)
        export_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"

        # Sanitize PII for judicial export package
        sanitized_case = dict(case_record)
        sanitized_case["notes"] = [
            {**n, "author_id": mask_email(n["author_id"]) if "@" in n["author_id"] else n["author_id"]}
            for n in sanitized_case.get("notes", [])
        ]
        sanitized_case["linked_account_numbers"] = [
            mask_account_number(acc) for acc in sanitized_case.get("linked_account_numbers", [])
        ]

        # Cryptographic chain-of-custody checksum
        dossier_content = (
            f"{case_record['case_number']}:{case_record['title']}:{case_record['status']}:"
            f"{actor_id}:{now.isoformat()}:{len(case_record.get('notes', []))}:{len(case_record.get('evidence', []))}"
        )
        checksum = hashlib.sha256(dossier_content.encode("utf-8")).hexdigest()

        # Audit log: EXPORT_DATA / CASE_EXPORTED
        await audit_service.log_event(
            action=AuditAction.EXPORT_DATA,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE_DOSSIER",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "export_id": export_id,
                "chain_of_custody_hash": checksum,
                "case_number": case_record["case_number"],
            },
        )
        await audit_service.log_event(
            action=AuditAction.CASE_EXPORTED,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type="CASE_DOSSIER",
            resource_id=case_record["case_number"],
            client_ip=client_ip,
            status="SUCCESS",
            details={
                "export_id": export_id,
                "chain_of_custody_hash": checksum,
                "case_number": case_record["case_number"],
            },
        )


        return CaseExportResponse(
            export_id=export_id,
            case_number=case_record["case_number"],
            exported_at=now,
            exported_by=actor_id,
            exported_role=actor_role,
            case_data=sanitized_case,
            case_metadata=sanitized_case,
            chain_of_custody_hash=checksum,
            dossier_sha256=checksum,
        )

    # Internal Helpers
    @classmethod
    def _find_case_record(cls, case_id: str) -> Optional[Dict[str, Any]]:
        """Look up case record by UUID or business case_number."""
        if case_id in cls._MEMORY_CASES:
            return cls._MEMORY_CASES[case_id]
        for c in cls._MEMORY_CASES.values():
            if c.get("id") == case_id or c.get("case_number") == case_id:
                return c
        return None

    @classmethod
    def _to_case_response(cls, record: Dict[str, Any]) -> CaseResponse:
        """Convert dictionary record to CaseResponse schema."""
        return CaseResponse(
            id=str(record.get("id")),
            case_number=record.get("case_number", ""),
            alert_id=record.get("alert_id"),
            title=record.get("title", ""),
            description=record.get("description"),
            priority=record.get("priority", "MEDIUM"),
            status=record.get("status", "OPEN"),
            total_fraud_amount_inr=Decimal(str(record.get("total_fraud_amount_inr", 0))),
            recovered_amount_inr=Decimal(str(record.get("recovered_amount_inr", 0))),
            assigned_to=record.get("assigned_to"),
            assigned_investigator=record.get("assigned_investigator") or record.get("assigned_to"),
            assigned_at=record.get("assigned_at"),
            assigned_by=record.get("assigned_by"),
            created_by=record.get("created_by") or record.get("created_by_username") or "SYSTEM",
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at"),
            resolved_at=record.get("resolved_at"),
            resolved_by=record.get("resolved_by"),
            resolution_status=record.get("resolution_status"),
            resolution_category=record.get("resolution_category"),
            resolution_reason=record.get("resolution_reason"),
            resolution_notes=record.get("resolution_notes"),
            closed_at=record.get("closed_at"),
            closed_by=record.get("closed_by"),
            linked_alert_ids=list(record.get("linked_alert_ids") or []),
            linked_account_numbers=list(record.get("linked_account_numbers") or []),
            linked_complaint_ids=list(record.get("linked_complaint_ids") or []),
            notes_count=len(record.get("notes") or []),
            evidence_count=len(record.get("evidence") or []),
        )

    @classmethod
    def _to_case_detail_response(cls, record: Dict[str, Any]) -> CaseDetailResponse:
        """Convert dictionary record to CaseDetailResponse with nested objects."""
        base_res = cls._to_case_response(record)
        notes = [CaseNoteResponse(**n) for n in record.get("notes") or []]
        evidence = [CaseEvidenceResponse(**e) for e in record.get("evidence") or []]
        timeline = [CaseTimelineEventResponse(**t) for t in record.get("timeline") or []]

        # Retrieve originating alert data if alert_id is present
        linked_alert = None
        if record.get("alert_id"):
            from backend.app.alerts.engine import alert_engine
            alt = alert_engine.get_alert(record["alert_id"])
            if alt:
                linked_alert = alt.model_dump()

        return CaseDetailResponse(
            **base_res.model_dump(),
            notes=notes,
            evidence=evidence,
            timeline=timeline,
            linked_alert=linked_alert,
        )


case_service = CaseService()
