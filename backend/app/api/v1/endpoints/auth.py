"""Authentication and identity lifecycle endpoints enforcing RBAC, rate limiting, and audit trails."""

from datetime import timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.core.config import settings
from backend.app.core.rate_limit import rate_limit
from backend.app.core.security import (
    Role,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user_claims,
    get_password_hash,
    oauth2_scheme,
    require_roles,
    revoke_token,
    verify_password,
)
from backend.app.schemas.auth import (
    LogoutResponse,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from backend.app.services.audit_service import AuditAction, audit_service

router = APIRouter()

# Synthetic demo user store containing all 4 platform roles
MOCK_DEV_USERS: Dict[str, Dict[str, Any]] = {
    "admin@cybercell.gov.in": {
        "hashed_password": get_password_hash("AdminSecure@2024!"),
        "role": Role.ADMIN.value,
        "full_name": "Director V. K. Raman",
        "badge_number": "CYB-HQ-001",
        "department": "National Cyber Crime Coordination Centre (I4C)",
    },
    "supervisor@cybercell.gov.in": {
        "hashed_password": get_password_hash("Supervisor@2024!"),
        "role": Role.SUPERVISOR.value,
        "full_name": "SP Anita Deshmukh",
        "badge_number": "CYB-MAH-010",
        "department": "Cyber Crime Supervisory Division",
    },
    "investigator@cybercell.gov.in": {
        "hashed_password": get_password_hash("Investigate@2024!"),
        "role": Role.INVESTIGATOR.value,
        "full_name": "DySP Vikram Rathore",
        "badge_number": "CYB-DEL-204",
        "department": "Special Operations / Anti-Mule Task Force",
    },
    "analyst@cybercell.gov.in": {
        "hashed_password": get_password_hash("AnalystPass@2024!"),
        "role": Role.ANALYST.value,
        "full_name": "Inspector R. Sharma",
        "badge_number": "CYB-IND-4091",
        "department": "Financial Fraud Intelligence Unit",
    },
    # Public SIH Demonstration Environment (Synthetic Accounts)
    "investigator.demo@cybershield.local": {
        "hashed_password": get_password_hash("InvestigatorDemo@2024!"),
        "role": Role.INVESTIGATOR.value,
        "full_name": "Demo Investigator (SIH Judge Access)",
        "badge_number": "SIH-INV-001",
        "department": "Mule Detection Task Force (Demo)",
    },
    "supervisor.demo@cybershield.local": {
        "hashed_password": get_password_hash("SupervisorDemo@2024!"),
        "role": Role.SUPERVISOR.value,
        "full_name": "Demo Supervisor (SIH Judge Access)",
        "badge_number": "SIH-SUP-001",
        "department": "Supervisory Oversight Division (Demo)",
    },
    "analyst.demo@cybershield.local": {
        "hashed_password": get_password_hash("AnalystDemo@2024!"),
        "role": Role.ANALYST.value,
        "full_name": "Demo Analyst (SIH Judge Access)",
        "badge_number": "SIH-ANA-001",
        "department": "Financial Intelligence Unit (Demo)",
    },
    "admin.demo@cybershield.local": {
        "hashed_password": get_password_hash("AdminDemo@2024!"),
        "role": Role.ADMIN.value,
        "full_name": "Demo Administrator (SIH Judge Access)",
        "badge_number": "SIH-ADM-001",
        "department": "System Administration (Demo)",
    },
}


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request headers or remote connection."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))])
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """OAuth2 password login returning signed JWT access and refresh tokens.

    Protected by sliding-window rate limiting (5 req/min per IP) to prevent brute-force attacks.
    """
    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")
    username = form_data.username.lower().strip()

    user_record = MOCK_DEV_USERS.get(username)
    if not user_record or not verify_password(form_data.password, user_record["hashed_password"]):
        # Log failed authentication attempt
        await audit_service.log_event(
            action=AuditAction.LOGIN,
            actor_id=username,
            actor_role="UNKNOWN",
            resource_type="AUTH",
            resource_id=username,
            client_ip=client_ip,
            user_agent=user_agent,
            status="FAILURE",
            details={"reason": "Invalid credentials provided"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or security credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue Access & Refresh Tokens
    role = user_record["role"]
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=username,
        role=role,
        expires_delta=access_token_expires,
        extra_claims={
            "full_name": user_record["full_name"],
            "badge": user_record["badge_number"],
            "dept": user_record["department"],
        },
    )
    refresh_token = create_refresh_token(subject=username, role=role)

    # Log successful authentication
    await audit_service.log_event(
        action=AuditAction.LOGIN,
        actor_id=username,
        actor_role=role,
        resource_type="AUTH",
        resource_id=username,
        client_ip=client_ip,
        user_agent=user_agent,
        status="SUCCESS",
        details={"badge": user_record["badge_number"], "dept": user_record["department"]},
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=role,
    )


@router.post("/login-json", response_model=Token, dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))])
async def login_with_json_credentials(
    request: Request,
    credentials: UserLogin,
) -> Token:
    """Alternative JSON body authentication endpoint."""
    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")
    email = credentials.email.lower().strip()

    user_record = MOCK_DEV_USERS.get(email)
    if not user_record or not verify_password(credentials.password, user_record["hashed_password"]):
        await audit_service.log_event(
            action=AuditAction.LOGIN,
            actor_id=email,
            actor_role="UNKNOWN",
            resource_type="AUTH",
            resource_id=email,
            client_ip=client_ip,
            user_agent=user_agent,
            status="FAILURE",
            details={"reason": "Invalid credentials provided"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or security credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = user_record["role"]
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=email,
        role=role,
        expires_delta=access_token_expires,
        extra_claims={
            "full_name": user_record["full_name"],
            "badge": user_record["badge_number"],
            "dept": user_record["department"],
        },
    )
    refresh_token = create_refresh_token(subject=email, role=role)

    await audit_service.log_event(
        action=AuditAction.LOGIN,
        actor_id=email,
        actor_role=role,
        resource_type="AUTH",
        resource_id=email,
        client_ip=client_ip,
        user_agent=user_agent,
        status="SUCCESS",
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=role,
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    request: Request,
) -> Token:
    """Exchange a valid Refresh Token for a new Access Token."""
    decoded = decode_token(payload.refresh_token, expected_type="refresh")
    subject = decoded.get("sub")
    role = decoded.get("role", Role.ANALYST.value)

    if not subject or subject not in MOCK_DEV_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active or valid.",
        )

    user_record = MOCK_DEV_USERS[subject]
    new_access_token = create_access_token(
        subject=subject,
        role=role,
        extra_claims={
            "full_name": user_record["full_name"],
            "badge": user_record["badge_number"],
            "dept": user_record["department"],
        },
    )

    return Token(
        access_token=new_access_token,
        refresh_token=payload.refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=role,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> LogoutResponse:
    """Revoke session token and terminate authenticated session."""
    revoke_token(token)
    actor_id = claims.get("sub", "unknown")
    actor_role = claims.get("role", "ANALYST")
    client_ip = _get_client_ip(request)

    await audit_service.log_event(
        action=AuditAction.LOGOUT,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="AUTH",
        resource_id=actor_id,
        client_ip=client_ip,
        status="SUCCESS",
    )

    return LogoutResponse(status="SUCCESS", message="Session invalidated and token revoked successfully.")


@router.get("/me")
async def get_current_user_profile(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    """Retrieve profile and assigned RBAC privileges of the active caller."""
    return {
        "email": claims.get("sub"),
        "role": claims.get("role"),
        "full_name": claims.get("full_name", "Cyber Intelligence Officer"),
        "badge_number": claims.get("badge", "OFFICER-01"),
        "department": claims.get("dept", "Cyber Crime Unit"),
    }


@router.post("/users", response_model=UserResponse, dependencies=[Depends(require_roles(Role.ADMIN))])
async def register_new_user(
    user_in: UserCreate,
    request: Request,
    admin_claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> UserResponse:
    """Create a new platform user with designated role (ADMIN permission required)."""
    email_clean = user_in.email.lower().strip()
    if email_clean in MOCK_DEV_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{email_clean}' already exists.",
        )

    canonical_role = Role.normalize(user_in.role or "ANALYST").value
    hashed_pwd = get_password_hash(user_in.password)

    MOCK_DEV_USERS[email_clean] = {
        "hashed_password": hashed_pwd,
        "role": canonical_role,
        "full_name": user_in.full_name,
        "badge_number": user_in.badge_number or "UNASSIGNED",
        "department": user_in.department or "Cyber Crime Cell",
    }

    # Audit the admin action
    await audit_service.log_event(
        action=AuditAction.ADMIN_ACTION,
        actor_id=admin_claims.get("sub", "admin"),
        actor_role=admin_claims.get("role", "ADMIN"),
        resource_type="USER",
        resource_id=email_clean,
        client_ip=_get_client_ip(request),
        status="SUCCESS",
        details={"created_role": canonical_role, "full_name": user_in.full_name},
    )

    return UserResponse(
        email=email_clean,
        full_name=user_in.full_name,
        badge_number=user_in.badge_number,
        department=user_in.department or "Cyber Crime Cell",
        role=canonical_role,
        is_active=True,
    )
