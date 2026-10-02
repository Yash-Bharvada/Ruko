"""Tests for Module M5: Ingest (Screenshot OCR and Voice-Note STT)."""

import io
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import AppException, PayloadTooLargeError
from app.main import app, create_app
from app.modules.extractor.llm_client import LLMClient
from app.modules.ingest.ocr import (
    IngestResult,
    image_to_text,
    sniff_image_mime,
)
from app.modules.ingest.stt import (
    audio_to_text,
    sniff_audio_mime,
)


# Minimal genuine file headers
VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa75\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82"
)

VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"

VALID_WAV_BYTES = (
    b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
    b"\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
)

EXE_BYTES = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00\xb8\x00\x00\x00"


class MockVisionLLMClient(LLMClient):
    """Mock vision LLM client returning sample transcribed text."""

    def __init__(self, transcribed_text: str = "Guaranteed 25% monthly return on investment") -> None:
        super().__init__(settings=Settings(LLM_API_KEY="test_key", ENABLE_THIRD_PARTY_AI=True))
        self.transcribed_text = transcribed_text
        self.call_count = 0

    async def generate_text_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str = "",
    ) -> str:
        self.call_count += 1
        return self.transcribed_text


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --- Magic Byte Sniffing Tests ---

def test_magic_byte_sniffing_images() -> None:
    """Verify magic byte detection distinguishes real images from disguised files."""
    assert sniff_image_mime(VALID_PNG_BYTES) == "image/png"
    assert sniff_image_mime(VALID_JPEG_BYTES) == "image/jpeg"
    assert sniff_image_mime(b"RIFF1234WEBP...") == "image/webp"

    # Disguised EXE or random text
    assert sniff_image_mime(EXE_BYTES) is None
    assert sniff_image_mime(b"hello world") is None
    assert sniff_image_mime(b"") is None


