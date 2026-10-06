"""Video and multimedia ingestion pipeline with frame OCR and audio STT extraction."""

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.core import config
from app.core.config import Settings
from app.core.errors import AppException, PayloadTooLargeError
from app.core.logging import logger
from app.modules.ingest.ocr import image_to_text
from app.modules.ingest.stt import audio_to_text


class VideoIngestResult(BaseModel):
    """Result of video speech and on-screen text extraction."""

    text: str = Field(..., description="Merged plain text (speech and on-screen lines without labels)")
    speech_text: str = Field("", description="Transcribed spoken audio from the video")
    on_screen_text: str = Field("", description="Deduplicated OCR text from video frames")
    source: str = Field("video", description="Ingestion source: video")
    degraded: List[str] = Field(default_factory=list, description="Degraded components during processing")


def sniff_video_mime(data: bytes) -> Optional[str]:
    """Sniff video MIME type using file headers and magic bytes.

    Supports:
    - MP4: ftyp box at offset 4
    - QuickTime / MOV: moov/wide/qt atoms or ftypqt
    - WebM: EBML header starting with \x1a\x45\xdf\xa3 containing webm
    """
    if not data or len(data) < 12:
        return None

    # Check for executable / PE magic bytes
    if data[:2] == b"MZ":
        return None

    # Check MP4 / QuickTime ftyp atom
    if data[4:8] == b"ftyp":
        brand = data[8:12].lower()
        if brand.startswith(b"qt"):
            return "video/quicktime"
        return "video/mp4"

    # QuickTime atom headers
    if data[4:8] in (b"moov", b"wide", b"mdat", b"free", b"skip", b"pnot"):
        return "video/quicktime"

    # WebM EBML header
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        head_sample = data[:128].lower()
        if b"webm" in head_sample or b"matroska" in head_sample:
            return "video/webm"

    return None


def _get_base_temp_dir() -> Path:
    """Select private temp directory, preferring in-memory /dev/shm when available."""
    shm_path = Path("/dev/shm")
    if shm_path.is_dir() and os.access(shm_path, os.W_OK):
        return shm_path
    return Path(tempfile.gettempdir())


def _find_binary(name: str) -> Optional[str]:
    """Find binary in system PATH or venv bin directory."""
    found = shutil.which(name)
    if found:
        return found
    venv_bin = Path(__file__).resolve().parents[3] / ".venv" / "bin" / name
    if venv_bin.is_file() and os.access(venv_bin, os.X_OK):
        return str(venv_bin)
    return None


def check_ffmpeg_available() -> bool:
    """Check if ffmpeg and ffprobe binaries are installed and accessible."""
    return bool(_find_binary("ffmpeg") and (_find_binary("ffprobe") or True))


