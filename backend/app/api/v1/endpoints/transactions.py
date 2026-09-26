"""Financial transactions and risk assessment endpoints."""

from decimal import Decimal
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.risk import RiskAssessmentRequest, RiskAssessmentResponse
from backend.app.schemas.transaction import BankAccountSummary, TransactionResponse
from backend.app.services.risk_engine import RiskEngineService

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
async def list_recent_transactions(
    limit: int = Query(20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Retrieve simulated high-velocity financial transactions."""
    # Synthetic transactional feed
    synthetic_txns = []
    for i in range(limit):
        amount = 10000.0 + (i * 4500.0) % 85000.0
        synthetic_txns.append({
            "id": f"txn-syn-{1000 + i}",
            "txn_ref_no": f"UPI/4289{1000 + i}48/SYN",
            "sender_account": f"SYN{2000000000 + i}",
            "receiver_account": f"SYN{9000000000 + (i % 5)}",
            "sender_upi": f"victim_{i}@synthaxis",
            "receiver_upi": f"mule_{(i % 5) + 1}@synthaxis",
            "amount_inr": amount,
            "rail_type": "UPI" if i % 3 != 0 else "IMPS",
            "timestamp": "2024-09-15T10:15:00Z",
            "layer_depth": 1 if i % 2 == 0 else 2,
            "is_flagged_suspicious": amount > 40000.0,
            "anomaly_score": round(min(0.99, amount / 90000.0), 4),
        })
    return synthetic_txns


@router.post("/assess-risk", response_model=RiskAssessmentResponse)
async def assess_entity_risk(
    request: RiskAssessmentRequest,
) -> RiskAssessmentResponse:
    """Execute multi-factor risk scoring engine on account, UPI ID, or phone number."""
    result = await RiskEngineService.evaluate_account_risk(request)
    return result


@router.get("/accounts/{account_number}", response_model=BankAccountSummary)
async def get_account_risk_summary(
    account_number: str,
) -> BankAccountSummary:
    """Retrieve synthetic bank account metadata, mule layer level, and risk score."""
    is_mule = account_number.startswith("MULE") or "9" in account_number
    return BankAccountSummary(
        account_number=account_number,
        ifsc_code="SYNB0001092",
        bank_name="State Bank of Synth",
        holder_synthetic_name="Synthetic Beneficiary Identity",
        is_frozen=False,
        risk_score=Decimal("0.8400") if is_mule else Decimal("0.2200"),
        mule_layer_detected=2 if is_mule else 0,
        flagged_reasons=[
            "Rapid debit within 3 minutes of credit",
            "Associated with 2 NCRP reports",
        ] if is_mule else [],
        total_credit_volume_inr=Decimal("450000.00"),
        total_debit_volume_inr=Decimal("442000.00"),
    )
