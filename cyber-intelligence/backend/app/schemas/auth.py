"""Pydantic schemas for authentication, credentials, and user profiles."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = "Cyber Cell / LEA"
    role: Optional[str] = "analyst"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    badge_number: Optional[str] = None
    department: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
