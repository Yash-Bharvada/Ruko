"""Unit and integration tests for Breach Exposure Monitoring & Twilio Verify."""

import asyncio
import logging
import time
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.schemas import ExposureRecord
from app.main import create_app
from app.modules.breach.eligibility import can_place_alert
from app.modules.breach.normalize import normalize_email, normalize_phone_e164
from app.modules.breach.providers import HibpProvider, MockProvider
from app.modules.breach.risk_classifier import classify_exposure
from app.modules.breach.tokens import issue_phone_token, verify_phone_token
from app.modules.breach.twilio_client import (
    ALERT_CALL_SCRIPT,
    build_alert_twiml,
    check_phone_verification,
    place_alert_call,
    start_phone_verification,
)


# =============================================================================
# 1. Normalization Tests
# =============================================================================

def test_email_normalization_valid():
    assert normalize_email("  User.Name+Tag@Example.COM  ") == "user.name+tag@example.com"
    assert normalize_email("INVESTOR@DOMAIN.IN") == "investor@domain.in"


def test_email_normalization_invalid():
    with pytest.raises(Exception):
        normalize_email("not-an-email")

    with pytest.raises(Exception):
        normalize_email("@missinguser.com")

    with pytest.raises(Exception):
        normalize_email("")


def test_phone_normalization_valid():
    assert normalize_phone_e164("+91 98765 43210") == "+919876543210"
    assert normalize_phone_e164("+1 (555) 234-5678") == "+15552345678"
    assert normalize_phone_e164("+91-9876543210") == "+919876543210"


def test_phone_normalization_invalid():
    with pytest.raises(Exception):
        normalize_phone_e164("123")  # too short

    with pytest.raises(Exception):
        normalize_phone_e164("+000000000000000000")  # too long or invalid


# =============================================================================
# 2. Risk Classifier & Financial Exposure Isolation Tests
# =============================================================================

def test_risk_classifier_financial_exposure_explicit_only():
    # Explicit financial categories
    risk, fin = classify_exposure(["Email addresses", "Credit card details", "Passphrases"])
    assert risk == "HIGH"
    assert fin is True

    risk, fin = classify_exposure(["Bank account numbers", "Names"])
    assert risk == "HIGH"
    assert fin is True

    # High-risk credentials without financial data
    risk, fin = classify_exposure(["Email addresses", "Passwords", "Usernames"])
    assert risk == "HIGH"
    assert fin is False  # Never infer financial exposure from generic breaches!

    # Medium-risk personal profile
    risk, fin = classify_exposure(["Email addresses", "Phone numbers", "Physical addresses"])
    assert risk == "MEDIUM"
    assert fin is False

    # Low-risk public/basic profile
    risk, fin = classify_exposure(["Usernames", "Website activity"])
    assert risk == "LOW"
    assert fin is False


# =============================================================================
# 3. Provider Handling & Zero Raw Leaked Data Tests
# =============================================================================

@pytest.mark.asyncio
async def test_mock_provider_clean_and_breached():
    mock_p = MockProvider()
    settings = Settings(BREACH_PROVIDER="mock")

    # Breached email
    status, exposures, is_demo, degraded = await mock_p.check_email("investor@example.com", settings)
    assert status == "ok"
    assert is_demo is True
    assert len(exposures) >= 2
    assert exposures[0].risk_level in ("HIGH", "MEDIUM", "LOW")
    assert isinstance(exposures[0], ExposureRecord)

    # Clean email
    status_clean, exposures_clean, _, _ = await mock_p.check_email("clean_investor@ruko.in", settings)
    assert status_clean == "ok"
    assert len(exposures_clean) == 0


@pytest.mark.asyncio
async def test_hibp_provider_failure_returns_scan_unavailable():
    """Verify that network/upstream errors return scan_unavailable, NEVER empty OK."""
    hibp = HibpProvider()
    settings = Settings(BREACH_PROVIDER="hibp", HIBP_API_KEY="mock_key")

    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        status, exposures, is_demo, degraded = await hibp.check_email("test@example.com", settings)
        assert status == "scan_unavailable"
        assert len(exposures) == 0
        assert "hibp_network_error" in degraded or "hibp_unavailable" in degraded


# =============================================================================
# 4. Twilio Verify Unit & Error Mapping Tests
# =============================================================================

