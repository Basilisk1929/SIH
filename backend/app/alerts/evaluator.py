"""Rule evaluation engine for the 6 mandatory financial transaction risk factors."""

from typing import Any, Dict, List, Tuple
from backend.app.alerts.constants import (
    ALERT_TYPE_CASHOUT,
    ALERT_TYPE_COMPLAINT,
    ALERT_TYPE_COMPOSITE,
    ALERT_TYPE_GEO,
    ALERT_TYPE_GRAPH,
    ALERT_TYPE_ML_RISK,
    ALERT_TYPE_VELOCITY,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from backend.app.alerts.schemas import AlertRuleEvaluation, TransactionEvent


class AlertRuleEvaluator:
    """Evaluates transaction events across the 6 mandatory threat dimensions."""

    @classmethod
    def evaluate_ml_risk(cls, event: TransactionEvent) -> Tuple[float, Dict[str, Any], List[str]]:
        """1. Evaluate ML risk score (0-100)."""
        score = event.ml_risk_score if event.ml_risk_score is not None else 0.0
        explanations: List[str] = []
        points = 0.0

        if score >= 85.0:
            points = 30.0
            explanations.append(f"Extreme ML risk probability signal ({score:.1f}/100)")
        elif score >= 60.0:
            points = 20.0
            explanations.append(f"High ML risk probability signal ({score:.1f}/100)")
        elif score >= 30.0:
            points = 10.0
            explanations.append(f"Moderate ML risk probability signal ({score:.1f}/100)")

        triggered = points > 0.0
        details = {
            "score": score,
            "points": points,
            "triggered": triggered,
        }
        return points, details, explanations

    @classmethod
    def evaluate_velocity(cls, event: TransactionEvent) -> Tuple[float, Dict[str, Any], List[str]]:
        """2. Evaluate transaction velocity in rolling 1-hour and 24-hour windows."""
        tx_1h = event.transactions_last_1h or 0
        tx_24h = event.transactions_last_24h or 0
        explanations: List[str] = []
        points = 0.0

        # 1-hour burst evaluation
        if tx_1h >= 8:
            points += 20.0
            explanations.append(f"Extreme 1-hour transaction burst ({tx_1h} transactions in 60 min)")
        elif tx_1h >= 4:
            points += 12.0
            explanations.append(f"Elevated 1-hour transaction burst ({tx_1h} transactions in 60 min)")

        # 24-hour velocity evaluation
        if tx_24h >= 25:
            points += 15.0
            explanations.append(f"High-frequency 24-hour velocity ({tx_24h} transactions in 24h)")
        elif tx_24h >= 12:
            points += 8.0
            explanations.append(f"Elevated 24-hour velocity ({tx_24h} transactions in 24h)")

        points = min(25.0, points)
        triggered = points > 0.0
        details = {
            "transactions_last_1h": tx_1h,
            "transactions_last_24h": tx_24h,
            "points": points,
            "triggered": triggered,
        }
        return points, details, explanations

    @classmethod
    def evaluate_graph(cls, event: TransactionEvent) -> Tuple[float, Dict[str, Any], List[str]]:
        """3. Evaluate suspicious graph connections, degree, and counterparty dispersion."""
        degree = event.graph_degree or 0
        centrality = event.graph_centrality or 0.0
        u_recv = event.unique_receivers or 0
        u_send = event.unique_senders or 0
        explanations: List[str] = []
        points = 0.0

        # Degree & centrality
        if degree >= 25:
            points += 15.0
            explanations.append(f"Elevated multigraph connectivity (degree: {degree})")
        elif degree >= 12:
            points += 8.0
            explanations.append(f"Moderate multigraph connectivity (degree: {degree})")

        if centrality >= 0.04:
            points += 10.0
            explanations.append(f"High network graph centrality ({centrality:.3f})")

        # Fan-in / Fan-out dispersion
        if u_recv >= 10:
            points += 12.0
            explanations.append(f"Rapid one-to-many fan-out pattern ({u_recv} distinct receivers in 24h)")
        elif u_send >= 10:
            points += 12.0
            explanations.append(f"Rapid many-to-one fan-in pattern ({u_send} distinct senders in 24h)")

        points = min(25.0, points)
        triggered = points > 0.0
        details = {
            "graph_degree": degree,
            "graph_centrality": centrality,
            "unique_receivers": u_recv,
            "unique_senders": u_send,
            "points": points,
            "triggered": triggered,
        }
        return points, details, explanations

    @classmethod
    def evaluate_cashout(cls, event: TransactionEvent) -> Tuple[float, Dict[str, Any], List[str]]:
        """4. Evaluate rapid cash-out and ATM drainage heuristics."""
        ratio = event.cashout_ratio or 0.0
        pat_type = (event.pattern_type or "").upper()
        txn_type = (event.transaction_type or "").upper()
        amt = event.amount or 0.0
        explanations: List[str] = []
        points = 0.0

        if ratio >= 0.85:
            points += 25.0
            explanations.append(f"Critical cashout ratio ({ratio * 100:.1f}% cumulative funds withdrawn via cash/ATM)")
        elif ratio >= 0.65:
            points += 15.0
            explanations.append(f"High cashout ratio ({ratio * 100:.1f}% cumulative funds withdrawn via cash/ATM)")

        if pat_type == "RAPID_CASHOUT" or (txn_type == "CASH_OUT" and amt >= 20000.0):
            points += 15.0
            explanations.append(f"Direct cashout transaction executed (₹{amt:,.2f})")

        points = min(30.0, points)
        triggered = points > 0.0
        details = {
            "cashout_ratio": ratio,
            "pattern_type": pat_type,
            "transaction_type": txn_type,
            "points": points,
            "triggered": triggered,
        }
        return points, details, explanations

    @classmethod
    def evaluate_geographic(cls, event: TransactionEvent) -> Tuple[float, Dict[str, Any], List[str]]:
        """5. Evaluate geographic distance anomalies and cyber hotspot presence."""
        dist = event.geographic_distance or 0.0
        is_hotspot = bool(event.is_hotspot_location)
        loc_name = event.location_name or "Unknown Location"
        explanations: List[str] = []
        points = 0.0

        # Physical distance
        if dist >= 1000.0:
            points += 15.0
            explanations.append(f"Geographic anomaly: long-distance transaction ({dist:.1f} km)")
        elif dist >= 400.0:
            points += 8.0
            explanations.append(f"Geographic anomaly: cross-state distance ({dist:.1f} km)")

        # Hotspot hub proximity
        if is_hotspot:
            points += 15.0
            explanations.append(f"Transaction georeferenced in high-risk cybercrime hub ({loc_name})")

        points = min(25.0, points)
        triggered = points > 0.0
        details = {
            "geographic_distance": dist,
            "is_hotspot_location": is_hotspot,
            "location_name": loc_name,
            "points": points,
            "triggered": triggered,
        }
        return points, details, explanations

    @classmethod
    def evaluate_complaint(cls, event: TransactionEvent) -> Tuple[float, Dict[str, Any], List[str]]:
        """6. Evaluate citizen NCRP complaint linkage."""
        cmp_count = event.complaint_link_count or 0
        has_phone = bool(event.suspect_phone)
        has_upi = bool(event.suspect_upi)
        explanations: List[str] = []
        points = 0.0

        if cmp_count >= 2:
            points = 35.0
            explanations.append(f"Account named as suspect in {cmp_count} prior citizen cybercrime complaints")
        elif cmp_count == 1:
            points = 25.0
            explanations.append("Account named as suspect in 1 prior citizen cybercrime complaint")

        if (has_phone or has_upi) and cmp_count > 0:
            points = min(40.0, points + 5.0)

        triggered = points > 0.0
        details = {
            "complaint_link_count": cmp_count,
            "suspect_phone": event.suspect_phone,
            "suspect_upi": event.suspect_upi,
            "points": points,
            "triggered": triggered,
        }
        return points, details, explanations

    @classmethod
    def evaluate(cls, event: TransactionEvent) -> AlertRuleEvaluation:
        """Run all 6 evaluations and compute composite risk score, severity, and dominant alert type."""
        ml_pts, ml_det, ml_exp = cls.evaluate_ml_risk(event)
        vel_pts, vel_det, vel_exp = cls.evaluate_velocity(event)
        grp_pts, grp_det, grp_exp = cls.evaluate_graph(event)
        csh_pts, csh_det, csh_exp = cls.evaluate_cashout(event)
        geo_pts, geo_det, geo_exp = cls.evaluate_geographic(event)
        cmp_pts, cmp_det, cmp_exp = cls.evaluate_complaint(event)

        # Base composite score sum (capped at 100.0)
        total_pts = ml_pts + vel_pts + grp_pts + csh_pts + geo_pts + cmp_pts
        composite_score = round(min(100.0, max(0.0, total_pts)), 1)

        # Merge all active explanations
        all_explanations = ml_exp + vel_exp + grp_exp + csh_exp + geo_exp + cmp_exp
        if not all_explanations:
            all_explanations.append("Routine transaction within normal baseline parameters")

        # Determine Primary Alert Type based on highest contributor
        points_map = {
            ALERT_TYPE_COMPLAINT: cmp_pts,
            ALERT_TYPE_CASHOUT: csh_pts,
            ALERT_TYPE_VELOCITY: vel_pts,
            ALERT_TYPE_ML_RISK: ml_pts,
            ALERT_TYPE_GRAPH: grp_pts,
            ALERT_TYPE_GEO: geo_pts,
        }
        primary_type = max(points_map, key=points_map.get)
        if points_map[primary_type] == 0:
            primary_type = ALERT_TYPE_ML_RISK if event.ml_risk_score else ALERT_TYPE_COMPOSITE

        # Severity Assignment
        cmp_count = event.complaint_link_count or 0
        cashout_ratio = event.cashout_ratio or 0.0
        tx_1h = event.transactions_last_1h or 0

        if (
            composite_score >= 85.0
            or cmp_count >= 2
            or (cashout_ratio >= 0.85 and tx_1h >= 4)
            or (event.ml_risk_score and event.ml_risk_score >= 90.0)
        ):
            assigned_severity = SEVERITY_CRITICAL
        elif composite_score >= 60.0 or cmp_count == 1:
            assigned_severity = SEVERITY_HIGH
        elif composite_score >= 30.0:
            assigned_severity = SEVERITY_MEDIUM
        else:
            assigned_severity = SEVERITY_LOW

        return AlertRuleEvaluation(
            ml_risk=ml_det,
            velocity=vel_det,
            graph=grp_det,
            cashout=csh_det,
            geographic=geo_det,
            complaint=cmp_det,
            total_composite_score=composite_score,
            assigned_severity=assigned_severity,
            primary_alert_type=primary_type,
            explanations=all_explanations,
        )
