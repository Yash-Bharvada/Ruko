"""Eligibility checks for automated emergency voice alerts (Quiet Hours & Verification)."""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from app.core.config import Settings


# Asia/Kolkata timezone offset (UTC+05:30)
KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30))


def is_in_quiet_hours(settings: Settings, current_dt: Optional[datetime] = None) -> bool:
    """Check if the current time in Asia/Kolkata falls within user quiet hours.

    Default quiet window: 21:00 (9 PM) to 08:00 (8 AM) Indian Standard Time.
    """
    now = current_dt if current_dt is not None else datetime.now(KOLKATA_TZ)
    hour = now.hour

    start = getattr(settings, "BREACH_QUIET_START", 21)
    end = getattr(settings, "BREACH_QUIET_END", 8)

    if start > end:
        # Crosses midnight (e.g. 21:00 to 08:00)
        return hour >= start or hour < end
    else:
        # Same day window (e.g. 01:00 to 06:00)
        return start <= hour < end


def can_place_alert(
    risk_level: str,
    is_new_high_risk: bool,
    opted_in: bool,
    phone_verified: bool,
    settings: Settings,
    override_quiet: Optional[bool] = None,
) -> Tuple[bool, str]:
    """Evaluate whether an automated voice alert call should be placed.

    Conditions:
    1. Voice alerts feature must be enabled in config.
    2. User must have explicitly opted in (opted_in=True).
    3. Phone number must be cryptographically verified (phone_verified=True).
    4. Exposure must be HIGH risk or newly surfaced high risk.
    5. Current time must NOT fall within quiet hours.

    Returns:
        (can_place: bool, reason_code: str)
    """
    if not getattr(settings, "VOICE_ALERTS_ENABLED", False):
        return False, "voice_alerts_disabled"

    if not opted_in:
        return False, "user_not_opted_in"

    if not phone_verified:
        return False, "phone_not_verified"

    # Only dispatch voice calls for high-risk critical exposures
    is_critical = (risk_level == "HIGH") or is_new_high_risk
    if not is_critical:
        return False, "not_high_risk"

    in_quiet = is_in_quiet_hours(settings) if override_quiet is None else override_quiet
    if in_quiet:
        return False, "quiet_hours_active"

    return True, "eligible"
