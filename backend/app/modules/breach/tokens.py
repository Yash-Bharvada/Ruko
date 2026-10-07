"""Stateless cryptographic HMAC-SHA256 signing for phone verification challenge and authorization tokens."""

import base64
import hashlib
import hmac
import secrets
import time
from typing import Optional

from app.core.config import Settings, get_settings


_IN_MEMORY_BREACH_SIGNING_KEY = secrets.token_urlsafe(32)


def get_breach_signing_key(settings: Optional[Settings] = None) -> str:
    """Retrieve configured breach signing key or persistent in-memory fallback."""
    conf = settings or get_settings()
    configured = getattr(conf, "BREACH_SIGNING_KEY", "") or getattr(conf, "EXPLAIN_SIGNING_KEY", "")
    if configured and configured.strip():
        return configured.strip()
    return _IN_MEMORY_BREACH_SIGNING_KEY


# =============================================================================
# 1. Stateless Phone Verification Challenge (5-minute TTL)
# =============================================================================

def generate_phone_challenge(
    phone_e164: str,
    code: str,
    expires_at: int,
    settings: Optional[Settings] = None,
) -> str:
    """Generate a stateless HMAC-signed challenge encapsulating the expected code and expiry.

    Payload signed: f"{phone_e164}|{expires_at}|{code}"
    Returns: f"{expires_at}.{signature_b64}"
    """
    key = get_breach_signing_key(settings).encode("utf-8")
    payload = f"{phone_e164}|{expires_at}|{code}".encode("utf-8")
    signature = hmac.new(key, payload, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{expires_at}.{sig_b64}"


def verify_phone_challenge(
    phone_e164: str,
    code: str,
    challenge: str,
    settings: Optional[Settings] = None,
    current_time: Optional[float] = None,
) -> bool:
    """Verify that the user submitted the exact 6-digit code for the challenge before expiry."""
    if not challenge or "." not in challenge:
        return False

    parts = challenge.split(".", 1)
    if len(parts) != 2:
        return False

    try:
        expires_at = int(parts[0])
    except ValueError:
        return False

    now = int(current_time if current_time is not None else time.time())
    if now > expires_at or (now < expires_at - 360):
        # Expired or suspiciously ahead in future (>6 minutes)
        return False

    expected_challenge = generate_phone_challenge(
        phone_e164=phone_e164,
        code=code.strip(),
        expires_at=expires_at,
        settings=settings,
    )

    return hmac.compare_digest(challenge, expected_challenge)


# =============================================================================
# 2. Stateless Phone Authorization Token (15-minute TTL)
# =============================================================================

def issue_phone_token(
    phone_e164: str,
    settings: Optional[Settings] = None,
    issued_at: Optional[int] = None,
) -> str:
    """Issue a stateless authorization token confirming verified ownership of the phone number.

    TTL: 15 minutes (900s).
    Format: f"{issued_at}.{signature_b64}"
    """
    iat = issued_at if issued_at is not None else int(time.time())
    key = get_breach_signing_key(settings).encode("utf-8")
    payload = f"{phone_e164}|{iat}|phone_verified".encode("utf-8")
    signature = hmac.new(key, payload, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{iat}.{sig_b64}"


def verify_phone_token(
    phone_token: str,
    phone_e164: str,
    settings: Optional[Settings] = None,
    current_time: Optional[float] = None,
) -> bool:
    """Verify validity and 15-minute expiration of a phone authorization token."""
    if not phone_token or "." not in phone_token:
        return False

    parts = phone_token.split(".", 1)
    if len(parts) != 2:
        return False

    try:
        iat = int(parts[0])
    except ValueError:
        return False

    now = int(current_time if current_time is not None else time.time())
    ttl_s = 900  # 15 minutes

    if (now - iat) > ttl_s or (iat - now) > 60:
        return False

    expected_token = issue_phone_token(
        phone_e164=phone_e164,
        settings=settings,
        issued_at=iat,
    )

    return hmac.compare_digest(phone_token, expected_token)
