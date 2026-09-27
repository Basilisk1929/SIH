"""Investigative Case Management API endpoints enforcing RBAC, workflow, and forensic audit logging."""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.rate_limit import rate_limit
from backend.app.core.security import Role, get_current_user_claims, require_roles
from backend.app.db.session import get_db_optional
from backend.app.schemas.case import (
    CaseAssignRequest,
    CaseCloseRequest,
    CaseCreate,
    CaseDetailResponse,
    CaseEvidenceCreate,
    CaseEvidenceResponse,
    CaseExportResponse,
    CaseFromAlertCreate,
    CaseListResponse,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseResolveRequest,
    CaseResponse,
    CaseStatsResponse,
    CaseTimelineEventResponse,
    CaseUpdate,
)
from backend.app.services.case_service import CaseService, case_service

logger = logging.getLogger("cases.api")
router = APIRouter()

# Reference memory store alias for full backward compatibility
_IN_MEMORY_CASES = CaseService._MEMORY_CASES


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
@router.post(
    "/",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
    include_in_schema=False,
)
async def create_case(
    case_in: CaseCreate,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseResponse:
    """Open a new cybercrime case docket.

    Audits: CREATE_CASE / CASE_CREATED.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)

    try:
        created = await case_service.create_case(
            case_in=case_in,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )
        return created
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Error creating case: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create case docket. The incident has been logged.",
        )


@router.post(
    "/from-alert",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def create_case_from_alert(
    payload: CaseFromAlertCreate,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseResponse:
    """Convert an intelligence alert directly into a formal case docket with attached evidence.

    Audits: CREATE_CASE, CASE_EVIDENCE_ADDED.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)

    try:
        created = await case_service.create_case_from_alert(
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )
        return created
    except KeyError as key_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(key_err),
        )
    except ValueError as val_err:
        err_msg = str(val_err)
        if "already open" in err_msg.lower() or "already linked" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=err_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )
    except Exception as exc:
        logger.error(f"Error converting alert to case: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize case from alert. The incident has been logged.",
        )


@router.get("", response_model=CaseListResponse)
@router.get("/", response_model=CaseListResponse, include_in_schema=False)
async def list_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    investigator_filter: Optional[str] = Query(None, alias="investigator"),
    severity_filter: Optional[str] = Query(None, alias="severity"),
    search_query: Optional[str] = Query(None, alias="q"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> CaseListResponse:
    """List case dockets with multi-criteria filtering, search, and pagination."""
    items, total = case_service.list_cases(
        status_filter=status_filter,
        priority_filter=priority_filter,
        investigator_filter=investigator_filter,
        severity_filter=severity_filter,
        search_query=search_query,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    return CaseListResponse(
        total=total,
        page=page,
        limit=limit,
        cases=items,
    )


@router.get("/stats", response_model=CaseStatsResponse)
async def get_case_statistics(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> CaseStatsResponse:
    """Retrieve operational dashboard counts for active cases, required actions, and investigator assignments."""
    user_id = claims.get("sub")
    return case_service.get_case_stats(user_id=user_id)


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case_by_id(
    case_id: str,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseDetailResponse:
    """Retrieve detailed case docket information by ID or case_number.

    Enforces Object-Level Authorization and logs CASE_VIEWED audit trail.
    """
    client_ip = _get_client_ip(request)
    try:
        case = await case_service.get_case(
            case_id=case_id,
            claims=claims,
            client_ip=client_ip,
            db=db,
        )
        return case
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )
    except PermissionError as perm_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(perm_err),
        )


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
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseResponse:
    """Update case status, priority, recovery amount, or assigned investigator.

    Enforces valid lifecycle transitions and forensic audit logging.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)

    case_rec = case_service._find_case_record(case_id)
    if not case_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )
    try:
        case_service.verify_case_access(claims, case_rec, write=True)
    except PermissionError as perm_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(perm_err),
        )

    try:
        updated = await case_service.update_case(
            case_id=case_id,
            update_in=case_update,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )
        return updated
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )


@router.post(
    "/{case_id}/assign",
    response_model=CaseResponse,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR]))],
)
async def assign_case(
    case_id: str,
    payload: CaseAssignRequest,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseResponse:
    """Assign or re-assign case docket to an investigator.

    Audits: CASE_ASSIGNED.
    Authorized Roles: ADMIN, SUPERVISOR.
    """
    actor_id = claims.get("sub", "supervisor")
    actor_role = claims.get("role", "SUPERVISOR")
    client_ip = _get_client_ip(request)

    try:
        updated = await case_service.assign_case(
            case_id=case_id,
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )
        return updated
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )


@router.get("/{case_id}/notes", response_model=List[CaseNoteResponse])
async def list_case_notes(
    case_id: str,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> List[CaseNoteResponse]:
    """Retrieve chronological investigation notes for a case."""
    try:
        return case_service.list_notes(case_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )


@router.post(
    "/{case_id}/notes",
    response_model=CaseNoteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def add_case_note(
    case_id: str,
    note_in: CaseNoteCreate,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseNoteResponse:
    """Append an official, immutable note to the case investigation history.

    Audits: CASE_NOTE_ADDED.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "INVESTIGATOR")
    actor_name = claims.get("full_name") or actor_id
    client_ip = _get_client_ip(request)

    try:
        note = await case_service.add_note(
            case_id=case_id,
            note_in=note_in,
            actor_id=actor_id,
            actor_role=actor_role,
            actor_name=actor_name,
            client_ip=client_ip,
            db=db,
        )
        return note
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )


