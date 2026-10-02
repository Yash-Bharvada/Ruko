"""Comprehensive acceptance tests for Module M11: Video / Reel Ingest."""

import glob
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import AppException, PayloadTooLargeError
from app.core.security import get_rate_limiter
from app.main import app
from app.modules.ingest.media import (
    _get_base_temp_dir,
    check_ffmpeg_available,
    sniff_video_mime,
    video_to_text,
)
from app.modules.ingest.ocr import IngestResult


@pytest.fixture(scope="session")
def sample_video_bytes() -> bytes:
    """Generate a valid, compact 10-second MP4 video using ffmpeg lavfi."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        temp_path = tf.name

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=navy:s=160x120:d=10",
        "-f",
        "lavfi",
        "-i",
        "sine=f=440:d=10",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        temp_path,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    video_data = Path(temp_path).read_bytes()
    try:
        os.remove(temp_path)
    except Exception:
        pass
    return video_data


@pytest.fixture
def client() -> TestClient:
    get_rate_limiter().reset()
    return TestClient(app)


# --- 1. Video Scam Speech Acceptance Check ---

@pytest.mark.asyncio
async def test_video_scam_speech_strong_red_flags(
    client: TestClient, sample_video_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Acceptance check: 10-15s video with mocked speech triggers strong_red_flags and input_source: video."""
    mock_speech = "Guaranteed 30% monthly returns join VIP group at t.me/vip_trade and send 5000 to trade@ybl"

    async def mock_audio_to_text(b: bytes, mime_hint: str = "", **kwargs: Any) -> IngestResult:
        return IngestResult(text=mock_speech, source="stt")

    async def mock_image_to_text(b: bytes, mime_hint: str = "", **kwargs: Any) -> IngestResult:
        return IngestResult(text="", source="ocr")

    monkeypatch.setattr("app.modules.ingest.media.audio_to_text", mock_audio_to_text)
    monkeypatch.setattr("app.modules.ingest.media.image_to_text", mock_image_to_text)

    files = {"file": ("reel.mp4", sample_video_bytes, "video/mp4")}
    response = client.post("/v1/check/media", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "strong_red_flags"
    assert data["input_source"] == "video"
    assert "Guaranteed" in data["speech_text"]
    assert len(data["reasons"]) >= 1


# --- 2. On-Screen Text & Caption Deduplication ---

@pytest.mark.asyncio
async def test_video_on_screen_text_deduplication(
    sample_video_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Acceptance check: Video with only on-screen text deduplicates repeated frame captions."""
    async def mock_audio_to_text(b: bytes, mime_hint: str = "", **kwargs: Any) -> IngestResult:
        return IngestResult(text="", source="stt")

    call_count = 0

    async def mock_image_to_text(b: bytes, mime_hint: str = "", **kwargs: Any) -> IngestResult:
        nonlocal call_count
        call_count += 1
        # Simulated captions across frames with repetitions
        if call_count % 2 == 1:
            return IngestResult(text="VIP Trading Club\nGuaranteed 50% Profit", source="ocr")
        else:
            return IngestResult(text="Guaranteed 50% Profit\nSend money to upi@ybl", source="ocr")

    monkeypatch.setattr("app.modules.ingest.media.audio_to_text", mock_audio_to_text)
    monkeypatch.setattr("app.modules.ingest.media.image_to_text", mock_image_to_text)

    result = await video_to_text(sample_video_bytes)
    assert result.source == "video"
    assert result.on_screen_text != ""

    # Check deduplication: lines should appear only once
    lines = [line.strip().lower() for line in result.on_screen_text.splitlines() if line.strip()]
    assert lines.count("guaranteed 50% profit") == 1
    assert lines.count("vip trading club") == 1


# --- 3. Format, Duration & Size Rejection ---

def test_video_format_and_oversize_rejection(client: TestClient, sample_video_bytes: bytes) -> None:
    """Acceptance check: EXE bytes -> 422, oversized -> 413, over-duration -> 413."""
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff" + (b"\x00" * 100)

    # 1. EXE bytes disguised as MP4
    files = {"file": ("x.mp4", exe_bytes, "video/mp4")}
    res_exe = client.post("/v1/check/media", files=files)
    assert res_exe.status_code == 422
    assert res_exe.json()["error"]["code"] == "invalid_video_format"

    # 2. Oversized payload check
    huge_bytes = sample_video_bytes + (b"\x00" * (26 * 1024 * 1024))  # 26MB > 25MB
    files_huge = {"file": ("large.mp4", huge_bytes, "video/mp4")}
    res_huge = client.post("/v1/check/media", files=files_huge)
    assert res_huge.status_code == 413


@pytest.mark.asyncio
async def test_over_duration_rejection(sample_video_bytes: bytes) -> None:
    """Acceptance check: Video duration exceeding MAX_VIDEO_SECONDS triggers 413."""
    # Settings with max 5s duration against 10s sample video
    short_settings = Settings(MAX_VIDEO_SECONDS=5)
    with pytest.raises(PayloadTooLargeError) as exc_info:
        await video_to_text(sample_video_bytes, settings=short_settings)

    assert exc_info.value.status_code == 413
    assert "exceeds maximum allowed limit" in exc_info.value.message


# --- 4. Temporary Directory Cleanliness (Zero Persistence) ---

@pytest.mark.asyncio
async def test_temp_dir_cleaned_up_on_success_and_error(
    sample_video_bytes: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Acceptance check: Private temp dir is deleted after success AND after forced exception."""
    base_dir = _get_base_temp_dir()

    def count_ruko_dirs() -> int:
        return len(glob.glob(str(base_dir / "ruko_v_*")))

    initial_dirs = count_ruko_dirs()

    # 1. Success execution
    async def mock_audio_success(b: bytes, **kwargs: Any) -> IngestResult:
        return IngestResult(text="Testing normal video transcript", source="stt")

    monkeypatch.setattr("app.modules.ingest.media.audio_to_text", mock_audio_success)
    res = await video_to_text(sample_video_bytes)
    assert res.source == "video"
    assert count_ruko_dirs() == initial_dirs, "Temp directory leaked after success"

    # 2. Forced exception during audio STT
    async def mock_audio_crash(b: bytes, **kwargs: Any) -> IngestResult:
        raise RuntimeError("CRITICAL FORCED STT EXCEPTION")

    monkeypatch.setattr("app.modules.ingest.media.audio_to_text", mock_audio_crash)
    # The pipeline catches STT error, records degraded, or raises if text is insufficient
    try:
        await video_to_text(sample_video_bytes)
    except Exception:
        pass

    assert count_ruko_dirs() == initial_dirs, "Temp directory leaked after exception"


# --- 5. Missing ffmpeg Graceful Degradation ---

def test_missing_ffmpeg_video_unavailable_only(client: TestClient, sample_video_bytes: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance check: Missing ffmpeg returns 503 video_unavailable for video; text, image, audio still work."""
    monkeypatch.setattr("app.modules.ingest.media.check_ffmpeg_available", lambda: False)

    # 1. Video returns 503
    files_video = {"file": ("sample.mp4", sample_video_bytes, "video/mp4")}
    res_video = client.post("/v1/check/media", files=files_video)
    assert res_video.status_code == 503
    assert res_video.json()["error"]["code"] == "video_unavailable"

    # 2. Text still works
    files_text = {"file": ("notes.txt", b"Safe note about stock market updates.", "text/plain")}
    res_text = client.post("/v1/check/media", files=files_text)
    assert res_text.status_code == 200
    assert res_text.json()["input_source"] == "text"


# --- 6. Transcribed Never Clear Rule on Video ---

def test_transcribed_never_clear_on_video(client: TestClient, sample_video_bytes: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance check: Clean transcribed video input returns cannot_verify, never no_red_flags_found."""
    clean_transcript = "Dear Customer, your bank transaction of INR 500 was completed on 01-Mar-2026."

    async def mock_audio_clean(b: bytes, **kwargs: Any) -> IngestResult:
        return IngestResult(text=clean_transcript, source="stt")

    monkeypatch.setattr("app.modules.ingest.media.audio_to_text", mock_audio_clean)

    files = {"file": ("clean_reel.mp4", sample_video_bytes, "video/mp4")}
    res = client.post("/v1/check/media", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "cannot_verify"
    assert data["input_source"] == "video"
    assert "transcription" in data["note"].lower()


# --- 7. Instagram Links Guardrail ---

def test_instagram_link_only_returns_hint_zero_outbound(client: TestClient) -> None:
    """Acceptance check: Instagram link with under ~30 other chars returns localized hint with zero outbound calls."""
    import httpx

    def forbidden_request(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("CRITICAL VIOLATION: Outbound HTTP request made for Instagram link!")

    with patch.object(httpx.AsyncClient, "request", side_effect=forbidden_request):
        payload = {"text": "Look at this https://www.instagram.com/reel/DC45_xyz123/"}
        res = client.post("/v1/check", json=payload)

    assert res.status_code == 200
    data = res.json()
    assert data["hint"] is not None
    assert "cannot open Instagram links" in data["hint"]


# --- 8. Disabled Third Party AI Media Endpoint Check ---

def test_disabled_third_party_ai_returns_503(client: TestClient, sample_video_bytes: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance check: When ENABLE_THIRD_PARTY_AI=False, audio/image/video return 503, text still works."""
    from app.core import config

    disabled_settings = Settings(ENABLE_THIRD_PARTY_AI=False)
    monkeypatch.setattr(config, "get_settings", lambda: disabled_settings)

    # Video returns 503
    files_video = {"file": ("video.mp4", sample_video_bytes, "video/mp4")}
    res_vid = client.post("/v1/check/media", files=files_video)
    assert res_vid.status_code == 503

    # Text returns 200
    files_text = {"file": ("msg.txt", b"Regular plain message text here.", "text/plain")}
    res_text = client.post("/v1/check/media", files=files_text)
    assert res_text.status_code == 200