@pytest.mark.asyncio
async def test_twilio_verify_start_sms_and_call_channels():
    settings = Settings(
        TWILIO_ACCOUNT_SID="AC_test",
        TWILIO_AUTH_TOKEN="auth_test",
        TWILIO_VERIFY_SERVICE_SID="VA_test",
    )

    mock_resp = httpx.Response(201, json={"status": "pending"})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        # Test SMS Channel
        status, msg = await start_phone_verification("+919876543210", "sms", settings)
        assert status == "ok"
        args, kwargs = mock_post.call_args
        assert kwargs["data"]["Channel"] == "sms"
        assert kwargs["data"]["To"] == "+919876543210"

        # Test Voice Call Channel
        status, msg = await start_phone_verification("+919876543210", "call", settings)
        assert status == "ok"
        args, kwargs = mock_post.call_args
        assert kwargs["data"]["Channel"] == "call"


@pytest.mark.asyncio
async def test_twilio_verify_sms_failure_falls_back_to_try_call():
    settings = Settings(
        TWILIO_ACCOUNT_SID="AC_test",
        TWILIO_AUTH_TOKEN="auth_test",
        TWILIO_VERIFY_SERVICE_SID="VA_test",
    )

    # Simulate SMS failure (e.g. DLT or carrier error)
    mock_err_resp = httpx.Response(400, json={"code": 60200, "message": "SMS delivery failed"})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_err_resp

        status, msg = await start_phone_verification("+919876543210", "sms", settings)
        assert status == "sms_unavailable_try_call"
        assert "voice call" in msg.lower()


@pytest.mark.asyncio
async def test_twilio_verify_error_mappings():
    settings = Settings(
        TWILIO_ACCOUNT_SID="AC_test",
        TWILIO_AUTH_TOKEN="auth_test",
        TWILIO_VERIFY_SERVICE_SID="VA_test",
    )

    # 1. Unverified trial number (Twilio 21608)
    trial_err_resp = httpx.Response(400, json={"code": 21608, "message": "Number unverified for trial"})
    with patch("httpx.AsyncClient.post", return_value=trial_err_resp):
        with pytest.raises(Exception) as excinfo:
            await start_phone_verification("+919876543210", "call", settings)
        assert "trial" in str(excinfo.value).lower() or getattr(excinfo.value, "code", "") == "number_not_verified_for_trial"

    # 2. Invalid phone number (Twilio 21211)
    invalid_num_resp = httpx.Response(422, json={"code": 21211, "message": "Invalid To number"})
    with patch("httpx.AsyncClient.post", return_value=invalid_num_resp):
        with pytest.raises(Exception) as excinfo:
            await start_phone_verification("+919876543210", "call", settings)
        assert getattr(excinfo.value, "code", "") == "invalid_phone_number" or getattr(excinfo.value, "status_code", 0) == 422

    # 3. Rate limit exceeded (Twilio 60202 / 429)
    rate_resp = httpx.Response(429, json={"code": 60202, "message": "Max check attempts reached"})
    with patch("httpx.AsyncClient.post", return_value=rate_resp):
        with pytest.raises(Exception) as excinfo:
            await start_phone_verification("+919876543210", "call", settings)
        assert getattr(excinfo.value, "status_code", 0) == 429 or getattr(excinfo.value, "code", "") == "rate_limit_exceeded"


@pytest.mark.asyncio
async def test_twilio_verify_check_approved_and_non_approved():
    settings = Settings(
        TWILIO_ACCOUNT_SID="AC_test",
        TWILIO_AUTH_TOKEN="auth_test",
        TWILIO_VERIFY_SERVICE_SID="VA_test",
    )

    # Approved status
    approved_resp = httpx.Response(200, json={"status": "approved"})
    with patch("httpx.AsyncClient.post", return_value=approved_resp):
        assert await check_phone_verification("+919876543210", "123456", settings) is True

    # Pending / failed status
    pending_resp = httpx.Response(200, json={"status": "pending"})
    with patch("httpx.AsyncClient.post", return_value=pending_resp):
        assert await check_phone_verification("+919876543210", "000000", settings) is False


# =============================================================================
# 5. Token Lifecycle & Guardrail Invariant Tests
# =============================================================================