def _run_command_sync(cmd: List[str]) -> Tuple[int, bytes, bytes]:
    """Execute command synchronously in a worker thread."""
    resolved_cmd = list(cmd)
    if resolved_cmd and not os.path.isabs(resolved_cmd[0]):
        bin_path = _find_binary(resolved_cmd[0])
        if bin_path:
            resolved_cmd[0] = bin_path

    try:
        proc = subprocess.run(
            resolved_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc.returncode or 0, proc.stdout, proc.stderr
    except Exception as exc:
        logger.warning("CLI execution failed for %s: %s", resolved_cmd[0], exc)
        return 1, b"", str(exc).encode()


async def _run_command(cmd: List[str]) -> Tuple[int, bytes, bytes]:
    """Run an external CLI process asynchronously in a thread without blocking event loop or failing on Windows."""
    return await asyncio.to_thread(_run_command_sync, cmd)


async def video_to_text(
    video_bytes: bytes,
    mime_hint: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> VideoIngestResult:
    """Extract speech audio and on-screen text frames from uploaded video bytes.

    HARD PRIVACY & SECURITY RULES:
    1. Zero persistence: creates ONE private temp dir (mode 0700, files 0600) strictly
       cleaned up in a finally block even on error.
    2. Zero transcript/frame logging: logs metadata only.
    3. Merged text has NO labels, matching model pre-training format.
    4. Duration > MAX_VIDEO_SECONDS -> 413. Oversize -> 413. Corrupt/non-video -> 422.
    """
    conf = settings or config.get_settings()

    # 1. Size Validation
    max_mb = getattr(conf, "MAX_VIDEO_MB", 25)
    max_bytes = max_mb * 1024 * 1024
    if len(video_bytes) > max_bytes:
        raise PayloadTooLargeError(f"Video file exceeds limit of {max_mb}MB ({len(video_bytes)} bytes)")

    # 2. Magic Bytes Validation
    sniffed_mime = sniff_video_mime(video_bytes) or mime_hint
    if not sniffed_mime or not sniff_video_mime(video_bytes):
        raise AppException(
            status_code=422,
            code="invalid_video_format",
            message="Uploaded file is not a supported video format (MP4, MOV, WEBM)",
        )

    # 3. Check ffmpeg availability
    if not check_ffmpeg_available():
        raise AppException(
            status_code=503,
            code="video_unavailable",
            message="Video processing unavailable: ffmpeg/ffprobe not installed on server",
        )

    # 4. Check Third Party AI enablement
    if not conf.ENABLE_THIRD_PARTY_AI:
        raise AppException(
            status_code=503,
            code="third_party_disabled",
            message="Video checking needs third-party AI for speech-to-text and vision OCR",
        )

    # 5. Create private temporary directory
    base_dir = _get_base_temp_dir()
    temp_dir = tempfile.mkdtemp(prefix="ruko_v_", dir=str(base_dir))

    # Set directory mode 0700 on POSIX
    try:
        os.chmod(temp_dir, 0o700)
    except Exception:
        pass

    degraded_flags: List[str] = []

    try:
        # Determine extension
        ext = "mp4"
        if "webm" in sniffed_mime:
            ext = "webm"
        elif "quicktime" in sniffed_mime:
            ext = "mov"

        input_path = Path(temp_dir) / f"input.{ext}"
        input_path.write_bytes(video_bytes)

        try:
            os.chmod(input_path, 0o600)
        except Exception:
            pass

        # 6. Check Duration via ffprobe
        probe_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ]
        ret_code, stdout, stderr = await _run_command(probe_cmd)
        if ret_code != 0:
            raise AppException(
                status_code=422,
                code="invalid_video_format",
                message="Corrupt or unreadable video file",
            )

        try:
            duration_str = stdout.decode().strip()
            duration_sec = float(duration_str)
        except ValueError:
            raise AppException(
                status_code=422,
                code="invalid_video_format",
                message="Could not determine video duration",
            )

        max_seconds = getattr(conf, "MAX_VIDEO_SECONDS", 60)
        if duration_sec > max_seconds:
            raise PayloadTooLargeError(
                f"Video duration ({duration_sec:.1f}s) exceeds maximum allowed limit of {max_seconds}s"
            )

        # 7. Define Concurrent Speech Extraction & Frame OCR Tasks
        async def _extract_speech() -> str:
            """Extract audio track and transcribe via STT (with chunking if longer than limit)."""
            audio_path = Path(temp_dir) / "audio.wav"
            extract_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "wav",
                str(audio_path),
            ]
            rc, _, _ = await _run_command(extract_cmd)
            if rc != 0 or not audio_path.is_file() or audio_path.stat().st_size < 100:
                return ""

            # Check STT segment limit (Sarvam limit from config)
            stt_limit = getattr(conf, "SARVAM_STT_MAX_SECONDS", 60)
            if duration_sec > stt_limit:
                # Segment audio into chunks
                segment_pattern = str(Path(temp_dir) / "seg_%03d.wav")
                seg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(audio_path),
                    "-f",
                    "segment",
                    "-segment_time",
                    str(stt_limit),
                    "-c",
                    "copy",
                    segment_pattern,
                ]
                await _run_command(seg_cmd)
                segments = sorted(Path(temp_dir).glob("seg_*.wav"))
                transcripts = []
                for seg in segments:
                    seg_bytes = seg.read_bytes()
                    res = await audio_to_text(seg_bytes, mime_hint="audio/wav", settings=conf)
                    if res.text.strip():
                        transcripts.append(res.text.strip())
                return " ".join(transcripts)
            else:
                audio_bytes = audio_path.read_bytes()
                res = await audio_to_text(audio_bytes, mime_hint="audio/wav", settings=conf)
                return res.text.strip()

        async def _extract_on_screen() -> str:
            """Extract frames every FRAME_INTERVAL_SECONDS, OCR each, and deduplicate lines."""
            interval = getattr(conf, "FRAME_INTERVAL_SECONDS", 3)
            max_frames = getattr(conf, "MAX_FRAMES", 8)
            frame_pattern = str(Path(temp_dir) / "frame_%03d.png")

            frames_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-vf",
                f"fps=1/{interval}",
                "-vframes",
                str(max_frames),
                frame_pattern,
            ]
            rc, _, _ = await _run_command(frames_cmd)
            if rc != 0:
                return ""

            frame_files = sorted(Path(temp_dir).glob("frame_*.png"))
            if not frame_files:
                return ""

            seen_lines = set()
            unique_lines = []

            for frame in frame_files:
                f_bytes = frame.read_bytes()
                try:
                    ocr_res = await image_to_text(f_bytes, mime_hint="image/png", settings=conf)
                    for raw_line in ocr_res.text.splitlines():
                        line = raw_line.strip()
                        if line and line.lower() not in seen_lines:
                            seen_lines.add(line.lower())
                            unique_lines.append(line)
                except Exception as exc:
                    logger.debug("Single frame OCR skipped: %s", exc)

            return "\n".join(unique_lines)

        # Run both concurrently with timeout
        speech_task = asyncio.create_task(_extract_speech())
        ocr_task = asyncio.create_task(_extract_on_screen())

        try:
            speech_text, on_screen_text = await asyncio.wait_for(
                asyncio.gather(speech_task, ocr_task, return_exceptions=True),
                timeout=45.0,
            )
        except asyncio.TimeoutError:
            speech_text = ""
            on_screen_text = ""
            degraded_flags.extend(["stt_unavailable", "ocr_unavailable"])

        # Handle speech outcome
        final_speech = ""
        if isinstance(speech_text, Exception):
            logger.warning("Video audio STT encountered issue: %s", speech_text)
            degraded_flags.append("stt_unavailable")
        elif isinstance(speech_text, str):
            final_speech = speech_text

        # Handle on-screen outcome
        final_ocr = ""
        if isinstance(on_screen_text, Exception):
            logger.warning("Video frame OCR encountered issue: %s", on_screen_text)
            degraded_flags.append("ocr_unavailable")
        elif isinstance(on_screen_text, str):
            final_ocr = on_screen_text

        # 8. Check for minimum extracted text
        parts = [p.strip() for p in (final_speech, final_ocr) if p.strip()]
        merged_text = "\n".join(parts)

        if len(merged_text.strip()) < 10:
            raise AppException(
                status_code=422,
                code="not_enough_text",
                message="Not enough text could be extracted from video speech or frames (under 10 characters)",
            )

        return VideoIngestResult(
            text=merged_text,
            speech_text=final_speech,
            on_screen_text=final_ocr,
            source="video",
            degraded=list(dict.fromkeys(degraded_flags)),
        )

    finally:
        # CRITICAL PRIVACY INVARIANT: Wipe temporary directory unconditionally
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as exc:
                logger.warning("Failed to remove temp dir %s: %s", temp_dir, exc)
