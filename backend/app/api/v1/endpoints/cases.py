"""Investigative Case Management API endpoints enforcing RBAC and forensic audit logging."""

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from backend.app.core.rate_limit import rate_limit
from backend.app.core.security import Role, get_current_user_claims, require_roles
from backend.app.schemas.case import (
    CaseCreate,
    CaseExportResponse,
    CaseListResponse,
    CaseResponse,
    CaseUpdate,
)
from backend.app.services.audit_service import AuditAction, audit_service

router = APIRouter()

# In-memory case repository for fast, reliable testing and demonstration
_IN_MEMORY_CASES: Dict[str, Dict[str, Any]] = {
    "CASE-2024-001": {
        "id": "e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101",
        "case_number": "CASE-2024-001",
        "title": "Operation Nightshade: Multi-State UPI Mule Ring",
        "description": "Cross-state cyber syndicate operating mule networks across Bharatpur, Alwar, and Jamtara.",
        "priority": "CRITICAL",
        "status": "ACTIVE",
        "total_fraud_amount_inr": 4850000.00,
        "recovered_amount_inr": 1250000.00,
        "assigned_to": "investigator@cybercell.gov.in",
        "created_by": "admin@cybercell.gov.in",
        "created_at": datetime(2024, 9, 10, 8, 30, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 9, 24, 14, 15, tzinfo=timezone.utc),
    }
}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def create_case(
    case_in: CaseCreate,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> CaseResponse:
    """Open a new cybercrime case docket.

    Audits: CREATE_CASE.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    case_num = f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now(timezone.utc)
    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)

    case_record = {
        "id": str(uuid.uuid4()),
        "case_number": case_num,
        "title": case_in.title,
        "description": case_in.description,
        "priority": case_in.priority.upper(),
        "status": "ACTIVE",
        "total_fraud_amount_inr": float(case_in.total_fraud_amount_inr),
        "recovered_amount_inr": 0.0,
        "assigned_to": case_in.assigned_to or actor_id,
        "created_by": actor_id,
        "created_at": now,
        "updated_at": now,
    }

    _IN_MEMORY_CASES[case_num] = case_record

    # Mandatory Forensic Audit Log: CREATE_CASE
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
            "assigned_to": case_record["assigned_to"],
        },
    )

    return CaseResponse(**case_record)


@router.get("", response_model=CaseListResponse)
async def list_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> CaseListResponse:
    """List case dockets with optional filtering and pagination."""
    items = list(_IN_MEMORY_CASES.values())

    if status_filter:
        stat_clean = status_filter.strip().upper()
        items = [c for c in items if c["status"] == stat_clean]

    if priority_filter:
        pri_clean = priority_filter.strip().upper()
        items = [c for c in items if c["priority"] == pri_clean]

    # Newest first
    items.sort(key=lambda x: x["created_at"], reverse=True)
    total = len(items)
    start = (page - 1) * limit
    paginated = items[start : start + limit]

    return CaseListResponse(
        total=total,
        page=page,
        limit=limit,
        cases=[CaseResponse(**c) for c in paginated],
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_by_id(
    case_id: str,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> CaseResponse:
    """Retrieve detailed case docket information by ID or case_number."""
    case = None
    if case_id in _IN_MEMORY_CASES:
        case = _IN_MEMORY_CASES[case_id]
    else:
        for c in _IN_MEMORY_CASES.values():
            if c["id"] == case_id or c["case_number"] == case_id:
                case = c
                break

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )

    return CaseResponse(**case)


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def update_case_docket(
    case_id: str,
    case_update: CaseUpdate,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> CaseResponse:
    """Update case status, priority, recovery amount, or assigned investigator.

    Audits: UPDATE_CASE.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    case = None
    target_key = None
    if case_id in _IN_MEMORY_CASES:
        case = _IN_MEMORY_CASES[case_id]
        target_key = case_id
    else:
        for k, c in _IN_MEMORY_CASES.items():
            if c["id"] == case_id or c["case_number"] == case_id:
                case = c
                target_key = k
                break

    if not case or not target_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )

    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)

    old_status = case["status"]
    update_dict = case_update.model_dump(exclude_unset=True)

    if "title" in update_dict:
        case["title"] = update_dict["title"]
    if "description" in update_dict:
        case["description"] = update_dict["description"]
    if "status" in update_dict:
        case["status"] = update_dict["status"].upper()
    if "priority" in update_dict:
        case["priority"] = update_dict["priority"].upper()
    if "recovered_amount_inr" in update_dict:
        case["recovered_amount_inr"] = float(update_dict["recovered_amount_inr"])
    if "assigned_to" in update_dict:
        case["assigned_to"] = update_dict["assigned_to"]

    case["updated_at"] = datetime.now(timezone.utc)
    _IN_MEMORY_CASES[target_key] = case

    # Mandatory Forensic Audit Log: UPDATE_CASE
    await audit_service.log_event(
        action=AuditAction.UPDATE_CASE,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="CASE",
        resource_id=case["case_number"],
        client_ip=client_ip,
        status="SUCCESS",
        details={
            "previous_status": old_status,
            "new_status": case["status"],
            "notes": case_update.investigation_notes,
            "recovered_inr": case["recovered_amount_inr"],
        },
    )

    return CaseResponse(**case)


@router.get(
    "/{case_id}/export",
    response_model=CaseExportResponse,
    dependencies=[
        Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR])),
        Depends(rate_limit(max_requests=10, window_seconds=60)),
    ],
)
async def export_case_docket(
    case_id: str,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> CaseExportResponse:
    """Export tamper-evident forensic intelligence dossier for court or inter-agency submission.

    Audits: EXPORT_DATA.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    Rate Limited: 10 requests / minute.
    """
    case = None
    if case_id in _IN_MEMORY_CASES:
        case = _IN_MEMORY_CASES[case_id]
    else:
        for c in _IN_MEMORY_CASES.values():
            if c["id"] == case_id or c["case_number"] == case_id:
                case = c
                break

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )

    actor_id = claims.get("sub", "officer")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)
    now = datetime.now(timezone.utc)
    export_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"

    # Generate cryptographic chain-of-custody checksum
    dossier_content = f"{case['case_number']}:{case['title']}:{case['status']}:{actor_id}:{now.isoformat()}"
    checksum = hashlib.sha256(dossier_content.encode("utf-8")).hexdigest()

    # Mandatory Forensic Audit Log: EXPORT_DATA
    await audit_service.log_event(
        action=AuditAction.EXPORT_DATA,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="CASE_DOSSIER",
        resource_id=case["case_number"],
        client_ip=client_ip,
        status="SUCCESS",
        details={
            "export_id": export_id,
            "chain_of_custody_hash": checksum,
            "case_number": case["case_number"],
        },
    )

    return CaseExportResponse(
        export_id=export_id,
        case_number=case["case_number"],
        exported_at=now,
        exported_by=actor_id,
        exported_role=actor_role,
        case_data=case,
        chain_of_custody_hash=checksum,
    )
