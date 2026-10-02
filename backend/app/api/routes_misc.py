"""Miscellaneous endpoints: registry lookup, privacy disclosures, and resources."""

from typing import Any, Dict
from fastapi import APIRouter, Query
from app.core.config import get_settings
from app.modules.registry.service import get_registry_service
from app.modules.voice.tts import SpeakRequest, build_spoken_script, synthesize_speech

router = APIRouter(prefix="/v1", tags=["Registry & Info"])


@router.get("/registry/lookup")
async def registry_lookup(
    q: str = Query(..., min_length=1, max_length=200, description="Registration number or entity name to look up"),
) -> Dict[str, Any]:
    """Offline dated SEBI intermediary snapshot lookup.

    HONEST DISCLOSURE:
    - Queries a dated, local offline snapshot, not live SEBI systems.
    - If not found, status is 'not_found_in_snapshot' ('could not confirm in our snapshot'), never 'fake'.
    """
    service = get_registry_service()
    return service.lookup(q)


@router.post("/speak")
async def speak_verdict(req: SpeakRequest) -> Dict[str, Any]:
    """Read verdict aloud in the user's language.

    SECURITY & INTEGRITY:
    - Speaks ONLY safe templated sentences from verified i18n files.
    - Rejects any free-text fields with HTTP 422.
    - Falls back to browser Web Speech API payload on any provider failure or timeout.
    """
    settings = get_settings()
    script = build_spoken_script(
        verdict=req.verdict,
        reason_codes=req.reason_codes,
        lang=req.language or "en",
        max_chars=getattr(settings, "MAX_TTS_CHARS", 500),
    )
    result = await synthesize_speech(
        text=script,
        lang=req.language or "en",
        settings=settings,
    )
    return result.model_dump()

