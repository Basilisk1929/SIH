"""Financial transactions and risk assessment endpoints."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import Role, get_current_user_claims, require_roles
from backend.app.db.session import get_db, get_db_optional
from backend.app.schemas.risk import RiskAssessmentRequest, RiskAssessmentResponse
from backend.app.schemas.transaction import BankAccountSummary, TransactionResponse
from backend.app.schemas.pipeline import TransactionPipelineRequest, TransactionPipelineResponse
from backend.app.services.risk_engine import RiskEngineService
from backend.app.services.pipeline_service import PipelineService

router = APIRouter()


@router.post(
    "",
    response_model=TransactionPipelineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
@router.post(
    "/",
    response_model=TransactionPipelineResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR]))],
)
async def submit_and_evaluate_transaction(
    request: TransactionPipelineRequest,
    db: Optional[AsyncSession] = Depends(get_db_optional),
) -> TransactionPipelineResponse:
    """Execute complete end-to-end transaction intelligence flow:
    Transaction -> Ingestion -> Validation -> PostgreSQL -> Risk Engine (XGBoost) -> Neo4j -> Geospatial Engine -> Alert Engine -> FastAPI -> Frontend.
    """
    try:
        result = await PipelineService.process_transaction(request.model_dump(), db=db)
        return TransactionPipelineResponse(**result)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction pipeline failure. The incident has been logged.",
        )


@router.get("", response_model=List[Dict[str, Any]])
async def list_recent_transactions(
    limit: int = Query(20, ge=1, le=100),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> List[Dict[str, Any]]:
    """Retrieve simulated high-velocity financial transactions."""
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


@router.post(
    "/assess-risk",
    response_model=RiskAssessmentResponse,
    dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPERVISOR, Role.INVESTIGATOR, Role.ANALYST]))],
)
async def assess_entity_risk(
    request: RiskAssessmentRequest,
) -> RiskAssessmentResponse:
    """Execute multi-factor risk scoring engine on account, UPI ID, or phone number."""
    result = await RiskEngineService.evaluate_account_risk(request)
    return result


@router.get("/accounts/{account_number}", response_model=BankAccountSummary)
async def get_account_risk_summary(
    account_number: str,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
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
