"""Stateless HMAC-SHA256 narration signing for safe, verified browser audio readout."""

import base64
import hashlib
import hmac
import secrets
import time
from typing import Optional

from app.core.config import Settings, get_settings

# In-memory startup fallback secret key if not set in environment
_IN_MEMORY_SIGNING_KEY = secrets.token_urlsafe(32)


def get_active_signing_key(settings: Optional[Settings] = None) -> str:
    """Retrieve configured signing key or persistent in-memory fallback."""
    conf = settings or get_settings()
    configured = getattr(conf, "EXPLAIN_SIGNING_KEY", "")
    if configured and configured.strip():
        return configured.strip()
    return _IN_MEMORY_SIGNING_KEY


def generate_speak_token(
    request_id: str,
    scene_id: str,
    language: str,
    issued_at: int,
    narration: str,
    settings: Optional[Settings] = None,
) -> str:
    """Generate a tamper-proof URL-safe base64 HMAC-SHA256 signature for a scene narration.

    Payload signed: f"{request_id}|{scene_id}|{language}|{issued_at}|{narration}"
    """
    key = get_active_signing_key(settings).encode("utf-8")
    payload = f"{request_id}|{scene_id}|{language}|{issued_at}|{narration}".encode("utf-8")
    signature = hmac.new(key, payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")


def verify_speak_token(
    request_id: str,
    scene_id: str,
    language: str,
    issued_at: int,
    narration: str,
    speak_token: str,
    settings: Optional[Settings] = None,
    current_time: Optional[float] = None,
) -> bool:
    """Verify that a narration string was signed by the server within the TTL window.

    Guarantees:
    - Enforces EXPLAIN_TOKEN_TTL_S (default 1800s / 30 minutes).
    - Constant-time comparison prevents timing attacks.
    - Zero persistence: validation is completely stateless.
    """
    conf = settings or get_settings()
    now = current_time if current_time is not None else time.time()
    ttl_s = getattr(conf, "EXPLAIN_TOKEN_TTL_S", 1800)

    # Check token expiration
    if (now - issued_at) > ttl_s or (issued_at - now) > 60:
        return False

    expected_token = generate_speak_token(
        request_id=request_id,
        scene_id=scene_id,
        language=language,
        issued_at=issued_at,
        narration=narration,
        settings=conf,
    )

    return hmac.compare_digest(speak_token, expected_token)
