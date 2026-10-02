"""Text-to-speech synthesis module with Sarvam AI and browser speech fallback."""

import asyncio
import hashlib
import time
from collections import OrderedDict
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.modules.verdict.i18n import get_verdict_note, normalize_lang_code, t

# In-memory LRU cache for synthesized templated audio: {(lang, sha256): AudioResult}
_MAX_CACHE_SIZE = 256
_tts_cache: OrderedDict[Tuple[str, str], "AudioResult"] = OrderedDict()


class SpeakRequest(BaseModel):
    """Request to synthesize spoken explanation.

    SECURITY MANDATE:
    Accepts ONLY structured reason codes and verdict. Free-text inputs are strictly
    forbidden to ensure the backend only speaks validated, safe templated phrases.
    """

    verdict: Literal["strong_red_flags", "cannot_verify", "no_red_flags_found", "out_of_scope"] = Field(
        ...,
        description="Verdict code for spoken summary note",
    )
    reason_codes: List[str] = Field(
        default_factory=list,
        description="List of reason codes to read aloud (max 3 spoken)",
    )
    language: Optional[str] = Field(
        "en",
        description="Target language (gu, hi, en)",
    )

    model_config = ConfigDict(extra="forbid")


class AudioResult(BaseModel):
    """Synthesized audio output from Sarvam AI."""

    audio_base64: str = Field(..., description="Base64 encoded audio bytes")
    mime: str = Field("audio/wav", description="Audio MIME type")
    source: Literal["sarvam"] = Field("sarvam")


class BrowserSpeechFallback(BaseModel):
    """Fallback payload for client-side device Web Speech API."""

    source: Literal["browser_speech"] = Field("browser_speech")
    text: str = Field(..., description="Safe templated script to speak via browser voice")
    lang_code: str = Field(..., description="BCP-47 language tag (e.g. hi-IN, gu-IN, en-IN)")


def map_language_to_bcp47(lang: Optional[str]) -> str:
    """Map language key to BCP-47 language code for browser speech and Sarvam."""
    norm = normalize_lang_code(lang)
    if norm == "hi":
        return "hi-IN"
    if norm == "gu":
        return "gu-IN"
    return "en-IN"


def build_spoken_script(
    verdict: str,
    reason_codes: List[str],
    lang: str = "en",
    max_chars: int = 500,
) -> str:
    """Assemble a safe, templated spoken script from i18n phrases.

    Order:
    1. Verdict note sentence.
    2. Up to 3 reason explanation sentences.

    Guarantees:
    - Never trims mid-sentence; drops complete trailing reason sentences if over max_chars.
    - Script length is strictly <= max_chars.
    """
    target_lang = normalize_lang_code(lang)
    note_text = get_verdict_note(verdict, target_lang)

    sentences: List[str] = [note_text]

    for code in reason_codes[:3]:
        reason_text = t(code, target_lang)
        if reason_text and reason_text != f"[{code}]":
            sentences.append(reason_text)

    # Trim by dropping whole sentences from the end if exceeding max_chars
    while len(" ".join(sentences)) > max_chars and len(sentences) > 1:
        sentences.pop()

    script = " ".join(sentences)
    # Edge case: if single note itself is longer than max_chars, truncate cleanly at word boundary
    if len(script) > max_chars:
        script = script[:max_chars].rsplit(" ", 1)[0] + "."

    return script


async def synthesize_speech(
    text: str,
    lang: str = "en",
    settings: Optional[Settings] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> Union[AudioResult, BrowserSpeechFallback]:
    """Synthesize speech via Sarvam AI, with in-memory caching and browser fallback.

    Guarantees:
    - In-memory LRU cache prevents duplicate API calls for identical templated phrases.
    - Safe fallback to BrowserSpeechFallback on any error, timeout, or missing credentials.
    - Strict 6-second timeout.
    - Never logs spoken text or base64 audio data.
    """
    conf = settings or get_settings()
    target_lang = normalize_lang_code(lang)
    lang_code = map_language_to_bcp47(target_lang)

    fallback = BrowserSpeechFallback(
        source="browser_speech",
        text=text,
        lang_code=lang_code,
    )

    # 1. Feature flag & API key checks
    if not conf.ENABLE_THIRD_PARTY_AI or not conf.SARVAM_API_KEY:
        logger.info("Sarvam TTS disabled or unconfigured; using browser speech fallback")
        return fallback

    # 2. Check LRU Cache
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cache_key = (target_lang, text_hash)

    if cache_key in _tts_cache:
        # Move to end (most recently used)
        _tts_cache.move_to_end(cache_key)
        logger.info("TTS cache hit for language=%s", target_lang)
        return _tts_cache[cache_key]

    # 3. Call Sarvam Text-to-Speech API
    sarvam_url = getattr(conf, "SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")
    sarvam_model = getattr(conf, "SARVAM_TTS_MODEL", "bulbul:v1")
    sarvam_speaker = getattr(conf, "SARVAM_TTS_SPEAKER", "meera")

    headers = {
        "api-subscription-key": conf.SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": [text],
        "target_language_code": lang_code,
        "speaker": sarvam_speaker,
        "pitch": 0,
        "pace": 1.0,
        "loudness": 1.5,
        "speech_sample_rate": 8000,
        "enable_preprocessing": True,
        "model": sarvam_model,
    }

    timeout = httpx.Timeout(6.0)
    start_time = time.perf_counter()

    try:
        if http_client:
            response = await http_client.post(
                sarvam_url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
        else:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    sarvam_url,
                    headers=headers,
                    json=payload,
                )

        if response.status_code != 200:
            logger.warning("Sarvam TTS returned status %d; falling back to browser speech", response.status_code)
            return fallback

        res_data = response.json()
        audios = res_data.get("audios", [])
        if not audios or not audios[0]:
            logger.warning("Sarvam TTS returned empty audios array; falling back to browser speech")
            return fallback

        result = AudioResult(
            audio_base64=audios[0],
            mime="audio/wav",
            source="sarvam",
        )

        # Store in LRU cache
        if len(_tts_cache) >= _MAX_CACHE_SIZE:
            _tts_cache.popitem(last=False)  # Evict oldest
        _tts_cache[cache_key] = result

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info("Sarvam TTS synthesized audio in %.2f ms (lang=%s)", latency_ms, target_lang)
        return result

    except (httpx.TimeoutException, asyncio.TimeoutError):
        logger.warning("Sarvam TTS timed out after 6.0s; falling back to browser speech")
        return fallback
    except Exception as exc:
        logger.warning("Sarvam TTS failed (%s); falling back to browser speech", exc)
        return fallback