@router.get("/{case_id}/evidence", response_model=List[CaseEvidenceResponse])
async def list_case_evidence(
    case_id: str,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> List[CaseEvidenceResponse]:
    """Retrieve all structured evidence items linked to a case docket."""
    try:
        return case_service.list_evidence(case_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )


@router.post(
    "/{case_id}/evidence",
    response_model=CaseEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def add_case_evidence(
    case_id: str,
    evidence_in: CaseEvidenceCreate,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseEvidenceResponse:
    """Link an existing platform intelligence item as structured case evidence.

    Audits: CASE_EVIDENCE_ADDED.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)

    try:
        ev = await case_service.add_evidence(
            case_id=case_id,
            evidence_in=evidence_in,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )
        return ev
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )


@router.get("/{case_id}/timeline", response_model=List[CaseTimelineEventResponse])
async def get_case_timeline(
    case_id: str,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> List[CaseTimelineEventResponse]:
    """Retrieve chronological, immutable timeline of investigation events backed by actual timestamps."""
    try:
        return case_service.get_timeline(case_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )


@router.post(
    "/{case_id}/resolve",
    response_model=CaseResponse,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def resolve_case_docket(
    case_id: str,
    payload: CaseResolveRequest,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseResponse:
    """Formally resolve a case docket with forensic disposition findings.

    Audits: CASE_RESOLVED.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    """
    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)

    try:
        resolved = await case_service.resolve_case(
            case_id=case_id,
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )
        return resolved
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )


@router.post(
    "/{case_id}/close",
    response_model=CaseResponse,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR]))],
)
async def close_case_docket(
    case_id: str,
    payload: CaseCloseRequest,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> CaseResponse:
    """Formally archive and close a case docket.

    Audits: CASE_CLOSED.
    Authorized Roles: ADMIN, SUPERVISOR.
    """
    actor_id = claims.get("sub", "supervisor")
    actor_role = claims.get("role", "SUPERVISOR")
    client_ip = _get_client_ip(request)

    try:
        closed = await case_service.close_case(
            case_id=case_id,
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
            db=db,
        )
        return closed
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )


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
    """Export tamper-evident forensic intelligence dossier with cryptographic SHA-256 chain-of-custody checksum.

    Audits: EXPORT_DATA / CASE_EXPORTED.
    Authorized Roles: ADMIN, SUPERVISOR, INVESTIGATOR.
    Rate Limited: 10 requests / minute.
    """
    actor_id = claims.get("sub", "officer")
    actor_role = claims.get("role", "INVESTIGATOR")
    client_ip = _get_client_ip(request)

    try:
        export_res = await case_service.export_case_dossier(
            case_id=case_id,
            actor_id=actor_id,
            actor_role=actor_role,
            client_ip=client_ip,
        )
        return export_res
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case docket '{case_id}' not found.",
        )
