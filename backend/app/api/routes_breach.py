"""Stateless API endpoints for Breach Exposure Monitoring and Voice Alerts."""

from fastapi import APIRouter, Request

from app.core import config
from app.core.errors import AppException
from app.core.logging import logger
from app.core.schemas import (
    BreachAlertRequest,
    BreachAlertResponse,
    BreachCheckRequest,
    BreachCheckResult,
    PhoneStartRequest,
    PhoneStartResponse,
    PhoneVerifyRequest,
    PhoneVerifyResponse,
)
from app.modules.breach import run_breach_check
from app.modules.breach.eligibility import can_place_alert
from app.modules.breach.normalize import normalize_phone_e164
from app.modules.breach.tokens import issue_phone_token, verify_phone_token
from app.modules.breach.twilio_client import (
    ALERT_CALL_SCRIPT,
    check_phone_verification,
    place_alert_call,
    start_phone_verification,
)

router = APIRouter(prefix="/v1/breach", tags=["Breach Monitor"])


@router.post("/check", response_model=BreachCheckResult)
async def check_breach(
    request: Request,
    payload: BreachCheckRequest,
) -> BreachCheckResult:
    """Stateless breach check endpoint: query known data breaches for an email address."""
    settings = getattr(request.app.state, "settings", None) or config.get_settings()
    request_id = getattr(request.state, "request_id", None)

    logger.info("Processing breach check request (request_id=%s)", request_id)
    return await run_breach_check(
        email=payload.email,
        consent=payload.consent,
        settings=settings,
        request_id=request_id,
    )


@router.post("/phone/start", response_model=PhoneStartResponse)
async def phone_verification_start(
    request: Request,
    payload: PhoneStartRequest,
) -> PhoneStartResponse:
    """Initiate phone verification via Twilio Verify (SMS or Voice Call).

    Guarantees:
    - Never logs phone number.
    - If SMS delivery fails (e.g. DLT or trial restrictions), returns status 'sms_unavailable_try_call'.
    - Maps Twilio errors to standard envelope.
    """
    settings = getattr(request.app.state, "settings", None) or config.get_settings()
    request_id = getattr(request.state, "request_id", None)

    if not payload.consent:
        raise AppException(
            status_code=422,
            code="consent_required",
            message="User consent is required to receive a phone verification OTP.",
        )

    phone_e164 = normalize_phone_e164(payload.phone)

    logger.info("Initiating phone verification OTP dispatch (channel=%s, request_id=%s)", payload.channel, request_id)
    status, message = await start_phone_verification(phone_e164, payload.channel, settings)

    return PhoneStartResponse(
        status=status,
        message=message,
    )


@router.post("/phone/verify", response_model=PhoneVerifyResponse)
async def phone_verification_verify(
    request: Request,
    payload: PhoneVerifyRequest,
) -> PhoneVerifyResponse:
    """Verify submitted 4-8 digit OTP against Twilio Verify and issue stateless 15-minute token."""
    settings = getattr(request.app.state, "settings", None) or config.get_settings()
    request_id = getattr(request.state, "request_id", None)

    phone_e164 = normalize_phone_e164(payload.phone)

    logger.info("Checking phone verification OTP (request_id=%s)", request_id)
    is_approved = await check_phone_verification(phone_e164, payload.code, settings)

    if not is_approved:
        logger.warning("Phone verification check failed (request_id=%s)", request_id)
        raise AppException(
            status_code=422,
            code="invalid_verification_code",
            message="Invalid or expired verification code. Please request a new code.",
        )

    logger.info("Phone verification succeeded, issuing authorization token (request_id=%s)", request_id)
    phone_token = issue_phone_token(phone_e164, settings)

    return PhoneVerifyResponse(phone_token=phone_token)


@router.post("/alert", response_model=BreachAlertResponse)
async def trigger_breach_alert(
    request: Request,
    payload: BreachAlertRequest,
) -> BreachAlertResponse:
    """Trigger an automated emergency security alert voice call if all eligibility criteria are satisfied."""
    settings = getattr(request.app.state, "settings", None) or config.get_settings()
    request_id = getattr(request.state, "request_id", None)

    phone_e164 = normalize_phone_e164(payload.phone)

    # Verify authorization token
    phone_verified = verify_phone_token(
        phone_token=payload.phone_token,
        phone_e164=phone_e164,
        settings=settings,
    )

    if not phone_verified:
        logger.warning("Alert call rejected: phone authorization token invalid or expired (request_id=%s)", request_id)
        raise AppException(
            status_code=401,
            code="unauthorized_phone",
            message="Phone authorization token is invalid or has expired. Please re-verify your phone number.",
        )

    # Evaluate eligibility (Opt-in, High Risk, Quiet Hours, Enabled)
    eligible, reason = can_place_alert(
        risk_level="HIGH" if payload.exposures_high_risk_new else "LOW",
        is_new_high_risk=payload.exposures_high_risk_new,
        opted_in=payload.voice_opt_in,
        phone_verified=phone_verified,
        settings=settings,
        override_quiet=False if payload.is_test_call else None,
    )

    if not eligible:
        reason_messages = {
            "voice_alerts_disabled": "Voice alerts are currently disabled in server configuration.",
            "user_not_opted_in": "User has not opted in to receive automated voice alert calls.",
            "not_high_risk": "Voice alerts are only dispatched for critical HIGH-risk exposures.",
            "quiet_hours_active": "Voice alerts are suppressed during quiet hours (21:00 - 08:00 IST) to respect user privacy.",
            "phone_not_verified": "Phone number is not verified.",
        }
        msg = reason_messages.get(reason, f"Alert call not placed: {reason}")
        logger.info("Alert call not dispatched: reason=%s (request_id=%s)", reason, request_id)
        return BreachAlertResponse(
            status="rejected" if reason != "voice_alerts_disabled" else "disabled",
            message=msg,
            call_placed=False,
        )

    # Generate contextual security alert script
    from app.modules.breach.twilio_client import build_contextual_alert_script
    alert_script = build_contextual_alert_script(
        email=payload.email,
        total_breaches=payload.total_breaches,
        financial_exposed=payload.financial_exposed,
        breach_names=payload.breach_names,
    )

    # Dispatch alert voice call or return simulated alert
    if getattr(settings, "BREACH_ALERT_SIMULATE", False):
        logger.info("BREACH_ALERT_SIMULATE=True: returning simulated alert (request_id=%s)", request_id)
        return BreachAlertResponse(
            status="simulated",
            script=alert_script,
            message="Simulated alert: no real call was placed.",
            call_placed=False,
        )

    logger.info("Dispatching emergency breach alert call (request_id=%s)", request_id)
    placed = await place_alert_call(phone_e164, settings, script=alert_script)

    return BreachAlertResponse(
        status="ok" if placed else "rejected",
        message="Voice alert call dispatched successfully." if placed else "Failed to dispatch voice call via upstream telephony.",
        call_placed=placed,
        script=alert_script,
        hint="live_calls_unavailable" if not placed else None,
    )
