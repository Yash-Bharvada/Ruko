"""Stateless Twilio Verify and Voice client for phone verification and security alert calls."""

from typing import List, Optional, Tuple
import httpx

from app.core.config import Settings
from app.core.errors import AppException
from app.core.logging import logger


ALERT_CALL_SCRIPT = (
    "This is a security alert from Ruko Cybersecurity Protection. "
    "A data exposure associated with your verified information has been detected. "
    "This does not necessarily mean your account has been compromised right now. "
    "Please open your security dashboard to review the details and remediation steps. "
    "Remember: Ruko will never ask you for your password, OTP, PIN, CVV, or banking credentials."
)


def build_contextual_alert_script(
    email: Optional[str] = None,
    total_breaches: int = 0,
    financial_exposed: bool = False,
    breach_names: Optional[list] = None,
) -> str:
    """Build dynamic, contextual alert message tailored to the user's specific breach scan."""
    parts = ["This is an urgent security alert from Ruko Cybersecurity Protection."]
    if email:
        parts.append(f"We detected that your email address, {email}, appeared in recent data breach incidents.")
    else:
        parts.append("We detected that your verified information appeared in recent data breach incidents.")

    if total_breaches > 0:
        parts.append(f"A total of {total_breaches} compromised incident records were identified.")

    if breach_names:
        services = ", ".join(breach_names[:4])
        parts.append(f"Compromised services include: {services}.")

    if financial_exposed:
        parts.append(
            "Critical Warning: Sensitive financial or payment card data was leaked. "
            "Please contact your bank immediately to monitor accounts and block unauthorized transactions."
        )
    else:
        parts.append(
            "Please change your passwords on affected accounts immediately and enable two-factor authentication."
        )

    parts.append(
        "Remember: Ruko will never ask you for your password, OTP, ATM PIN, or CVV. Stay alert and stay safe."
    )
    return " ".join(parts)


def build_alert_twiml(script: Optional[str] = None) -> str:
    """Build TwiML with Polly voice for data exposure alert."""
    text_to_speak = script or ALERT_CALL_SCRIPT
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        '<Say voice="Polly.Aditi" language="en-IN">'
        f"{text_to_speak}"
        "</Say>"
        "</Response>"
    )


async def start_phone_verification(
    phone_e164: str,
    channel: str,
    settings: Settings,
) -> Tuple[str, str]:
    """Initiate phone verification via Twilio Verify v2 REST API.

    Guarantees:
    - 8s timeout, no duplicate retries.
    - Never logs phone numbers, codes, tokens, or Twilio response bodies.
    - Maps upstream telephony errors to standard error envelopes.

    Returns:
        (status: "ok" | "sms_unavailable_try_call", message: str)
    """
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_VERIFY_SERVICE_SID):
        logger.info("Twilio Verify credentials not configured; start verification running in mock/demo mode")
        return "ok", "Verification code dispatched (mock mode)."

    url = f"https://verify.twilio.com/v2/Services/{settings.TWILIO_VERIFY_SERVICE_SID}/Verifications"
    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    data = {
        "To": phone_e164,
        "Channel": channel if channel in ("sms", "call") else "sms",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, data=data, auth=auth)
            logger.info("Twilio Verify Verifications response received (status=%s)", resp.status_code)

            if resp.status_code in (200, 201):
                return "ok", "Verification code sent successfully."

            # Parse error codes safely without logging response body
            status_code = resp.status_code
            tw_code = None
            try:
                err_json = resp.json()
                tw_code = err_json.get("code")
            except Exception:
                pass

            # 1. Unverified Trial Number error (Twilio error 21608)
            if tw_code == 21608:
                raise AppException(
                    status_code=400,
                    code="number_not_verified_for_trial",
                    message="On this demo account, only phone numbers pre-approved by the organisers can receive codes.",
                )

            # 2. Too many attempts / rate limit (e.g. 60202, 60203, 429)
            if status_code == 429 or tw_code in (60202, 60203):
                raise AppException(
                    status_code=429,
                    code="rate_limit_exceeded",
                    message="Too many verification attempts. Please wait a few minutes before trying again.",
                )

            # 3. Invalid phone number (Twilio 21211)
            if tw_code == 21211 or (status_code == 422 and tw_code != 60203):
                raise AppException(
                    status_code=422,
                    code="invalid_phone_number",
                    message="The phone number provided is invalid or unsupported.",
                )

            # 4. If SMS delivery failed (e.g. DLT or carrier block), offer voice call option
            if channel == "sms":
                return (
                    "sms_unavailable_try_call",
                    "SMS verification is unavailable for this carrier/number. Please try receiving the code via voice call.",
                )

            # 5. Any other telephony error
            raise AppException(
                status_code=503,
                code="verification_unavailable",
                message="Telephony verification service is temporarily unavailable. Please try again later.",
            )

    except AppException:
        raise
    except Exception as exc:
        logger.warning("Twilio Verify Verifications request failed: %s", type(exc).__name__)
        if channel == "sms":
            return (
                "sms_unavailable_try_call",
                "SMS verification is unavailable. Please try receiving the code via voice call.",
            )
        raise AppException(
            status_code=503,
            code="verification_unavailable",
            message="Telephony verification service timed out or is unavailable.",
        )


async def check_phone_verification(
    phone_e164: str,
    code: str,
    settings: Settings,
) -> bool:
    """Verify submitted code using Twilio Verify v2 VerificationCheck.

    Guarantees:
    - 8s timeout, no retries.
    - Never logs phone numbers, codes, tokens, or response bodies.
    - Treat status == "approved" as success.
    """
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_VERIFY_SERVICE_SID):
        logger.info("Twilio Verify credentials not configured; verification check running in mock/demo mode")
        # In mock mode, reject '000000' or '999999', accept valid codes
        return code not in ("000000", "999999", "0000")

    url = f"https://verify.twilio.com/v2/Services/{settings.TWILIO_VERIFY_SERVICE_SID}/VerificationCheck"
    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    data = {
        "To": phone_e164,
        "Code": code,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, data=data, auth=auth)
            logger.info("Twilio VerificationCheck response received (status=%s)", resp.status_code)

            if resp.status_code in (200, 201):
                try:
                    result_json = resp.json()
                    return result_json.get("status") == "approved"
                except Exception:
                    return False

            if resp.status_code == 429:
                raise AppException(
                    status_code=429,
                    code="rate_limit_exceeded",
                    message="Too many verification attempts. Please wait a few minutes before trying again.",
                )

            return False
    except AppException:
        raise
    except Exception as exc:
        logger.warning("Twilio VerificationCheck request failed: %s", type(exc).__name__)
        return False


async def place_alert_call(
    phone_e164: str,
    settings: Settings,
    script: Optional[str] = None,
) -> bool:
    """Place automated emergency security alert voice call with contextual script.

    Guarantees:
    - Never logs phone number.
    - Contextual security alert script without any credential requests.
    """
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER):
        logger.info("Twilio voice credentials not configured; alert call recorded as demo success")
        return True

    twiml = build_alert_twiml(script)
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Calls.json"
    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    data = {
        "To": phone_e164,
        "From": settings.TWILIO_PHONE_NUMBER,
        "Twiml": twiml,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, data=data, auth=auth)
            if resp.status_code in (200, 201):
                logger.info("Twilio alert call initiated successfully (status=%s)", resp.status_code)
                return True
            else:
                logger.warning("Twilio alert call returned non-success status: %s", resp.status_code)
                return False
    except Exception as exc:
        logger.warning("Failed to place Twilio alert call: %s", type(exc).__name__)
        return False
