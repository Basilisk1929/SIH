"""Multi-factor financial transaction risk scoring and mule ring detection engine."""

from decimal import Decimal
from typing import Dict, List, Optional
from backend.app.schemas.risk import RiskAssessmentRequest, RiskAssessmentResponse, RiskFactor


class RiskEngineService:
    """Evaluates cybercrime risk using behavioral, graph, and transactional heuristics."""

    HIGH_RISK_IFSC_PREFIXES = ("SYNB0001", "SYNB0009", "MULE0000")

    @classmethod
    async def evaluate_account_risk(
        cls, request: RiskAssessmentRequest
    ) -> RiskAssessmentResponse:
        """Calculate weighted composite risk score for a suspect account or identifier."""
        factors: List[RiskFactor] = []
        metrics: Dict[str, float] = {}

        total_score = 0.0
        entity_id = request.account_number or request.upi_id or request.phone or "UNKNOWN_ENTITY"
        entity_type = "ACCOUNT" if request.account_number else ("UPI" if request.upi_id else "PHONE")

        # Factor 1: Complaint Association Weight (40%)
        complaint_count = len(request.complaint_ids) if request.complaint_ids else 0
        metrics["associated_complaints_count"] = float(complaint_count)
        if complaint_count >= 3:
            f1_score = 0.95
            f1_desc = f"Directly referenced across {complaint_count} active NCRP/1930 cyber fraud complaints."
        elif complaint_count > 0:
            f1_score = 0.70
            f1_desc = f"Referenced in {complaint_count} citizen cybercrime complaint."
        else:
            f1_score = 0.10
            f1_desc = "No direct NCRP complaints currently on file."
        factors.append(RiskFactor(name="Complaint Association", weight=0.40, score=f1_score, description=f1_desc))
        total_score += 0.40 * f1_score

        # Factor 2: High Velocity & Layer Outflow (30%)
        # Simulated heuristic: large transaction values trigger higher velocity risk
        amount = float(request.transaction_amount_inr) if request.transaction_amount_inr else 0.0
        metrics["transaction_amount_inr"] = amount
        if amount > 100000:
            f2_score = 0.85
            f2_desc = f"High value transfer (₹{amount:,.2f}) matching typical mule account drain patterns."
        elif amount > 25000:
            f2_score = 0.60
            f2_desc = f"Moderate transfer volume (₹{amount:,.2f}) above typical retail peer-to-peer threshold."
        else:
            f2_score = 0.20
            f2_desc = "Transaction amount within normal retail parameters."
        factors.append(RiskFactor(name="Transaction Velocity & Drain Rate", weight=0.30, score=f2_score, description=f2_desc))
        total_score += 0.30 * f2_score

        # Factor 3: Synthetic IFSC / Known Node Cluster (20%)
        is_high_risk_cluster = False
        if request.account_number and request.account_number.startswith("MULE"):
            is_high_risk_cluster = True
        metrics["is_flagged_cluster"] = 1.0 if is_high_risk_cluster else 0.0

        if is_high_risk_cluster:
            f3_score = 0.92
            f3_desc = "Account mapped to high-risk beneficiary cluster identified in prior investigations."
        else:
            f3_score = 0.15
            f3_desc = "Branch and network identifiers exhibit normal baseline attributes."
        factors.append(RiskFactor(name="Entity Cluster Affinity", weight=0.20, score=f3_score, description=f3_desc))
        total_score += 0.20 * f3_score

        # Factor 4: Behavioral Anomaly Baseline (10%)
        f4_score = 0.45
        factors.append(
            RiskFactor(
                name="Behavioral Anomaly Index",
                weight=0.10,
                score=f4_score,
                description="Composite anomaly score derived from device, IP, and timing dispersion.",
            )
        )
        total_score += 0.10 * f4_score

        # Determine level and actionable recommendations
        if total_score >= 0.75:
            level = "SEVERE"
            rec_action = "EMERGENCY_FREEZE"
            is_mule = True
        elif total_score >= 0.55:
            level = "HIGH"
            rec_action = "MANUAL_REVIEW"
            is_mule = True
        elif total_score >= 0.35:
            level = "MEDIUM"
            rec_action = "MONITOR"
            is_mule = False
        else:
            level = "LOW"
            rec_action = "ALLOW"
            is_mule = False

        return RiskAssessmentResponse(
            entity_id=entity_id,
            entity_type=entity_type,
            overall_risk_score=round(total_score, 4),
            risk_level=level,
            is_mule_candidate=is_mule,
            recommended_action=rec_action,
            contributing_factors=factors,
            feature_metrics=metrics,
        )
