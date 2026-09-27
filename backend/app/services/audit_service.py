"""Forensic audit service tracking chain-of-custody, data access, and administrative actions."""

import asyncio
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Union
import uuid
from backend.app.core.sanitizer import mask_account_number, mask_sensitive_dict

logger = logging.getLogger("audit.trail")


class AuditAction(str, Enum):
    """Mandatory platform audit event classifications."""

    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    VIEW_ALERT = "VIEW_ALERT"
    VIEW_ACCOUNT = "VIEW_ACCOUNT"
    CREATE_CASE = "CREATE_CASE"
    UPDATE_CASE = "UPDATE_CASE"
    EXPORT_DATA = "EXPORT_DATA"
    ADMIN_ACTION = "ADMIN_ACTION"

    # Phase 11E Investigation Lifecycle Actions
    CASE_CREATED = "CASE_CREATED"
    CASE_VIEWED = "CASE_VIEWED"
    CASE_ASSIGNED = "CASE_ASSIGNED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_NOTE_ADDED = "CASE_NOTE_ADDED"
    CASE_STATUS_CHANGED = "CASE_STATUS_CHANGED"
    CASE_EVIDENCE_ADDED = "CASE_EVIDENCE_ADDED"
    CASE_RESOLVED = "CASE_RESOLVED"
    CASE_CLOSED = "CASE_CLOSED"
    CASE_EXPORTED = "CASE_EXPORTED"

    # Phase 11F End-to-End Simulation Actions
    DEMO_SIMULATION_STARTED = "DEMO_SIMULATION_STARTED"
    DEMO_SIMULATION_COMPLETED = "DEMO_SIMULATION_COMPLETED"
    DEMO_DATA_RESET = "DEMO_DATA_RESET"



class AuditService:
    """Manages immutable audit logging for regulatory compliance (CERT-In / DPDP Act / IT Act)."""

    def __init__(self):
        self._in_memory_audit_logs: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def log_event(
        self,
        action: Union[AuditAction, str],
        actor_id: str,
        actor_role: str,
        resource_type: str,
        resource_id: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a forensic audit log event with automatic sensitive data redaction."""
        action_str = str(action.value if isinstance(action, AuditAction) else action).upper()

        # Sanitize details payload: no passwords, tokens, full account numbers
        sanitized_details = mask_sensitive_dict(details or {})

        # Mask resource_id if it represents an account or phone number
        display_resource_id = str(resource_id)
        if resource_type.lower() == "account" and display_resource_id.startswith("SYN"):
            display_resource_id = mask_account_number(display_resource_id)

        record: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action_str,
            "actor_id": str(actor_id),
            "actor_role": str(actor_role).upper(),
            "resource_type": str(resource_type).upper(),
            "resource_id": display_resource_id,
            "client_ip": client_ip or "127.0.0.1",
            "user_agent": user_agent or "Unknown-Client",
            "status": status.upper(),
            "details": sanitized_details,
        }

        async with self._lock:
            self._in_memory_audit_logs.append(record)
            if len(self._in_memory_audit_logs) > 5000:
                self._in_memory_audit_logs.pop(0)

        # Log structured audit entry (SafeLogFormatter guarantees scrubbing)
        logger.info(
            f"AUDIT_EVENT | action={action_str} | actor={actor_id} ({actor_role}) | "
            f"resource={resource_type}:{display_resource_id} | status={status.upper()} | ip={client_ip}"
        )

        return record

    def list_logs(
        self,
        action: Optional[str] = None,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Query stored audit records with filtering and pagination."""
        records = list(self._in_memory_audit_logs)

        if action:
            act_clean = action.strip().upper()
            records = [r for r in records if r["action"] == act_clean]

        if actor_id:
            act_id_clean = actor_id.strip().lower()
            records = [r for r in records if act_id_clean in r["actor_id"].lower()]

        if resource_type:
            res_clean = resource_type.strip().upper()
            records = [r for r in records if r["resource_type"] == res_clean]

        # Reverse chronological ordering (newest first)
        records.reverse()
        total_count = len(records)
        paginated = records[offset : offset + limit]

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "logs": paginated,
        }

    def clear(self) -> None:
        """Clear logs (used for test isolation)."""
        self._in_memory_audit_logs.clear()


# Global audit singleton
audit_service = AuditService()
