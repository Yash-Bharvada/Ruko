"""Unit and integration tests for Instagram Reel and video URL ingestion pipeline."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.security import get_rate_limiter
from app.main import app
from app.modules.ingest.media import VideoIngestResult
from app.modules.ingest.url_media import (
    extract_video_url_from_text,
    is_video_url,
)


@pytest.fixture
def client() -> TestClient:
    get_rate_limiter().reset()
    return TestClient(app)


def test_is_video_url_patterns() -> None:
    """Verify regex correctly identifies Instagram Reel and post links."""
    assert is_video_url("https://www.instagram.com/reel/Dd1ZAstNqe9/?stkn=xyz")
    assert is_video_url("https://instagram.com/p/C5abcdef123/")
    assert is_video_url("Check this: https://www.instagram.com/reel/12345/ now!")
    assert is_video_url("https://www.youtube.com/shorts/abcdef")
    assert not is_video_url("https://www.sebi.gov.in/registry")
    assert not is_video_url("Just a plain text message about stocks")


def test_extract_video_url_from_text() -> None:
    """Verify URL extraction extracts clean URLs from mixed text."""
    text = "Look at this reel https://www.instagram.com/reel/Dd1ZAstNqe9/?stkn=123 please verify"
    extracted = extract_video_url_from_text(text)
    assert extracted is not None
    assert "https://www.instagram.com/reel/Dd1ZAstNqe9/" in extracted


def test_check_url_endpoint_success(client: TestClient) -> None:
    """Verify POST /v1/check/url runs pipeline and returns full CheckResult."""
    mock_result = VideoIngestResult(
        text="Invest in VIP group for 50% guaranteed return. Send money to personal UPI.",
        speech_text="Invest in VIP group for 50% guaranteed return.",
        on_screen_text="[Reel Caption]: Send money to personal UPI.",
        source="video",
        degraded=[],
    )

    with patch(
        "app.api.routes_media.download_and_extract_url_video",
        new=AsyncMock(return_value=mock_result),
    ):
        payload = {
            "url": "https://www.instagram.com/reel/Dd1ZAstNqe9/",
            "language": "en",
        }
        res = client.post("/v1/check/url", json=payload)

    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] in ("strong_red_flags", "cannot_verify")
    assert data["source"] == "video"
    assert data["speech_text"] == "Invest in VIP group for 50% guaranteed return."
    assert "[Reel Caption]" in data["on_screen_text"]
    assert len(data["reasons"]) > 0


def test_check_url_endpoint_invalid_url(client: TestClient) -> None:
    """Verify POST /v1/check/url returns 422 for invalid/unreachable video links."""
    from app.core.errors import AppException

    with patch(
        "app.api.routes_media.download_and_extract_url_video",
        new=AsyncMock(side_effect=AppException(status_code=422, code="video_download_failed", message="Download failed")),
    ):
        payload = {"url": "https://www.instagram.com/reel/invalid_reel_999/"}
        res = client.post("/v1/check/url", json=payload)

    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "video_download_failed"


def test_check_main_endpoint_auto_extracts_instagram_reel(client: TestClient) -> None:
    """Verify POST /v1/check automatically detects Instagram link and extracts video & audio."""
    mock_result = VideoIngestResult(
        text="Double your money in 24 hours guaranteed tips group.",
        speech_text="Double your money in 24 hours.",
        on_screen_text="[Reel Caption]: Guaranteed tips group.",
        source="video",
        degraded=[],
    )

    with patch(
        "app.api.routes_check.download_and_extract_url_video",
        new=AsyncMock(return_value=mock_result),
    ):
        payload = {"text": "https://www.instagram.com/reel/Dd1ZAstNqe9/?stkn=MTl1bm8zdjlzd3N5aQ=="}
        res = client.post("/v1/check", json=payload)

    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "video"
    assert data["speech_text"] == "Double your money in 24 hours."
    assert "[Reel Caption]" in data["on_screen_text"]
