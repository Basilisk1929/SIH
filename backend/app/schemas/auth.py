"""Pydantic schemas for authentication, credentials, and user profiles."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    """Token response carrying JWT credentials."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in_seconds: int
    role: str = "ANALYST"


class RefreshTokenRequest(BaseModel):
    """Refresh token submission schema."""

    refresh_token: str = Field(..., description="Valid JWT refresh token")


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    role: str
    type: str = "access"
    jti: str
    exp: datetime


class UserLogin(BaseModel):
    """Direct JSON credentials login schema."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserCreate(BaseModel):
    """User registration schema."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    badge_number: Optional[str] = None
    department: Optional[str] = "Cyber Crime Cell / LEA"
    role: Optional[str] = "ANALYST"


class UserResponse(BaseModel):
    """Safe user profile response omitting credentials."""

    id: Optional[UUID] = None
    email: EmailStr
    full_name: str
    badge_number: Optional[str] = None
    department: str
    role: str
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LogoutResponse(BaseModel):
    """Logout confirmation response."""

    status: str = "SUCCESS"
    message: str = "Session invalidated and token revoked successfully."