def test_magic_byte_sniffing_audio() -> None:
    """Verify magic byte detection distinguishes real audio from non-audio files."""
    assert sniff_audio_mime(VALID_WAV_BYTES) == "audio/wav"
    assert sniff_audio_mime(b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00") == "audio/ogg"
    assert sniff_audio_mime(b"ID3\x03\x00\x00\x00\x00\x00\x00\x00\x00") == "audio/mp3"
    assert sniff_audio_mime(b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01") == "audio/webm"
    assert sniff_audio_mime(b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00") == "audio/m4a"

    # Disguised EXE or random text
    assert sniff_audio_mime(EXE_BYTES) is None
    assert sniff_audio_mime(b"Plain text note") is None
    assert sniff_audio_mime(b"") is None


# --- OCR Tests ---

@pytest.mark.asyncio
async def test_valid_image_ocr_success() -> None:
    """Acceptance check: Valid small PNG transcribed to text in memory."""
    mock_llm = MockVisionLLMClient("Guaranteed 30% monthly return, pay 5000 to trade@ybl")
    result = await image_to_text(VALID_PNG_BYTES, client=mock_llm)

    assert mock_llm.call_count == 1
    assert result.source == "ocr"
    assert "Guaranteed 30%" in result.text


@pytest.mark.asyncio
async def test_image_with_png_extension_but_exe_bytes_rejected() -> None:
    """Acceptance check: File with PNG mime/ext but EXE bytes is rejected with 422."""
    mock_llm = MockVisionLLMClient()
    with pytest.raises(AppException) as exc_info:
        await image_to_text(EXE_BYTES, client=mock_llm)

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "invalid_image_format"
    assert mock_llm.call_count == 0


@pytest.mark.asyncio
async def test_oversized_image_rejected_with_413() -> None:
    """Acceptance check: Image exceeding MAX_IMAGE_MB triggers 413 uniform error."""
    mock_llm = MockVisionLLMClient()
    settings = Settings(MAX_IMAGE_MB=1, LLM_API_KEY="test_key", ENABLE_THIRD_PARTY_AI=True)
    large_image = VALID_PNG_BYTES + (b"\x00" * (2 * 1024 * 1024))  # 2MB > 1MB

    with pytest.raises(PayloadTooLargeError) as exc_info:
        await image_to_text(large_image, settings=settings, client=mock_llm)

    assert exc_info.value.status_code == 413
    assert exc_info.value.code == "payload_too_large"


@pytest.mark.asyncio
async def test_ocr_empty_or_short_extraction_triggers_422() -> None:
    """Acceptance check: OCR producing empty or < 10 characters returns 422 not_enough_text."""
    # Under 10 characters
    mock_llm = MockVisionLLMClient("Hi!")
    with pytest.raises(AppException) as exc_info:
        await image_to_text(VALID_PNG_BYTES, client=mock_llm)

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "not_enough_text"


@pytest.mark.asyncio
async def test_ocr_disabled_third_party_ai_returns_503() -> None:
    """Acceptance check: When ENABLE_THIRD_PARTY_AI=False, returns 503 and zero outbound calls."""
    settings = Settings(ENABLE_THIRD_PARTY_AI=False, LLM_API_KEY="test_key")
    mock_llm = MockVisionLLMClient()

    with pytest.raises(AppException) as exc_info:
        await image_to_text(VALID_PNG_BYTES, settings=settings, client=mock_llm)

    assert exc_info.value.status_code == 503
    assert "image/voice checking needs third-party AI" in exc_info.value.message
    assert mock_llm.call_count == 0


# --- Audio STT Tests ---

@pytest.mark.asyncio
async def test_valid_audio_stt_success() -> None:
    """Acceptance check: Valid WAV audio transcribed via Sarvam STT in memory."""
    import httpx

    def mock_sarvam(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("api-subscription-key") == "mock_sarvam_key"
        return httpx.Response(
            200,
            json={
                "transcript": "Roj 5% nafo guaranteed che, aaje j jodavo",
                "language_code": "gu-IN",
            },
        )

    transport = httpx.MockTransport(mock_sarvam)
    async with httpx.AsyncClient(transport=transport) as http_client:
        settings = Settings(
            ENABLE_THIRD_PARTY_AI=True,
            SARVAM_API_KEY="mock_sarvam_key",
        )
        result = await audio_to_text(
            VALID_WAV_BYTES,
            lang_hint="gu",
            settings=settings,
            http_client=http_client,
        )

        assert result.source == "stt"
        assert "Roj 5% nafo" in result.text
        assert result.language == "gu-IN"


@pytest.mark.asyncio
async def test_audio_with_wav_extension_but_exe_bytes_rejected() -> None:
    """Acceptance check: Audio file with EXE bytes is rejected with 422 invalid_audio_format."""
    settings = Settings(ENABLE_THIRD_PARTY_AI=True, SARVAM_API_KEY="key")
    with pytest.raises(AppException) as exc_info:
        await audio_to_text(EXE_BYTES, settings=settings)

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "invalid_audio_format"


@pytest.mark.asyncio
async def test_audio_oversized_rejected_with_413() -> None:
    """Acceptance check: Audio exceeding MAX_AUDIO_MB triggers 413 uniform error."""
    settings = Settings(MAX_AUDIO_MB=1, SARVAM_API_KEY="key", ENABLE_THIRD_PARTY_AI=True)
    large_audio = VALID_WAV_BYTES + (b"\x00" * (2 * 1024 * 1024))  # 2MB > 1MB

    with pytest.raises(PayloadTooLargeError) as exc_info:
        await audio_to_text(large_audio, settings=settings)

    assert exc_info.value.status_code == 413
    assert exc_info.value.code == "payload_too_large"


@pytest.mark.asyncio
async def test_audio_disabled_third_party_ai_returns_503() -> None:
    """Acceptance check: Audio checking with third party disabled returns 503."""
    settings = Settings(ENABLE_THIRD_PARTY_AI=False, SARVAM_API_KEY="key")
    with pytest.raises(AppException) as exc_info:
        await audio_to_text(VALID_WAV_BYTES, settings=settings)

    assert exc_info.value.status_code == 503
    assert "image/voice checking needs third-party AI" in exc_info.value.message


# --- Zero Disk Writing & Log Privacy Assertions ---

@pytest.mark.asyncio
async def test_ingest_never_writes_to_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance check: Ingestion is strictly in-memory; fails if disk write attempted."""
    def forbidden_write(*args: object, **kwargs: object) -> None:
        raise AssertionError("CRITICAL VIOLATION: Disk write attempted during ingestion!")

    # Monkeypatch open to fail for write modes
    import builtins
    orig_open = builtins.open

    def guarded_open(file: object, mode: str = "r", *args: object, **kwargs: object) -> object:
        if any(w in mode for w in ("w", "a", "+", "x")):
            raise AssertionError(f"CRITICAL VIOLATION: File opened in write mode: {mode}")
        return orig_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)

    mock_llm = MockVisionLLMClient("Legitimate investment notice from regulator")
    result = await image_to_text(VALID_PNG_BYTES, client=mock_llm)
    assert result.source == "ocr"


# --- HTTP API Route Tests ---

def test_api_check_image_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance check: POST /v1/check/image returns {text, source} with mocked OCR."""
    async def mock_image_to_text(b: bytes, mime_hint: str = "") -> IngestResult:
        return IngestResult(text="Extracted text from test screenshot", source="ocr")

    monkeypatch.setattr("app.api.routes_media.image_to_text", mock_image_to_text)

    files = {"file": ("screenshot.png", VALID_PNG_BYTES, "image/png")}
    response = client.post("/v1/check/image", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "ocr"
    assert "Extracted text" in data["text"]


def test_api_check_audio_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance check: POST /v1/check/audio returns {text, source} with mocked STT."""
    async def mock_audio_to_text(b: bytes, mime_hint: str = "", lang_hint: str = "") -> IngestResult:
        return IngestResult(text="Extracted audio transcript from voice note", source="stt")

    monkeypatch.setattr("app.api.routes_media.audio_to_text", mock_audio_to_text)

    files = {"file": ("voicenote.wav", VALID_WAV_BYTES, "audio/wav")}
    response = client.post("/v1/check/audio", files=files, data={"language": "hi"})

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "stt"
    assert "Extracted audio" in data["text"]


def test_api_check_image_rejected_exe_bytes(client: TestClient) -> None:
    """Acceptance check: POST /v1/check/image with EXE bytes returns 422 uniform error."""
    files = {"file": ("malicious.png", EXE_BYTES, "image/png")}
    response = client.post("/v1/check/image", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "invalid_image_format"
