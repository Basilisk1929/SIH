"""Security primitives, authentication tokens, password hashing, and role-based access control (RBAC)."""

from datetime import datetime, timedelta, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Set, Union
import uuid
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from backend.app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=True,
)


class Role(str, Enum):
    """Platform access tiers with strict role-based separation of duties."""

    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"

    @classmethod
    def normalize(cls, role_input: Union["Role", str, Any]) -> "Role":
        """Normalize case-insensitive role string or enum to canonical enum."""
        if isinstance(role_input, cls):
            return role_input
        if hasattr(role_input, "value"):
            role_input = role_input.value
        if not role_input:
            return cls.ANALYST
        cleaned = str(role_input).strip().upper()
        if cleaned.startswith("ROLE."):
            cleaned = cleaned[5:]
        for member in cls:
            if member.value == cleaned or member.name == cleaned:
                return member
        return cls.ANALYST


# In-memory revocation blacklist tracking logged out token signatures / JTIs
_REVOKED_TOKENS: Set[str] = set()


def revoke_token(token: str) -> None:
    """Add token to revocation blacklist upon logout."""
    if token:
        _REVOKED_TOKENS.add(token.strip())


def is_token_revoked(token: str) -> bool:
    """Check if token signature has been revoked/logged out."""
    return token.strip() in _REVOKED_TOKENS


def clear_revoked_tokens() -> None:
    """Test helper to reset revocation set."""
    _REVOKED_TOKENS.clear()


# --- Password Hashing & Strength Validation ---


def validate_password_strength(password: str) -> None:
    """Validate password complexity against baseline security standards.

    Requires: minimum 8 characters, at least one uppercase, one lowercase, one digit or symbol.
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password) > 128:
        raise ValueError("Password must not exceed 128 characters.")
    if password.lower() in ("password", "12345678", "admin123", "investigate", "qwerty123"):
        raise ValueError("Password is too common and easily guessable.")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against stored salted hash using bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate salted cryptographic hash for a password (bcrypt with 12 rounds)."""
    validate_password_strength(password)
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


# --- JWT Token Generation & Verification ---


def create_access_token(
    subject: str,
    role: Union[Role, str] = Role.ANALYST,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token with expiration, type, and RBAC claims."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    canonical_role = Role.normalize(str(role)).value

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": canonical_role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(
        to_encode,
        settings.get_resolved_jwt_secret(),
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str,
    role: Union[Role, str] = Role.ANALYST,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT refresh token (default: 7 days)."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    canonical_role = Role.normalize(str(role)).value

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": canonical_role,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        to_encode,
        settings.get_resolved_jwt_secret(),
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and strictly validate a JWT token, rejecting revoked or wrong-type tokens."""
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has been revoked or logged out.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.get_resolved_jwt_secret(),
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please authenticate again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type = payload.get("type", "access")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type: expected '{expected_type}', got '{token_type}'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def decode_access_token(token: str) -> Dict[str, Any]:
    """Backwards-compatible access token decoder."""
    return decode_token(token, expected_type="access")


# --- FastAPI Authorization Dependencies ---


async def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """FastAPI dependency to extract claims of currently authenticated user."""
    return decode_access_token(token)


def require_roles(allowed_roles: Union[List[Union[Role, str]], Role, str]):
    """Role-based access control (RBAC) guard factory enforcing role permissions at API layer.

    Allows specified roles, with ADMIN inherently inheriting supervisor/investigator/analyst rights.
    """
    if isinstance(allowed_roles, (Role, str)):
        roles_list = [allowed_roles]
    else:
        roles_list = list(allowed_roles)

    canonical_allowed = {Role.normalize(str(r)).value for r in roles_list}

    async def role_checker(claims: Dict[str, Any] = Depends(get_current_user_claims)) -> Dict[str, Any]:
        user_role = Role.normalize(claims.get("role", "ANALYST")).value
        # ADMIN inherits all operational permissions
        if user_role == Role.ADMIN.value or user_role in canonical_allowed:
            return claims

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Role '{user_role}' lacks required permissions ({sorted(canonical_allowed)}).",
        )

    return role_checker
