"""Tests for Module M7: Voice Output (TTS with Safe Browser Speech Fallback)."""

import pytest
from typing import Any, Dict
import httpx
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.modules.voice.tts import (
    AudioResult,
    BrowserSpeechFallback,
    SpeakRequest,
    _tts_cache,
    build_spoken_script,
    map_language_to_bcp47,
    synthesize_speech,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --- Script Builder Tests ---

def test_build_spoken_script_structure() -> None:
    """Acceptance check: Assembles spoken script from verdict note + up to 3 reason sentences."""
    script_en = build_spoken_script(
        verdict="strong_red_flags",
        reason_codes=["guaranteed_returns", "personal_upi_payment"],
        lang="en",
    )
    assert "Do not pay or share OTP/PIN" in script_en
    assert "Promises guaranteed or risk-free returns" in script_en
    assert "Asks to send money to a personal or third-party UPI address" in script_en

    # Multilingual: Gujarati
    script_gu = build_spoken_script(
        verdict="strong_red_flags",
        reason_codes=["guaranteed_returns"],
        lang="gu",
    )
    assert "પૈસા મોકલશો નહીં કે ઓટીપી/પિન શેર કરશો નહીં" in script_gu
    assert "ગેરંટીડ કે જોખમ વગરના નફાનો વાયદો કરે છે" in script_gu


def test_build_spoken_script_length_limit_and_whole_sentence_trimming() -> None:
    """Acceptance check: Script never exceeds max_chars; trims by dropping last reason sentence, not mid-sentence."""
    # Build with small limit (e.g. 120 chars)
    verdict = "strong_red_flags"
    reason_codes = [
        "guaranteed_returns",
        "unrealistic_return_claim",
        "upfront_payment_request",
    ]
    small_limit = 120
    script = build_spoken_script(verdict, reason_codes, lang="en", max_chars=small_limit)

    assert len(script) <= small_limit
    # Must end with punctuation, not a cut-off word
    assert script.endswith((".", "!", "?"))
    # The note must be present
    assert "Do not pay or share OTP/PIN" in script


def test_map_language_to_bcp47() -> None:
    """Verify BCP-47 tag mapping for browser speech and Sarvam."""
    assert map_language_to_bcp47("hi") == "hi-IN"
    assert map_language_to_bcp47("gu") == "gu-IN"
    assert map_language_to_bcp47("en") == "en-IN"
    assert map_language_to_bcp47("unknown") == "en-IN"
    assert map_language_to_bcp47(None) == "en-IN"


# --- Provider Synthesis & LRU Cache Tests ---

@pytest.mark.asyncio
async def test_valid_request_synthesizes_audio_and_second_hits_cache() -> None:
    """Acceptance check: Valid request synthesizes audio; second identical request hits LRU cache."""
    call_count = 0

    def mock_sarvam_tts(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json={"audios": ["UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="]},
        )

    transport = httpx.MockTransport(mock_sarvam_tts)
    async with httpx.AsyncClient(transport=transport) as http_client:
        settings = Settings(
            ENABLE_THIRD_PARTY_AI=True,
            SARVAM_API_KEY="mock_tts_key",
        )
        _tts_cache.clear()

        text = "Do not pay or share OTP/PIN. Check with an official source."

        # 1. First call -> invokes provider
        res1 = await synthesize_speech(text, lang="en", settings=settings, http_client=http_client)
        assert isinstance(res1, AudioResult)
        assert res1.source == "sarvam"
        assert res1.audio_base64 != ""
        assert call_count == 1

        # 2. Second identical call -> served from in-memory LRU cache
        res2 = await synthesize_speech(text, lang="en", settings=settings, http_client=http_client)
        assert isinstance(res2, AudioResult)
        assert res2.audio_base64 == res1.audio_base64
        # Assert provider was NOT called a second time
        assert call_count == 1


@pytest.mark.asyncio
async def test_provider_failure_or_missing_key_returns_browser_fallback_http_200() -> None:
    """Acceptance check: Provider 500 / timeout / missing key returns browser_speech fallback."""
    # 1. Missing key
    settings_no_key = Settings(ENABLE_THIRD_PARTY_AI=True, SARVAM_API_KEY="")
    text = "Verify with SEBI or your bank before acting."
    res_no_key = await synthesize_speech(text, lang="hi", settings=settings_no_key)

    assert isinstance(res_no_key, BrowserSpeechFallback)
    assert res_no_key.source == "browser_speech"
    assert res_no_key.text == text
    assert res_no_key.lang_code == "hi-IN"

    # 2. Provider 500
    def mock_500(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "internal error"})

    transport_500 = httpx.MockTransport(mock_500)
    async with httpx.AsyncClient(transport=transport_500) as http_client:
        settings_key = Settings(ENABLE_THIRD_PARTY_AI=True, SARVAM_API_KEY="key")
        res_500 = await synthesize_speech("Any text", lang="gu", settings=settings_key, http_client=http_client)
        assert isinstance(res_500, BrowserSpeechFallback)
        assert res_500.source == "browser_speech"
        assert res_500.lang_code == "gu-IN"


# --- HTTP API Endpoint /v1/speak Tests ---

def test_api_speak_success_with_fallback(client: TestClient) -> None:
    """Acceptance check: POST /v1/speak with valid payload returns HTTP 200 (fallback when no API key)."""
    payload = {
        "verdict": "strong_red_flags",
        "reason_codes": ["guaranteed_returns", "personal_upi_payment"],
        "language": "hi",
    }
    response = client.post("/v1/speak", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["source"] in ("sarvam", "browser_speech")
    assert "text" in data or "audio_base64" in data


def test_api_speak_rejects_free_text_field_with_422(client: TestClient) -> None:
    """Acceptance check: Free-text fields are strictly forbidden and rejected with HTTP 422."""
    malicious_payload = {
        "verdict": "strong_red_flags",
        "reason_codes": ["guaranteed_returns"],
        "language": "en",
        "text": "Arbitrary unvetted user text saying buy this stock!",
    }
    response = client.post("/v1/speak", json=malicious_payload)

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "validation_error"
