"""Real-time financial transaction alert engine package."""

from backend.app.alerts.broadcaster import AlertBroadcaster, alert_broadcaster
from backend.app.alerts.constants import (
    ALERT_DISCLAIMER,
    ALERT_STATES,
    ALERT_TYPE_CASHOUT,
    ALERT_TYPE_COMPLAINT,
    ALERT_TYPE_COMPOSITE,
    ALERT_TYPE_GEO,
    ALERT_TYPE_GRAPH,
    ALERT_TYPE_ML_RISK,
    ALERT_TYPE_VELOCITY,
    DEFAULT_DEDUP_WINDOW_SECONDS,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LEVELS,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    STATE_ACKNOWLEDGED,
    STATE_FALSE_POSITIVE,
    STATE_INVESTIGATING,
    STATE_NEW,
    STATE_RESOLVED,
    VALID_STATE_TRANSITIONS,
)
from backend.app.alerts.deduplicator import AlertDeduplicator
from backend.app.alerts.engine import RealTimeAlertEngine, alert_engine
from backend.app.alerts.evaluator import AlertRuleEvaluator
from backend.app.alerts.rate_limiter import InMemoryRateLimiter, rate_limiter, verify_rate_limit
from backend.app.alerts.schemas import (
    AlertCreateRequest,
    AlertListResponse,
    AlertResponse,
    AlertRuleEvaluation,
    AlertStatsResponse,
    AlertStatusUpdateRequest,
    TransactionEvent,
)

__all__ = [
    "alert_engine",
    "RealTimeAlertEngine",
    "AlertRuleEvaluator",
    "AlertDeduplicator",
    "AlertBroadcaster",
    "alert_broadcaster",
    "InMemoryRateLimiter",
    "rate_limiter",
    "verify_rate_limit",
    "TransactionEvent",
    "AlertRuleEvaluation",
    "AlertCreateRequest",
    "AlertStatusUpdateRequest",
    "AlertResponse",
    "AlertListResponse",
    "AlertStatsResponse",
    "SEVERITY_LOW",
    "SEVERITY_MEDIUM",
    "SEVERITY_HIGH",
    "SEVERITY_CRITICAL",
    "SEVERITY_LEVELS",
    "STATE_NEW",
    "STATE_ACKNOWLEDGED",
    "STATE_INVESTIGATING",
    "STATE_RESOLVED",
    "STATE_FALSE_POSITIVE",
    "ALERT_STATES",
    "VALID_STATE_TRANSITIONS",
    "ALERT_DISCLAIMER",
    "DEFAULT_DEDUP_WINDOW_SECONDS",
]
