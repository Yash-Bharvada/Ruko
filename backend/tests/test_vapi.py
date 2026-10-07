"""Unit and integration tests for Vapi AI calling agent module."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app
from app.modules.vapi.prompt import generate_first_message, get_agent_variable_values


def test_first_message_multilingual_generation():
    """Verify first greeting generation in Hindi, Gujarati, and English."""
    hi_msg = generate_first_message("user@test.com", 2, True, "hi")
    assert "नमस्ते" in hi_msg
    assert "वित्तीय जानकारी" in hi_msg

    gu_msg = generate_first_message("user@test.com", 2, True, "gu")
    assert "નમસ્તે" in gu_msg
    assert "નાણાકીય" in gu_msg

    en_msg = generate_first_message("user@test.com", 3, False, "en")
    assert "Hello" in en_msg
    assert "user@test.com" in en_msg


def test_agent_variable_values_mapping():
    """Verify variable values formatting for Vapi template substitution."""
    vars_dict = get_agent_variable_values(
        email="test@example.com",
        total_breaches=2,
        high_risk_count=1,
        financial_exposed=True,
        breach_names=["FinPay", "RetailHub"],
        exposure_categories=["Passwords", "Credit cards"],
    )
    assert vars_dict["user_email"] == "test@example.com"
    assert vars_dict["total_breaches"] == "2"
    assert "YES" in vars_dict["financial_exposed"]
    assert "FinPay" in vars_dict["exposed_services"]


@pytest.mark.asyncio
async def test_vapi_session_endpoint():
    """Test /v1/vapi/session endpoint with simulated mode."""
    app = create_app(Settings(VAPI_SIMULATE=True))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/vapi/session",
            json={
                "email": "investor@example.com",
                "total_breaches": 4,
                "high_risk_count": 2,
                "financial_exposed": True,
                "breach_names": ["Canva", "FinPay"],
                "exposure_categories": ["Passwords", "Bank accounts"],
                "language": "hi",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ready", "simulated")
        assert "नमस्ते" in data["first_message"]
        assert "investor@example.com" in data["variable_values"]["user_email"]


@pytest.mark.asyncio
async def test_vapi_phone_call_endpoint_simulation():
    """Test /v1/vapi/call/phone endpoint in simulation mode."""
    app = create_app(Settings(VAPI_SIMULATE=True))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/vapi/call/phone",
            json={
                "phone": "+919876543210",
                "email": "investor@example.com",
                "total_breaches": 1,
                "high_risk_count": 0,
                "financial_exposed": False,
                "language": "en",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "simulated"
        assert "call_id" in data