def test_phone_authorization_token_lifecycle():
    phone = "+919876543210"
    now = int(time.time())

    token = issue_phone_token(phone, issued_at=now)

    # Valid token within 15 min TTL
    assert verify_phone_token(token, phone, current_time=now + 60) is True
    assert verify_phone_token(token, phone, current_time=now + 899) is True

    # Expired token (>900s)
    assert verify_phone_token(token, phone, current_time=now + 950) is False

    # Wrong phone
    assert verify_phone_token(token, "+919000000000", current_time=now) is False

    # Tampered token
    tampered = token[:-4] + "abcd"
    assert verify_phone_token(tampered, phone, current_time=now) is False


def test_voice_alert_script_contains_zero_credential_requests():
    """Verify that the alert script strictly forbids asking for OTP/PIN/password."""
    script = ALERT_CALL_SCRIPT.lower()

    # Must contain warning statement
    assert "never ask you for your password" in script
    assert "otp" in script
    assert "pin" in script
    assert "cvv" in script
    assert "does not necessarily mean your account has been compromised" in script

    # TwiML xml test
    twiml = build_alert_twiml()
    assert "<Say" in twiml
    assert "Polly.Aditi" in twiml


# =============================================================================
# 6. Eligibility & Quiet Hours Tests
# =============================================================================

def test_can_place_alert_matrix():
    settings = Settings(
        VOICE_ALERTS_ENABLED=True,
        BREACH_QUIET_START=21,
        BREACH_QUIET_END=8,
    )

    # 1. Fully eligible (high risk, opted in, verified, not in quiet hours)
    eligible, reason = can_place_alert(
        risk_level="HIGH",
        is_new_high_risk=True,
        opted_in=True,
        phone_verified=True,
        settings=settings,
        override_quiet=False,
    )
    assert eligible is True
    assert reason == "eligible"

    # 2. Quiet hours active -> Rejected
    eligible, reason = can_place_alert(
        risk_level="HIGH",
        is_new_high_risk=True,
        opted_in=True,
        phone_verified=True,
        settings=settings,
        override_quiet=True,
    )
    assert eligible is False
    assert reason == "quiet_hours_active"

    # 3. Not opted in -> Rejected
    eligible, reason = can_place_alert(
        risk_level="HIGH",
        is_new_high_risk=True,
        opted_in=False,
        phone_verified=True,
        settings=settings,
        override_quiet=False,
    )
    assert eligible is False
    assert reason == "user_not_opted_in"

    # 4. Not high risk -> Rejected
    eligible, reason = can_place_alert(
        risk_level="LOW",
        is_new_high_risk=False,
        opted_in=True,
        phone_verified=True,
        settings=settings,
        override_quiet=False,
    )
    assert eligible is False
    assert reason == "not_high_risk"

    # 5. Disabled in settings
    disabled_settings = Settings(VOICE_ALERTS_ENABLED=False)
    eligible, reason = can_place_alert(
        risk_level="HIGH",
        is_new_high_risk=True,
        opted_in=True,
        phone_verified=True,
        settings=disabled_settings,
        override_quiet=False,
    )
    assert eligible is False
    assert reason == "voice_alerts_disabled"


# =============================================================================
# 7. End-to-End API Integration & Zero PII Logging Tests
# =============================================================================

