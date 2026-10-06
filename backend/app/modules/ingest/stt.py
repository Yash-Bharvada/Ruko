"""Voice-note and audio STT ingestion module using Sarvam AI with local speech recognition fallback."""

import asyncio
import io
import shutil
import subprocess
from typing import Any, Dict, Optional
import httpx
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.errors import AppException, PayloadTooLargeError
from app.core.logging import logger
from app.modules.ingest.ocr import IngestResult


def _find_ffmpeg() -> Optional[str]:
    """Locate ffmpeg binary in PATH."""
    return shutil.which("ffmpeg")


def _convert_audio_to_wav_sync(audio_bytes: bytes) -> Optional[bytes]:
    """Convert audio bytes to 16kHz mono WAV in-memory via ffmpeg pipe."""
    ffmpeg_bin = _find_ffmpeg()
    if not ffmpeg_bin:
        return None
    try:
        proc = subprocess.Popen(
            [ffmpeg_bin, "-y", "-i", "pipe:0", "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate(input=audio_bytes, timeout=10)
        if proc.returncode == 0 and len(stdout) > 100:
            return stdout
    except Exception as exc:
        logger.debug("In-memory audio conversion failed: %s", exc)
    return None


def _speech_recognize_wav_sync(wav_bytes: bytes, lang_hint: Optional[str]) -> Optional[str]:
    """Transcribe 16kHz mono WAV bytes in-memory using SpeechRecognition."""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        lang_code = "en-IN"
        if lang_hint:
            norm = lang_hint.lower().strip()
            if norm in ("hi", "hi-in", "hindi"):
                lang_code = "hi-IN"
            elif norm in ("gu", "gu-in", "gujarati"):
                lang_code = "gu-IN"
            elif norm in ("en", "en-in", "english"):
                lang_code = "en-IN"

        with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language=lang_code)
            return text.strip() if text else None
    except Exception as exc:
        logger.debug("Speech recognition fallback returned: %s", exc)
        return None


def sniff_audio_mime(audio_bytes: bytes) -> Optional[str]:
    """Sniff magic bytes to verify WAV, MP3, OGG, WEBM, M4A, or AAC audio format.

    Rejects files whose headers do not strictly match genuine audio signatures.
    """
    if len(audio_bytes) < 12:
        return None

    # Explicit rejection for executable / PE magic bytes
    if audio_bytes[:2] == b"MZ":
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

    # M4A / AAC in MP4 container: bytes 4-8 == b"ftyp"
    if len(audio_bytes) >= 12 and audio_bytes[4:8] == b"ftyp":
        brand = audio_bytes[8:12].lower()
        if any(b in brand for b in (b"m4a", b"m4b", b"alac", b"isom", b"mp42", b"mp41")):
            return "audio/m4a"

    # Raw ADTS AAC
    if audio_bytes[:2] in (b"\xff\xf1", b"\xff\xf9"):
        return "audio/aac"

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
    """Convert audio voice note into text in-memory using Sarvam STT or local fallback.

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

    transcript = ""
    lang_code = map_language_to_sarvam_code(lang_hint)
    detected_language = lang_code
    confidence_source = "sarvam_stt"

    # 4. Attempt Sarvam Speech-to-Text API if configured
    if conf.SARVAM_API_KEY:
        sarvam_url = getattr(conf, "SARVAM_STT_URL", "https://api.sarvam.ai/speech-to-text")
        sarvam_model = getattr(conf, "SARVAM_STT_MODEL", "saaras:v2")

        headers = {
            "api-subscription-key": conf.SARVAM_API_KEY,
        }
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

            if response.status_code < 400:
                res_data = response.json()
                transcript = res_data.get("transcript", "").strip()
                detected_language = res_data.get("language_code", lang_code)
                confidence_source = "sarvam_stt"
            elif response.status_code >= 500:
                logger.warning("Sarvam STT returned status %d", response.status_code)
        except httpx.TimeoutException as exc:
            logger.warning("Sarvam STT timed out after 8s")
        except Exception as exc:
            logger.warning("Sarvam STT request failed: %s", exc)

    # 5. In-Memory Fallback STT via ffmpeg + SpeechRecognition
    if not transcript:
        try:
            wav_data = await asyncio.to_thread(_convert_audio_to_wav_sync, audio_bytes)
            if wav_data:
                fallback_text = await asyncio.to_thread(_speech_recognize_wav_sync, wav_data, lang_hint)
                if fallback_text:
                    transcript = fallback_text.strip()
                    confidence_source = "stt_fallback"
        except Exception as exc:
            logger.debug("Local STT fallback failed: %s", exc)

    # 6. If no transcription succeeded
    if not transcript:
        if not conf.SARVAM_API_KEY:
            raise AppException(
                status_code=503,
                code="service_unavailable",
                message="image/voice checking needs third-party AI; paste the text instead",
            )
        raise AppException(
            status_code=502,
            code="stt_failed",
            message="Could not transcribe audio. Please paste the text or record a clearer voice note.",
        )

    # 7. Minimum character length check (>= 10 chars)
    if len(transcript) < 10:
        raise AppException(
            status_code=422,
            code="not_enough_text",
            message=f"Not enough clear speech detected in voice note ({len(transcript)} characters). Please record again clearly or paste the text.",
        )

    return IngestResult(
        text=transcript,
        confidence_note=confidence_source,
        language=detected_language,
        source="stt",
    )
