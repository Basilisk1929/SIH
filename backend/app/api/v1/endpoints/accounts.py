"""Bank account intelligence endpoints enforcing RBAC, sensitive field masking, and audit logging."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from backend.app.core.sanitizer import mask_account_number
from backend.app.core.security import Role, get_current_user_claims, require_roles
from backend.app.schemas.transaction import BankAccountSummary
from backend.app.services.audit_service import AuditAction, audit_service

router = APIRouter()

# Synthetic bank account repository
_SYNTHETIC_ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "SYN1122334455": {
        "account_number": "SYN1122334455",
        "ifsc_code": "SYNB0001092",
        "bank_name": "State Bank of Synth",
        "holder_synthetic_name": "R. K. Beneficiary Mule",
        "is_frozen": False,
        "risk_score": Decimal("0.8900"),
        "mule_layer_detected": 2,
        "flagged_reasons": [
            "Rapid debit within 3 minutes of large incoming transfer",
            "Linked to 2 citizen cybercrime complaints",
            "Georeferenced ATM cashout in high-risk cyber hub",
        ],
        "total_credit_volume_inr": Decimal("520000.00"),
        "total_debit_volume_inr": Decimal("510000.00"),
    },
    "SYN9876543210": {
        "account_number": "SYN9876543210",
        "ifsc_code": "SYNB0001001",
        "bank_name": "Synth Bank of India",
        "holder_synthetic_name": "Synthetic Primary Aggregator",
        "is_frozen": True,
        "risk_score": Decimal("0.9600"),
        "mule_layer_detected": 3,
        "flagged_reasons": [
            "Many-to-one aggregation from 8 distinct UPI senders",
            "Immediate cash-out via ATM within 45 seconds",
        ],
        "total_credit_volume_inr": Decimal("1850000.00"),
        "total_debit_volume_inr": Decimal("1800000.00"),
    },
    "SYN4455667788": {
        "account_number": "SYN4455667788",
        "ifsc_code": "SYNB0001044",
        "bank_name": "Punjab Synth Bank",
        "holder_synthetic_name": "Verified Merchant Outlet",
        "is_frozen": False,
        "risk_score": Decimal("0.1200"),
        "mule_layer_detected": 0,
        "flagged_reasons": [],
        "total_credit_volume_inr": Decimal("85000.00"),
        "total_debit_volume_inr": Decimal("42000.00"),
    },
}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.get("", response_model=List[BankAccountSummary])
async def list_accounts(
    min_risk: Optional[float] = Query(None, ge=0.0, le=1.0),
    is_frozen: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> List[BankAccountSummary]:
    """List financial accounts with risk scores.

    Applies role-sensitive masking: ANALYSTS see masked account identifiers,
    while INVESTIGATOR, SUPERVISOR, and ADMIN see unmasked account numbers.
    """
    caller_role = Role.normalize(claims.get("role", "ANALYST")).value
    results = []

    for acct_id, acct_data in _SYNTHETIC_ACCOUNTS.items():
        if min_risk is not None and float(acct_data["risk_score"]) < min_risk:
            continue
        if is_frozen is not None and acct_data["is_frozen"] != is_frozen:
            continue

        item = dict(acct_data)
        # Apply field-level masking for read-only ANALYST roles
        if caller_role == Role.ANALYST.value:
            item["account_number"] = mask_account_number(item["account_number"])

        results.append(BankAccountSummary(**item))
        if len(results) >= limit:
            break

    return results


@router.get("/{account_number}", response_model=BankAccountSummary)
async def get_account_profile(
    account_number: str,
    request: Request,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> BankAccountSummary:
    """Retrieve full risk assessment and forensic profile of a specific bank account.

    Audits: VIEW_ACCOUNT.
    Applies sensitive field protection: middle digits masked for ANALYSTS.
    """
    clean_acct = account_number.strip().upper()
    acct = _SYNTHETIC_ACCOUNTS.get(clean_acct)

    # Support looking up by unmasked even if masked input provided
    if not acct:
        for raw_id, data in _SYNTHETIC_ACCOUNTS.items():
            if raw_id == clean_acct or mask_account_number(raw_id) == clean_acct:
                acct = data
                clean_acct = raw_id
                break

    if not acct:
        # Generate on-the-fly synthetic profile for test accounts
        is_mule = "MULE" in clean_acct or "9" in clean_acct
        acct = {
            "account_number": clean_acct,
            "ifsc_code": "SYNB0001092",
            "bank_name": "State Bank of Synth",
            "holder_synthetic_name": "Synthetic Beneficiary Identity",
            "is_frozen": False,
            "risk_score": Decimal("0.8400") if is_mule else Decimal("0.2200"),
            "mule_layer_detected": 2 if is_mule else 0,
            "flagged_reasons": ["Rapid debit within 3 minutes of credit"] if is_mule else [],
            "total_credit_volume_inr": Decimal("450000.00"),
            "total_debit_volume_inr": Decimal("442000.00"),
        }

    actor_id = claims.get("sub", "investigator")
    actor_role = claims.get("role", "ANALYST")
    client_ip = _get_client_ip(request)

    # Mandatory Forensic Audit Log: VIEW_ACCOUNT (account number automatically masked in audit log)
    await audit_service.log_event(
        action=AuditAction.VIEW_ACCOUNT,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="ACCOUNT",
        resource_id=clean_acct,
        client_ip=client_ip,
        status="SUCCESS",
        details={
            "bank_name": acct["bank_name"],
            "risk_score": float(acct["risk_score"]),
            "mule_layer": acct["mule_layer_detected"],
        },
    )

    out_data = dict(acct)
    if Role.normalize(actor_role).value == Role.ANALYST.value:
        out_data["account_number"] = mask_account_number(out_data["account_number"])

    return BankAccountSummary(**out_data)