@pytest.mark.asyncio
async def test_api_breach_check_requires_consent():
    app = create_app(Settings(BREACH_PROVIDER="mock"))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Without consent -> 422
        resp = await client.post("/v1/breach/check", json={"email": "test@example.com", "consent": False})
        assert resp.status_code == 422

        # Extra forbidden fields -> 422
        resp = await client.post("/v1/breach/check", json={"email": "test@example.com", "consent": True, "extra_field": "bad"})
        assert resp.status_code == 422

        # Valid request with consent
        resp = await client.post("/v1/breach/check", json={"email": "test@example.com", "consent": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "exposures" in data
        assert "data_safety" in data
        assert len(data["data_safety"]) >= 3


@pytest.mark.asyncio
async def test_api_phone_verification_and_alert_flow(caplog):
    caplog.set_level(logging.INFO)
    app = create_app(Settings(BREACH_PROVIDER="mock", VOICE_ALERTS_ENABLED=True))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Start phone verification (SMS channel)
        start_resp = await client.post(
            "/v1/breach/phone/start",
            json={"phone": "+919876543210", "consent": True, "channel": "sms"},
        )
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        assert start_data["status"] == "ok"

        # 2. Invalid code format (<4 digits or non-numeric) -> 422
        bad_format_resp = await client.post(
            "/v1/breach/phone/verify",
            json={"phone": "+919876543210", "code": "12"},
        )
        assert bad_format_resp.status_code == 422

        bad_alpha_resp = await client.post(
            "/v1/breach/phone/verify",
            json={"phone": "+919876543210", "code": "abcdef"},
        )
        assert bad_alpha_resp.status_code == 422

        # 3. Wrong code -> 422
        bad_verify = await client.post(
            "/v1/breach/phone/verify",
            json={"phone": "+919876543210", "code": "000000"},
        )
        assert bad_verify.status_code == 422

        # 4. Valid code -> 200 + phone_token
        good_verify = await client.post(
            "/v1/breach/phone/verify",
            json={"phone": "+919876543210", "code": "123456"},
        )
        assert good_verify.status_code == 200
        phone_token = good_verify.json()["phone_token"]
        assert len(phone_token) > 10

        # 5. Trigger alert call with valid token
        alert_resp = await client.post(
            "/v1/breach/alert",
            json={
                "phone": "+919876543210",
                "phone_token": phone_token,
                "voice_opt_in": True,
                "exposures_high_risk_new": True,
            },
        )
        assert alert_resp.status_code == 200
        alert_data = alert_resp.json()
        assert alert_data["status"] in ("ok", "rejected")

        # 6. Verify zero phone numbers or codes in logs
        log_text = caplog.text
        assert "+919876543210" not in log_text
        assert "9876543210" not in log_text
        assert "123456" not in log_text


@pytest.mark.asyncio
async def test_api_simulated_alert_flow():
    """Verify that BREACH_ALERT_SIMULATE=True returns status='simulated' with fixed script without calling Twilio."""
    app = create_app(Settings(
        BREACH_PROVIDER="mock",
        VOICE_ALERTS_ENABLED=True,
        BREACH_ALERT_SIMULATE=True,
        BREACH_QUIET_START=0,
        BREACH_QUIET_END=0,  # Quiet hours inactive
    ))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Start & verify phone to obtain valid token
        await client.post("/v1/breach/phone/start", json={"phone": "+919876543210", "consent": True, "channel": "sms"})
        verify_resp = await client.post("/v1/breach/phone/verify", json={"phone": "+919876543210", "code": "123456"})
        phone_token = verify_resp.json()["phone_token"]

        with patch("app.modules.breach.twilio_client.place_alert_call", new_callable=AsyncMock) as mock_call:
            alert_resp = await client.post(
                "/v1/breach/alert",
                json={
                    "phone": "+919876543210",
                    "phone_token": phone_token,
                    "voice_opt_in": True,
                    "exposures_high_risk_new": True,
                },
            )
            assert alert_resp.status_code == 200
            data = alert_resp.json()
            assert data["status"] == "simulated"
            assert data["call_placed"] is False
            assert "script" in data and data["script"] is not None
            assert "never ask you for your password" in data["script"].lower()
            assert data["message"] == "Simulated alert: no real call was placed."
            # Twilio call must NOT have been called
            mock_call.assert_not_called()


@pytest.mark.asyncio
async def test_simulated_alert_blocked_by_eligibility():
    """Verify that eligibility checks (opt-in, high-risk, disabled) still block simulated alerts."""
    app = create_app(Settings(
        BREACH_PROVIDER="mock",
        VOICE_ALERTS_ENABLED=True,
        BREACH_ALERT_SIMULATE=True,
    ))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get valid token
        verify_resp = await client.post("/v1/breach/phone/verify", json={"phone": "+919876543210", "code": "123456"})
        phone_token = verify_resp.json()["phone_token"]

        # 1. Blocked if not opted in
        resp = await client.post(
            "/v1/breach/alert",
            json={
                "phone": "+919876543210",
                "phone_token": phone_token,
                "voice_opt_in": False,
                "exposures_high_risk_new": True,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"
        assert "opted in" in resp.json()["message"].lower()

        # 2. Blocked if invalid phone token
        resp_bad = await client.post(
            "/v1/breach/alert",
            json={
                "phone": "+919876543210",
                "phone_token": "bad.token.signature",
                "voice_opt_in": True,
                "exposures_high_risk_new": True,
            },
        )
        assert resp_bad.status_code == 401

