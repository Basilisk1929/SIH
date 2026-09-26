"""Authentication endpoints for analyst login and identity token management."""

from datetime import timedelta
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.core.config import settings
from backend.app.core.security import (
    create_access_token,
    get_current_user_claims,
    verify_password,
    get_password_hash,
)
from backend.app.schemas.auth import Token, UserLogin

router = APIRouter()

# In-memory mock demo user store for prototype development without DB pre-population
MOCK_DEV_USERS = {
    "analyst@cybercell.gov.in": {
        "hashed_password": get_password_hash("Investigate@2024!"),
        "role": "analyst",
        "full_name": "Inspector R. Sharma",
        "badge_number": "CYB-IND-4091",
        "department": "State Cyber Cell Special Task Force",
    },
    "admin@cybercell.gov.in": {
        "hashed_password": get_password_hash("AdminSecure@2024!"),
        "role": "admin",
        "full_name": "Director V. K. Raman",
        "badge_number": "CYB-HQ-001",
        "department": "National Cyber Crime Coordination Centre (I4C)",
    },
}


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """OAuth2 password login returning a signed JWT access token.

    Note: Employs generic error response to mitigate user enumeration attacks.
    """
    user_record = MOCK_DEV_USERS.get(form_data.username)
    if not user_record or not verify_password(form_data.password, user_record["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or security credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=form_data.username,
        role=user_record["role"],
        expires_delta=access_token_expires,
        extra_claims={
            "full_name": user_record["full_name"],
            "badge": user_record["badge_number"],
            "dept": user_record["department"],
        },
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me")
async def get_current_user_profile(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    """Retrieve profile and privileges of currently authenticated analyst."""
    return {
        "email": claims.get("sub"),
        "role": claims.get("role"),
        "full_name": claims.get("full_name", "Cyber Intelligence Analyst"),
        "badge_number": claims.get("badge", "DEV-OFFICER-01"),
        "department": claims.get("dept", "Cyber Crime Unit"),
    }
