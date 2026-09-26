"""Core Real-Time Alert Engine orchestrating threat evaluations, deduplication, and persistence."""

from datetime import datetime, timezone
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional

from backend.app.alerts.broadcaster import alert_broadcaster
from backend.app.alerts.constants import (
    ALERT_DISCLAIMER,
    ALERT_STATES,
    DEFAULT_DEDUP_WINDOW_SECONDS,
    SEVERITY_LEVELS,
    STATE_NEW,
    VALID_STATE_TRANSITIONS,
)
from backend.app.alerts.deduplicator import AlertDeduplicator
from backend.app.alerts.evaluator import AlertRuleEvaluator
from backend.app.alerts.schemas import (
    AlertListResponse,
    AlertResponse,
    AlertStatsResponse,
    TransactionEvent,
)

logger = logging.getLogger("alerts.engine")


class RealTimeAlertEngine:
    """Consumes transaction events, executes 6-factor evaluations, deduplicates, and broadcasts."""

    def __init__(self, dedup_window_seconds: int = DEFAULT_DEDUP_WINDOW_SECONDS):
        self.deduplicator = AlertDeduplicator(default_window_seconds=dedup_window_seconds)
        self.broadcaster = alert_broadcaster
        self._lock = threading.Lock()
        # In-memory storage for rapid millisecond lookup and testing
        self._alerts_by_id: Dict[str, AlertResponse] = {}
        self._alerts_by_business_id: Dict[str, str] = {}  # alert_id -> id (UUID string)
        self._deduplicated_suppressions: int = 0

    @staticmethod
    def generate_alert_id() -> str:
        """Create a human-readable, chronological alert identifier."""
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_uuid = uuid.uuid4().hex[:8].upper()
        return f"ALT_{now_str}_{short_uuid}"

    async def process_transaction_event(
        self,
        event: TransactionEvent,
        dedup_window_seconds: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> AlertResponse:
        """Evaluate a transaction event across the 6 factors, deduplicate, and broadcast."""
        # 1. Evaluate the 6 threat factors
        eval_result = AlertRuleEvaluator.evaluate(event)

        # 2. Check Deduplication Window
        window = dedup_window_seconds if dedup_window_seconds is not None else self.deduplicator.default_window_seconds
        is_dup, orig_alert_id, dup_count = self.deduplicator.check_and_register(
            account_id=event.account_id,
            transaction_id=event.transaction_id,
            alert_type=eval_result.primary_alert_type,
            window_seconds=window,
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        if is_dup and orig_alert_id:
            # Duplicate detected within window: suppress new alert and increment count
            with self._lock:
                self._deduplicated_suppressions += 1
                uuid_id = self._alerts_by_business_id.get(orig_alert_id)
                if uuid_id and uuid_id in self._alerts_by_id:
                    existing = self._alerts_by_id[uuid_id]
                    # Update duplicate count and timestamp
                    updated = existing.model_copy(
                        update={
                            "duplicate_count": dup_count,
                            "is_deduplicated": True,
                            "updated_at": now_iso,
                        }
                    )
                    self._alerts_by_id[uuid_id] = updated
                    logger.info(
                        f"Duplicate alert suppressed for account={event.account_id}, txn={event.transaction_id}. "
                        f"Count: {dup_count}, AlertID: {orig_alert_id}"
                    )
                    return updated

        # 3. Create New Alert
        sys_id = str(uuid.uuid4())
        business_alert_id = self.generate_alert_id()

        rule_flags_payload = eval_result.model_dump()
        if notes:
            rule_flags_payload["investigator_notes"] = notes

        alert = AlertResponse(
            id=sys_id,
            alert_id=business_alert_id,
            alert_type=eval_result.primary_alert_type,
            severity=eval_result.assigned_severity,
            status=STATE_NEW,
            risk_score=eval_result.total_composite_score,
            triggered_entity_type="TRANSACTION",
            triggered_entity_id=event.transaction_id,
            account_id=event.account_id,
            transaction_id=event.transaction_id,
            rule_flags=rule_flags_payload,
            is_deduplicated=False,
            duplicate_count=1,
            created_at=now_iso,
            updated_at=now_iso,
            disclaimer=ALERT_DISCLAIMER,
        )

        # 4. Bind in Deduplicator and Store
        self.deduplicator.bind_alert_id(
            account_id=event.account_id,
            transaction_id=event.transaction_id,
            alert_type=eval_result.primary_alert_type,
            alert_id=business_alert_id,
        )

        with self._lock:
            self._alerts_by_id[sys_id] = alert
            self._alerts_by_business_id[business_alert_id] = sys_id

        # 5. Broadcast in Real-Time to WebSockets and SSE
        await self.broadcaster.broadcast({
            "event_type": "ALERT_CREATED",
            "alert": alert.model_dump(),
        })

        logger.info(
            f"Alert emitted: {alert.alert_id} | Severity: {alert.severity} | Score: {alert.risk_score} | "
            f"Type: {alert.alert_type} | Account: {alert.account_id}"
        )

        return alert

    def get_alert(self, alert_id_or_uuid: str) -> Optional[AlertResponse]:
        """Retrieve single alert by UUID or business alert_id."""
        query = alert_id_or_uuid.strip()
        with self._lock:
            if query in self._alerts_by_id:
                return self._alerts_by_id[query]
            if query in self._alerts_by_business_id:
                uuid_id = self._alerts_by_business_id[query]
                return self._alerts_by_id.get(uuid_id)
        return None

    def list_alerts(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        account_id: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> AlertListResponse:
        """List alerts with filtering, reverse-chronological sorting, and pagination."""
        with self._lock:
            alerts = list(self._alerts_by_id.values())

        # Filtering
        if severity:
            sev_clean = severity.strip().upper()
            alerts = [a for a in alerts if a.severity == sev_clean]
        if status:
            stat_clean = status.strip().upper()
            alerts = [a for a in alerts if a.status == stat_clean]
        if account_id:
            acc_clean = account_id.strip()
            alerts = [a for a in alerts if a.account_id == acc_clean]

        # Sort newest first, then highest risk_score
        alerts.sort(key=lambda a: (a.created_at, a.risk_score), reverse=True)

        total = len(alerts)
        total_pages = max(1, (total + limit - 1) // limit)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = alerts[start_idx:end_idx]

        return AlertListResponse(
            items=paginated_items,
            total=total,
            page=page,
            limit=limit,
            pages=total_pages,
        )

    async def update_alert_status(
        self,
        alert_id_or_uuid: str,
        new_status: str,
        investigator_id: Optional[str] = None,
        resolution_notes: Optional[str] = None,
    ) -> AlertResponse:
        """Transition alert workflow state with validation and real-time broadcast."""
        status_clean = new_status.strip().upper()
        if status_clean not in ALERT_STATES:
            raise ValueError(f"Invalid alert state: {new_status}. Allowed: {sorted(ALERT_STATES)}")

        alert = self.get_alert(alert_id_or_uuid)
        if alert is None:
            raise KeyError(f"Alert not found: {alert_id_or_uuid}")

        current_status = alert.status
        allowed_transitions = VALID_STATE_TRANSITIONS.get(current_status, set())
        if status_clean != current_status and status_clean not in allowed_transitions:
            raise ValueError(
                f"Illegal state transition from {current_status} to {status_clean}. "
                f"Valid target states: {sorted(allowed_transitions)}"
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        updated = alert.model_copy(
            update={
                "status": status_clean,
                "investigator_id": investigator_id or alert.investigator_id,
                "resolution_notes": resolution_notes or alert.resolution_notes,
                "updated_at": now_iso,
            }
        )

        with self._lock:
            self._alerts_by_id[updated.id] = updated

        # Broadcast state update to connected dashboards
        await self.broadcaster.broadcast({
            "event_type": "ALERT_STATUS_UPDATED",
            "alert_id": updated.alert_id,
            "old_status": current_status,
            "new_status": status_clean,
            "investigator_id": updated.investigator_id,
            "updated_at": now_iso,
        })

        logger.info(
            f"Alert {updated.alert_id} state transition: {current_status} -> {status_clean} by {investigator_id}"
        )
        return updated

    def get_stats(self) -> AlertStatsResponse:
        """Calculate dashboard operational metrics."""
        with self._lock:
            alerts = list(self._alerts_by_id.values())
            suppressions = self._deduplicated_suppressions

        sev_counts = {s: 0 for s in SEVERITY_LEVELS}
        stat_counts = {st: 0 for st in ALERT_STATES}

        for a in alerts:
            sev_counts[a.severity] = sev_counts.get(a.severity, 0) + 1
            stat_counts[a.status] = stat_counts.get(a.status, 0) + 1

        return AlertStatsResponse(
            total_alerts=len(alerts),
            by_severity=sev_counts,
            by_status=stat_counts,
            deduplicated_suppressions=suppressions,
        )

    def clear(self) -> None:
        """Reset internal alert repository and deduplication cache."""
        with self._lock:
            self._alerts_by_id.clear()
            self._alerts_by_business_id.clear()
            self._deduplicated_suppressions = 0
        self.deduplicator.clear()


# Global singleton engine instance
alert_engine = RealTimeAlertEngine()
