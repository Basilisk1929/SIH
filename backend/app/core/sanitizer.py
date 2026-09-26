"""Sensitive data protection, forensic masking, and log sanitization utilities."""

import re
from typing import Any, Dict, List, Union


def mask_account_number(account: str | None) -> str:
    """Mask middle digits/characters of a bank account number.

    Example: 'SYN1122334455' -> 'SYN******4455'
             '123456789012'  -> '1234****9012'
    """
    if not account:
        return ""
    account_str = str(account).strip()
    length = len(account_str)
    if length <= 6:
        return "*" * length
    prefix_len = 3 if account_str.startswith("SYN") else min(4, length // 3)
    suffix_len = min(4, length // 3)
    masked_count = max(4, length - prefix_len - suffix_len)
    return f"{account_str[:prefix_len]}{'*' * masked_count}{account_str[-suffix_len:]}"


def mask_phone(phone: str | None) -> str:
    """Mask middle digits of an Indian phone number (+91 or 10 digits).

    Example: '+919876543210' -> '+91******3210'
             '9876543210'    -> '98****3210'
    """
    if not phone:
        return ""
    phone_str = str(phone).strip()
    if phone_str.startswith("+91"):
        digits = phone_str[3:]
        if len(digits) >= 6:
            return f"+91{'*' * (len(digits) - 4)}{digits[-4:]}"
        return f"+91{'*' * len(digits)}"
    elif len(phone_str) >= 6:
        return f"{phone_str[:2]}{'*' * (len(phone_str) - 6)}{phone_str[-4:]}"
    return "*" * len(phone_str)


def mask_email(email: str | None) -> str:
    """Mask username portion of email address while preserving domain.

    Example: 'officer@cybercell.gov.in' -> 'o*****r@cybercell.gov.in'
    """
    if not email or "@" not in email:
        return email or ""
    parts = email.split("@", 1)
    username, domain = parts[0], parts[1]
    if len(username) <= 2:
        masked_user = "*" * len(username)
    else:
        masked_user = f"{username[0]}{'*' * (len(username) - 2)}{username[-1]}"
    return f"{masked_user}@{domain}"


def mask_upi(upi: str | None) -> str:
    """Mask username portion of UPI VPA while preserving PSP handle.

    Example: 'suspect99@synthaxis' -> 's*******9@synthaxis'
    """
    if not upi or "@" not in upi:
        return upi or ""
    handle, provider = upi.split("@", 1)
    if len(handle) <= 2:
        masked_handle = "*" * len(handle)
    else:
        masked_handle = f"{handle[0]}{'*' * (len(handle) - 2)}{handle[-1]}"
    return f"{masked_handle}@{provider}"


# Patterns targeting sensitive data in log strings
RE_PASSWORD = re.compile(r'(["\']?(?:password|passwd|pwd|secret)["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE)
RE_BEARER = re.compile(r'(Bearer\s+)[A-Za-z0-9\-_\.]+', re.IGNORECASE)
RE_JWT = re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+')
RE_AUTH_HEADER = re.compile(r'(["\']?Authorization["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE)
RE_FULL_SYN_ACCOUNT = re.compile(r'\b(SYN\d{2})\d{2,8}(\d{4})\b')


def sanitize_for_logging(text: str) -> str:
    """Scrub passwords, JWTs, Bearer tokens, and full account numbers from a log string."""
    if not text:
        return text
    # 1. Mask passwords & secrets
    sanitized = RE_PASSWORD.sub(r'\1[REDACTED_SECRET]\3', text)
    # 2. Mask Authorization headers
    sanitized = RE_AUTH_HEADER.sub(r'\1[REDACTED_AUTH]\3', sanitized)
    # 3. Mask Bearer tokens
    sanitized = RE_BEARER.sub(r'\1[REDACTED_TOKEN]', sanitized)
    # 4. Mask JWT tokens
    sanitized = RE_JWT.sub(r'[REDACTED_JWT]', sanitized)
    # 5. Mask full synthetic account numbers: SYN1122334455 -> SYN11****4455
    sanitized = RE_FULL_SYN_ACCOUNT.sub(r'\1****\2', sanitized)
    return sanitized


SENSITIVE_DICT_KEYS = {
    "password",
    "hashed_password",
    "password_hash",
    "passwd",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "jwt_secret",
    "jwt_secret_key",
    "authorization",
    "api_key",
    "private_key",
    "credential",
    "credentials",
}


def mask_sensitive_dict(data: Union[Dict[str, Any], List[Any], Any]) -> Any:
    """Recursively redact sensitive keys from dictionary payloads before audit logging."""
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            if k.lower() in SENSITIVE_DICT_KEYS:
                cleaned[k] = "[REDACTED]"
            elif k.lower() in ("account_number", "sender_account", "receiver_account", "suspect_account_number"):
                cleaned[k] = mask_account_number(str(v)) if v else v
            elif k.lower() in ("phone", "suspect_phone", "mobile"):
                cleaned[k] = mask_phone(str(v)) if v else v
            elif k.lower() in ("upi", "sender_upi", "receiver_upi", "suspect_upi"):
                cleaned[k] = mask_upi(str(v)) if v else v
            else:
                cleaned[k] = mask_sensitive_dict(v)
        return cleaned
    elif isinstance(data, list):
        return [mask_sensitive_dict(item) for item in data]
    return data
