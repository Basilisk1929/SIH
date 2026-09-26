"""Audit log query endpoints enforcing strict RBAC (ADMIN / SUPERVISOR only)."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from backend.app.core.security import Role, get_current_user_claims, require_roles
from backend.app.services.audit_service import audit_service

router = APIRouter()


@router.get(
    "/logs",
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR]))],
)
async def query_audit_trail(
    action: Optional[str] = Query(None, description="Filter by audit action (LOGIN, LOGOUT, VIEW_ALERT, etc.)"),
    actor_id: Optional[str] = Query(None, description="Filter by actor email or identifier"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (ACCOUNT, ALERT, CASE, etc.)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    """Retrieve immutable forensic chain-of-custody audit logs.

    Restricted strictly to ADMIN and SUPERVISOR roles.
    Sensitive credentials and full account numbers are guaranteed masked.
    """
    return audit_service.list_logs(
        action=action,
        actor_id=actor_id,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )
