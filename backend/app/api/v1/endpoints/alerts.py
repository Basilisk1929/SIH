"""FastAPI router for Real-Time Alert Engine endpoints, WebSockets, and Server-Sent Events."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse

from backend.app.alerts.broadcaster import alert_broadcaster
from backend.app.alerts.constants import ALERT_STATES, SEVERITY_LEVELS
from backend.app.alerts.engine import alert_engine
from backend.app.alerts.rate_limiter import verify_rate_limit
from backend.app.alerts.schemas import (
    AlertCreateRequest,
    AlertListResponse,
    AlertResponse,
    AlertStatsResponse,
    AlertStatusUpdateRequest,
    TransactionEvent,
)
from backend.app.services.audit_service import AuditAction, audit_service

logger = logging.getLogger("alerts.api")
router = APIRouter(tags=["Real-Time Alert Engine"])


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_or_evaluate_alert(
    request: AlertCreateRequest,
    req_http: Request,
    _rate_limit: None = Depends(verify_rate_limit),
):
    """Evaluate a transaction event against the 6 risk dimensions, deduplicate, and broadcast."""
    try:
        alert = await alert_engine.process_transaction_event(
            event=request.event,
            dedup_window_seconds=request.dedup_window_seconds,
            notes=request.notes,
        )
        return alert
    except Exception as e:
        logger.error(f"Error evaluating alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert evaluation failure: {str(e)}",
        )


@router.get("", response_model=AlertListResponse)
@router.get("/", response_model=AlertListResponse, include_in_schema=False)
def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    alert_status: Optional[str] = Query(None, alias="status", description="Filter by status (NEW, ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE)"),
    account_id: Optional[str] = Query(None, description="Filter by account number"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """List alerts with filtering, reverse-chronological sorting, and pagination."""
    if severity and severity.upper() not in SEVERITY_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid severity filter '{severity}'. Allowed: {sorted(SEVERITY_LEVELS)}",
        )
    if alert_status and alert_status.upper() not in ALERT_STATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status filter '{alert_status}'. Allowed: {sorted(ALERT_STATES)}",
        )

    return alert_engine.list_alerts(
        severity=severity,
        status=alert_status,
        account_id=account_id,
        page=page,
        limit=limit,
    )


@router.get("/stats", response_model=AlertStatsResponse)
def get_alert_statistics():
    """Retrieve operational dashboard counts by severity, status, and deduplication count."""
    return alert_engine.get_stats()


# --- Real-Time Streaming: WebSockets & Server-Sent Events (SSE) ---

@router.websocket("/ws")
async def websocket_alert_feed(websocket: WebSocket):
    """WebSocket stream emitting real-time alert creations and state updates."""
    await alert_broadcaster.connect_ws(websocket)
    try:
        while True:
            # Keep socket alive and listen for client heartbeat or ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"PONG"}')
    except WebSocketDisconnect:
        await alert_broadcaster.disconnect_ws(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        await alert_broadcaster.disconnect_ws(websocket)


@router.get("/sse")
async def sse_alert_feed(req: Request):
    """Server-Sent Events (SSE) stream for HTTP-based real-time dashboard listeners."""
    return StreamingResponse(
        alert_broadcaster.subscribe_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_by_id(alert_id: str, request: Request):
    """Retrieve a single alert by UUID or business alert_id.

    Audits: VIEW_ALERT.
    """
    alert = alert_engine.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )

    # Extract caller identity if authenticated
    actor_id = "analyst"
    actor_role = "ANALYST"
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from backend.app.core.security import decode_access_token
            claims = decode_access_token(auth_header.split(" ", 1)[1])
            actor_id = claims.get("sub", "analyst")
            actor_role = claims.get("role", "ANALYST")
        except Exception:
            pass

    client_ip = request.client.host if request.client else "127.0.0.1"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    await audit_service.log_event(
        action=AuditAction.VIEW_ALERT,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="ALERT",
        resource_id=alert.alert_id,
        client_ip=client_ip,
        status="SUCCESS",
        details={
            "severity": alert.severity,
            "composite_score": alert.risk_score,
            "status": alert.status,
        },
    )

    return alert


@router.patch("/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: str,
    update_data: AlertStatusUpdateRequest,
    req_http: Request,
    _rate_limit: None = Depends(verify_rate_limit),
):
    """Update alert workflow status (NEW, ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE)."""
    try:
        updated = await alert_engine.update_alert_status(
            alert_id_or_uuid=alert_id,
            new_status=update_data.status,
            investigator_id=update_data.investigator_id,
            resolution_notes=update_data.resolution_notes,
        )
        return updated
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
