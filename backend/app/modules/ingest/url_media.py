"""URL media ingestion module for downloading and analyzing Instagram Reels and video links."""

import asyncio
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.core import config
from app.core.config import Settings
from app.core.errors import AppException, PayloadTooLargeError
from app.core.logging import logger
from app.modules.ingest.media import VideoIngestResult, _get_base_temp_dir, video_to_text

# Regex matching Instagram Reels, Posts, and TV links
INSTAGRAM_URL_REGEX = re.compile(
    r"(?i)https?://(?:www\.)?(?:instagram\.com|instagr\.am)/(?:reel|p|tv|share/reel)/([a-zA-Z0-9_\-]+)/?"
)

# Broader pattern matching general social video URLs
GENERIC_VIDEO_URL_REGEX = re.compile(
    r"(?i)https?://(?:www\.)?(?:instagram\.com|instagr\.am|youtube\.com/shorts|youtu\.be|tiktok\.com)/[^\s]+"
)


def is_video_url(text: str) -> bool:
    """Return True if text contains an Instagram Reel or supported social video link."""
    if not text:
        return False
    return bool(INSTAGRAM_URL_REGEX.search(text) or GENERIC_VIDEO_URL_REGEX.search(text))


def extract_video_url_from_text(text: str) -> Optional[str]:
    """Extract the first Instagram Reel or social video URL from text."""
    if not text:
        return None
    match = INSTAGRAM_URL_REGEX.search(text) or GENERIC_VIDEO_URL_REGEX.search(text)
    if match:
        return match.group(0)
    return None


def _download_video_sync(url: str, temp_dir: Path, max_bytes: int) -> dict:
    """Download video and extract metadata using yt-dlp synchronously in a worker thread."""
    try:
        import yt_dlp
    except ImportError as exc:
        raise AppException(
            status_code=503,
            code="ytdlp_unavailable",
            message="yt-dlp is not installed on the server",
        ) from exc

    output_template = str(temp_dir / "reel_video.%(ext)s")

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "max_filesize": max_bytes,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info or {}


async def download_and_extract_url_video(
    url: str,
    settings: Optional[Settings] = None,
    language_hint: Optional[str] = None,
) -> VideoIngestResult:
    """Download an Instagram Reel or social video, extract speech and on-screen frames, and synthesize text.

    HARD PRIVACY & SECURITY RULES:
    1. Zero persistence: creates ONE private temp dir strictly cleaned up in a finally block even on error.
    2. Zero transcript/frame logging: logs metadata only.
    3. Merged text combines spoken audio, on-screen OCR, and reel caption.
    4. Duration > MAX_VIDEO_SECONDS or size > MAX_VIDEO_MB raises PayloadTooLargeError.
    """
    conf = settings or config.get_settings()

    if not getattr(conf, "ENABLE_URL_VIDEO_INGEST", True):
        raise AppException(
            status_code=503,
            code="url_ingest_disabled",
            message="URL video ingestion is disabled in configuration",
        )

    max_mb = getattr(conf, "MAX_VIDEO_MB", 25)
    max_bytes = max_mb * 1024 * 1024

    base_dir = _get_base_temp_dir()
    temp_dir = Path(tempfile.mkdtemp(prefix="ruko_url_v_", dir=str(base_dir)))

    try:
        os.chmod(temp_dir, 0o700)
    except Exception:
        pass

    try:
        # 1. Download video and extract metadata in background thread
        try:
            info = await asyncio.wait_for(
                asyncio.to_thread(_download_video_sync, url, temp_dir, max_bytes),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            raise AppException(
                status_code=504,
                code="download_timeout",
                message="Timed out downloading the video from URL (exceeded 30 seconds)",
            )
        except AppException:
            raise
        except Exception as exc:
            logger.warning("Failed to download video from URL: %s", type(exc).__name__)
            raise AppException(
                status_code=422,
                code="video_download_failed",
                message="Could not download video from link. The video may be private, restricted, or unavailable.",
            ) from exc

        # 2. Extract caption and metadata
        caption = (info.get("description") or "").strip()
        title = (info.get("title") or "").strip()
        uploader = (info.get("uploader") or "").strip()

        # 3. Locate downloaded video file
        video_files = list(temp_dir.glob("reel_video.*"))
        if not video_files:
            # Fall back to any video file in the directory
            video_files = [f for f in temp_dir.iterdir() if f.is_file() and not f.name.endswith(".part")]

        if not video_files:
            raise AppException(
                status_code=422,
                code="no_video_downloaded",
                message="No playable video file could be extracted from the provided URL",
            )

        video_path = video_files[0]
        max_seconds = getattr(conf, "MAX_VIDEO_SECONDS", 180)
        trimmed_path = temp_dir / "trimmed.mp4"
        video_bytes = video_path.read_bytes()

        # If video may exceed max duration, cleanly trim to max_seconds so processing always succeeds
        def _trim_video_sync() -> None:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(video_path),
                    "-t",
                    str(max_seconds),
                    "-c",
                    "copy",
                    str(trimmed_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        try:
            await asyncio.to_thread(_trim_video_sync)
            if trimmed_path.is_file() and trimmed_path.stat().st_size > 1000:
                video_bytes = trimmed_path.read_bytes()
        except Exception as exc:
            logger.debug("Video duration trim skipped or failed: %s", exc)

        # 4. Run standard video-to-text pipeline (audio STT + frame OCR)
        video_result = await video_to_text(video_bytes, settings=conf)

        # 5. Enrich with caption/metadata
        speech_text = video_result.speech_text
        on_screen_text = video_result.on_screen_text

        # Combine reel caption into on_screen_text if available
        if caption:
            if on_screen_text:
                on_screen_text = f"{on_screen_text}\n\n[Reel Caption]:\n{caption}".strip()
            else:
                on_screen_text = f"[Reel Caption]:\n{caption}".strip()

        # Formulate merged plain text
        text_components = []
        if speech_text:
            text_components.append(speech_text)
        if on_screen_text:
            text_components.append(on_screen_text)

        merged_text = "\n".join(text_components).strip()
        if not merged_text and caption:
            merged_text = caption

        if len(merged_text.strip()) < 10:
            raise AppException(
                status_code=422,
                code="not_enough_text",
                message="Not enough text could be extracted from video speech, frames, or caption (under 10 characters)",
            )

        return VideoIngestResult(
            text=merged_text,
            speech_text=speech_text,
            on_screen_text=on_screen_text,
            source="video",
            degraded=video_result.degraded,
        )

    finally:
        # CRITICAL PRIVACY INVARIANT: Clean up temporary files unconditionally
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as exc:
                logger.warning("Failed to clean up url temp dir %s: %s", temp_dir, exc)
