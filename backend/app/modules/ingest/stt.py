"""Voice-note and audio STT ingestion module using Sarvam AI."""

import asyncio
from typing import Any, Dict, Optional
import httpx
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import AppException, PayloadTooLargeError
from app.core.logging import logger
from app.modules.ingest.ocr import IngestResult


def sniff_audio_mime(audio_bytes: bytes) -> Optional[str]:
    """Sniff magic bytes to verify WAV, MP3, OGG, WEBM, or M4A audio format.

    Rejects files whose headers do not strictly match genuine audio signatures.
    """
    if len(audio_bytes) < 12:
        return None

    # WAV: RIFF....WAVE
    if audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return "audio/wav"

    # OGG: OggS
    if audio_bytes.startswith(b"OggS"):
        return "audio/ogg"

    # WEBM: \x1a\x45\xdf\xa3
    if audio_bytes.startswith(b"\x1a\x45\xdf\xa3"):
        return "audio/webm"

    # MP3: ID3 or sync frame \xff\xe0+
    if audio_bytes.startswith(b"ID3"):
        return "audio/mp3"
    if audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xE0) == 0xE0:
        return "audio/mp3"

    # M4A / MP4 container: bytes 4-8 == b"ftyp"
    if audio_bytes[4:8] == b"ftyp":
        return "audio/m4a"

    return None


def map_language_to_sarvam_code(lang_hint: Optional[str]) -> str:
    """Map language hint to Sarvam supported language code (hi-IN, gu-IN, en-IN, or unknown)."""
    if not lang_hint:
        return "unknown"
    hint_clean = lang_hint.lower().strip()
    if hint_clean in ("hi", "hi-in", "hindi"):
        return "hi-IN"
    if hint_clean in ("gu", "gu-in", "gujarati"):
        return "gu-IN"
    if hint_clean in ("en", "en-in", "english"):
        return "en-IN"
    return "unknown"


async def audio_to_text(
    audio_bytes: bytes,
    mime_hint: Optional[str] = None,
    lang_hint: Optional[str] = None,
    settings: Optional[Settings] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> IngestResult:
    """Convert audio voice note into text in-memory using Sarvam STT.

    Guarantees:
    - In-memory only: zero disk writing.
    - Magic byte sniffing rejects non-audio payloads.
    - Enforces MAX_AUDIO_MB with 413.
    - 503 if third-party AI is disabled or unconfigured.
    - 422 'not_enough_text' if transcribed text < 10 chars.
    - Never logs audio bytes or transcribed content.
    """
    conf = settings or get_settings()

    # 1. Feature flag check
    if not conf.ENABLE_THIRD_PARTY_AI:
        raise AppException(
            status_code=503,
            code="service_unavailable",
            message="image/voice checking needs third-party AI; paste the text instead",
        )

    # 2. Size limit validation
    max_bytes = conf.MAX_AUDIO_MB * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise PayloadTooLargeError(
            message=f"Audio size ({len(audio_bytes)} bytes) exceeds limit of {conf.MAX_AUDIO_MB}MB"
        )

    # 3. Magic byte sniffing
    detected_mime = sniff_audio_mime(audio_bytes)
    if not detected_mime:
        raise AppException(
            status_code=422,
            code="invalid_audio_format",
            message="Unsupported or invalid audio file. Allowed formats: WAV, MP3, OGG, WEBM, M4A.",
        )

    # 4. Check Sarvam API key
    if not conf.SARVAM_API_KEY:
        raise AppException(
            status_code=503,
            code="service_unavailable",
            message="image/voice checking needs third-party AI; paste the text instead",
        )

    # 5. Call Sarvam Speech-to-Text API
    sarvam_url = getattr(conf, "SARVAM_STT_URL", "https://api.sarvam.ai/speech-to-text")
    sarvam_model = getattr(conf, "SARVAM_STT_MODEL", "saaras:v2")
    lang_code = map_language_to_sarvam_code(lang_hint)

    headers = {
        "api-subscription-key": conf.SARVAM_API_KEY,
    }

    # Multipart file and data payload in memory
    extension = detected_mime.split("/")[-1]
    filename = f"audio.{extension}"
    files = {
        "file": (filename, audio_bytes, detected_mime),
    }
    data = {
        "model": sarvam_model,
        "language_code": lang_code,
    }

    timeout = httpx.Timeout(8.0)

    try:
        if http_client:
            response = await http_client.post(
                sarvam_url,
                headers=headers,
                files=files,
                data=data,
                timeout=timeout,
            )
        else:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    sarvam_url,
                    headers=headers,
                    files=files,
                    data=data,
                )

        if response.status_code >= 500:
            logger.warning("Sarvam STT returned status %d", response.status_code)
            raise AppException(
                status_code=502,
                code="stt_failed",
                message="Voice recognition service error. Please try again or paste the text.",
            )

        response.raise_for_status()
        res_data = response.json()
        transcript = res_data.get("transcript", "").strip()
        detected_language = res_data.get("language_code", lang_code)

    except httpx.TimeoutException as exc:
        logger.warning("Sarvam STT timed out after 8s")
        raise AppException(
            status_code=504,
            code="stt_timeout",
            message="Voice note processing timed out. Please paste the text directly.",
        ) from exc
    except AppException:
        raise
    except Exception as exc:
        logger.warning("Sarvam STT request failed: %s", exc)
        raise AppException(
            status_code=502,
            code="stt_failed",
            message="Could not transcribe audio. Please paste the text or record a clearer voice note.",
        ) from exc

    # 6. Minimum character length check (>= 10 chars)
    if len(transcript) < 10:
        raise AppException(
            status_code=422,
            code="not_enough_text",
            message=f"Not enough clear speech detected in voice note ({len(transcript)} characters). Please record again clearly or paste the text.",
        )

    return IngestResult(
        text=transcript,
        confidence_note="sarvam_stt",
        language=detected_language,
        source="stt",
    )
