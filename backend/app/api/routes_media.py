"""Media ingestion API endpoints for screenshot OCR and audio STT."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, File, Form, UploadFile

from app.modules.ingest.ocr import image_to_text
from app.modules.ingest.stt import audio_to_text

router = APIRouter(prefix="/v1", tags=["Media Ingest"])


@router.post("/check/image")
async def check_image(
    file: UploadFile = File(..., description="Screenshot or photo of suspicious message"),
) -> Dict[str, Any]:
    """Ingest an image/screenshot, extract text via vision OCR in-memory, and return extracted text.

    (In M9, this orchestrates the full CheckResult pipeline).
    """
    image_bytes = await file.read()
    result = await image_to_text(image_bytes, mime_hint=file.content_type)
    return {
        "text": result.text,
        "source": result.source,
    }


@router.post("/check/audio")
async def check_audio(
    file: UploadFile = File(..., description="Audio voice-note file"),
    language: Optional[str] = Form(None, description="Optional language hint (hi, gu, en)"),
) -> Dict[str, Any]:
    """Ingest an audio voice note, transcribe text via Sarvam STT in-memory, and return extracted text.

    (In M9, this orchestrates the full CheckResult pipeline).
    """
    audio_bytes = await file.read()
    result = await audio_to_text(audio_bytes, mime_hint=file.content_type, lang_hint=language)
    return {
        "text": result.text,
        "source": result.source,
    }
