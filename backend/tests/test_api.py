"""Comprehensive acceptance tests for Module M9: Guardrails, Orchestrator, and Full API."""

import io
import logging
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import get_rate_limiter
from app.main import app, create_app
from app.modules.ingest.ocr import IngestResult


@pytest.fixture
def client() -> TestClient:
    get_rate_limiter().reset()
    return TestClient(app)


# --- 1. Demo Cases & Verdict Accuracy Tests ---

def test_gujarati_scam_returns_strong_red_flags(client: TestClient) -> None:
    """Acceptance check: Gujarati scam message with guaranteed return returns strong_red_flags."""
    payload = {
        "text": "રોજ ૨૫% નફો પાકો ગેરંટી સાથે. ૧૦૦% રિસ્ક ફ્રી રોકાણ. પૈસા આ UPI પર મોકલો: vip@ybl. ગ્રુપ: t.me/vip_invest",
        "language": "gu",
        "amount": 5000,
    }
    response = client.post("/v1/check", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["verdict"] == "strong_red_flags"
    assert data["language"] == "gu"
    assert data["score"] >= 0.80
    assert len(data["reasons"]) >= 1
    # Check that high severity reason is present
    severities = [r["severity"] for r in data["reasons"]]
    assert "high" in severities
    # Check claim extraction
    assert "vip@ybl" in str(data["claims"]) or len(data["claims"].get("payment_requests", [])) >= 1


def test_english_scam_returns_strong_red_flags(client: TestClient) -> None:
    """Acceptance check: English scam message with guaranteed return and urgent transfer returns strong_red_flags."""
    payload = {
        "text": "Guaranteed 35% monthly returns! 100% risk free. Join VIP insider group t.me/insider_stock. Send 10,000 to profit@oksbi right now!",
        "language": "en",
        "amount": 10000,
    }
    response = client.post("/v1/check", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["verdict"] == "strong_red_flags"
    assert data["score"] >= 0.80
    codes = [r["code"] for r in data["reasons"]]
    assert any(c in codes for c in ("guaranteed_returns", "unauthorized_channel", "model_high_risk"))


def test_genuine_bank_message_does_not_return_strong_red_flags(client: TestClient) -> None:
    """Acceptance check: Benign bank transaction notification returns no_red_flags_found or cannot_verify."""
    payload = {
        "text": "Dear Customer, your bank account ending in 4321 has been credited with INR 2,500 on 01-Mar-2026. Available balance is INR 18,200. Do not share OTP.",
        "language": "en",
    }
    response = client.post("/v1/check", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["verdict"] in ("no_red_flags_found", "cannot_verify")
    # Must never claim message/investment is safe
    assert data["verdict"] != "safe"
    assert "this is safe" not in data["note"].lower()
    assert "guaranteed safe" not in data["note"].lower()


# --- 2. Guardrails Advice Filter Tests ---

@pytest.mark.parametrize(
    "advice_query,expected_lang",
    [
        ("Which stock should I buy for 10x returns tomorrow?", "en"),
        ("What share can I invest in for quick profit?", "en"),
        ("Kaunsa share lu trading ke liye?", "en"),
        ("કયો શેર ખરીદવો જોઈએ?", "gu"),
    ],
)
def test_advice_queries_return_out_of_scope(client: TestClient, advice_query: str, expected_lang: str) -> None:
    """Acceptance check: Investment advice/recommendation queries return out_of_scope verdict."""
    response = client.post("/v1/check", json={"text": advice_query})
    assert response.status_code == 200
    data = response.json()

    assert data["verdict"] == "out_of_scope"
    assert data["score"] == 0.0
    assert len(data["reasons"]) == 0
    # Note mentions advice in either English, Gujarati, or Hindi
    assert any(term in data["note"].lower() for term in ("advice", "સલાહ", "सलाह"))


# --- 3. Rate Limiting Tests ---

def test_rate_limiter_blocks_31st_request(client: TestClient) -> None:
    """Acceptance check: 30 requests permitted per minute; 31st returns HTTP 429 uniform error."""
    limiter = get_rate_limiter()
    limiter.reset()

    # First 30 requests should succeed
    for i in range(30):
        res = client.get("/v1/privacy")
        assert res.status_code == 200, f"Request {i+1} failed"

    # 31st request should be rejected with 429
    res_31 = client.get("/v1/privacy")
    assert res_31.status_code == 429
    err = res_31.json()
    assert "error" in err
    assert err["error"]["code"] == "rate_limit_exceeded"
    assert "30 requests per minute" in err["error"]["message"]
    assert err["error"]["request_id"] != ""


# --- 4. Privacy & Third-Party Disclosure Tests ---

def test_privacy_disclosure_endpoint(client: TestClient) -> None:
    """Acceptance check: GET /v1/privacy returns zero-retention policy and component disclosures."""
    response = client.get("/v1/privacy")
    assert response.status_code == 200
    data = response.json()

    assert data["policy"] == "zero_persistence_by_design"
    assert data["storage"]["user_messages"] == "none"
    assert data["storage"]["database_present"] is False
    assert "request_body" in data["audit_logging"]["forbidden_fields"]
    assert "message_text" in data["audit_logging"]["forbidden_fields"]
    assert len(data["local_components"]) >= 3


# --- 5. Privacy Audit: Zero Body Logging ---

def test_zero_body_logging_during_check(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    """Acceptance check: Verifies that sensitive user message bodies are NEVER printed in log records."""
    unique_secret_phrase = "SECRET_UNTRACKED_TOKEN_99881122"
    message_text = f"Guaranteed 50% return daily on {unique_secret_phrase} to upi@ybl"

    with caplog.at_level(logging.INFO):
        response = client.post("/v1/check", json={"text": message_text})

    assert response.status_code == 200

    # Ensure the unique phrase was NEVER logged across all log records
    for record in caplog.records:
        assert unique_secret_phrase not in record.message
        assert "SECRET_UNTRACKED_TOKEN" not in record.message


# --- 6. Media Pipeline Orchestration Tests ---

def test_check_image_orchestrates_full_verdict(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance check: POST /v1/check/image orchestrates OCR and returns full CheckResult."""
    async def mock_ocr(image_bytes: bytes, mime_hint: str = "") -> IngestResult:
        return IngestResult(
            text="Guaranteed 30% profit every month. Transfer to scammer@ybl now!",
            source="ocr",
        )

    monkeypatch.setattr("app.api.routes_media.image_to_text", mock_ocr)

    valid_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa75\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("screenshot.png", valid_png, "image/png")}
    response = client.post("/v1/check/image", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "strong_red_flags"
    assert data["source"] == "ocr"
    assert "Guaranteed" in data["text"]


def test_check_audio_orchestrates_full_verdict(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance check: POST /v1/check/audio orchestrates STT and returns full CheckResult."""
    async def mock_stt(audio_bytes: bytes, mime_hint: str = "", lang_hint: str = "") -> IngestResult:
        return IngestResult(
            text="તમને ૧૦૦% ગેરંટીડ નફો મળશે, પૈસા આ UPI પર મોકલો: vip@ybl.",
            source="stt",
        )

    monkeypatch.setattr("app.api.routes_media.audio_to_text", mock_stt)

    valid_wav = (
        b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    files = {"file": ("note.wav", valid_wav, "audio/wav")}
    response = client.post("/v1/check/audio", files=files, data={"language": "gu"})

    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "strong_red_flags"
    assert data["source"] == "stt"
    assert data["language"] == "gu"
