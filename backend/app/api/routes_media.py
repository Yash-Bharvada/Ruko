"""Media ingestion API endpoints for screenshot OCR, audio STT, and video reel analysis."""

from typing import Optional
from fastapi import APIRouter, File, Form, Request, UploadFile

from app.api.routes_check import run_check
from app.core import config
from app.core.errors import AppException
from app.core.schemas import CheckResult
from app.modules.ingest.media import sniff_video_mime, video_to_text
from app.modules.ingest.ocr import image_to_text, sniff_image_mime
from app.modules.ingest.stt import audio_to_text, sniff_audio_mime

router = APIRouter(prefix="/v1", tags=["Media Ingest"])


@router.post("/check/image", response_model=CheckResult)
async def check_image(
    request: Request,
    file: UploadFile = File(..., description="Screenshot or photo of suspicious message"),
    language: Optional[str] = Form(None, description="Optional language hint (gu, hi, en)"),
    amount: Optional[float] = Form(None, description="Optional investment amount mentioned"),
) -> CheckResult:
    """Ingest an image/screenshot, extract text via vision OCR in-memory, and return full CheckResult."""
    request_id = getattr(request.state, "request_id", None)
    image_bytes = await file.read()
    result = await image_to_text(image_bytes, mime_hint=file.content_type)
    return await run_check(
        text=result.text,
        language_hint=language,
        amount=amount,
        request_id=request_id,
        source=result.source or "ocr",
        input_source="ocr",
    )


@router.post("/check/audio", response_model=CheckResult)
async def check_audio(
    request: Request,
    file: UploadFile = File(..., description="Audio voice-note file"),
    language: Optional[str] = Form(None, description="Optional language hint (hi, gu, en)"),
    amount: Optional[float] = Form(None, description="Optional investment amount mentioned"),
) -> CheckResult:
    """Ingest an audio voice note, transcribe text via Sarvam STT in-memory, and return full CheckResult."""
    request_id = getattr(request.state, "request_id", None)
    audio_bytes = await file.read()
    result = await audio_to_text(audio_bytes, mime_hint=file.content_type, lang_hint=language)
    return await run_check(
        text=result.text,
        language_hint=language,
        amount=amount,
        request_id=request_id,
        source=result.source or "stt",
        input_source="stt",
    )


@router.post("/check/media", response_model=CheckResult)
async def check_media(
    request: Request,
    file: UploadFile = File(..., description="Multipart file: text (.txt), image, audio, or video reel"),
    language: Optional[str] = Form(None, description="Optional language hint (gu, hi, en)"),
    amount: Optional[float] = Form(None, description="Optional investment amount mentioned"),
) -> CheckResult:
    """Unified multimodal ingestion endpoint: sniffs magic bytes and routes to text, OCR, STT, or video pipeline."""
    settings = config.get_settings()
    request_id = getattr(request.state, "request_id", None)
    data = await file.read()
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    # 1. Plain Text Routing (.txt or text/plain)
    if content_type.startswith("text/plain") or filename.endswith(".txt"):
        try:
            plain_text = data.decode("utf-8")
        except UnicodeDecodeError:
            plain_text = data.decode("latin-1", errors="replace")

        return await run_check(
            text=plain_text,
            language_hint=language,
            amount=amount,
            request_id=request_id,
            source="text",
            input_source="text",
        )

    # 2. Video Sniffing & Routing (checked before audio so WebM/MP4 videos aren't misrouted)
    video_mime = sniff_video_mime(data)
    if video_mime or content_type.startswith("video/") or any(filename.endswith(ext) for ext in (".mp4", ".mov", ".webm")):
        if not settings.ENABLE_THIRD_PARTY_AI:
            raise AppException(
                status_code=503,
                code="third_party_disabled",
                message="Video checking needs third-party AI for speech-to-text and vision OCR",
            )
        video_result = await video_to_text(data, mime_hint=video_mime or content_type, settings=settings)
        return await run_check(
            text=video_result.text,
            language_hint=language,
            amount=amount,
            request_id=request_id,
            source="video",
            input_source="video",
            speech_text=video_result.speech_text,
            on_screen_text=video_result.on_screen_text,
        )

    # 3. Image Sniffing & Routing
    image_mime = sniff_image_mime(data)
    if image_mime or content_type.startswith("image/") or any(filename.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")):
        if not settings.ENABLE_THIRD_PARTY_AI:
            raise AppException(
                status_code=503,
                code="third_party_disabled",
                message="Image checking needs third-party AI for vision OCR",
            )
        ocr_result = await image_to_text(data, mime_hint=image_mime or content_type, settings=settings)
        return await run_check(
            text=ocr_result.text,
            language_hint=language,
            amount=amount,
            request_id=request_id,
            source="ocr",
            input_source="ocr",
        )

    # 4. Audio Sniffing & Routing
    audio_mime = sniff_audio_mime(data)
    if audio_mime or content_type.startswith("audio/") or any(filename.endswith(ext) for ext in (".wav", ".mp3", ".ogg", ".m4a")):
        if not settings.ENABLE_THIRD_PARTY_AI:
            raise AppException(
                status_code=503,
                code="third_party_disabled",
                message="Voice checking needs third-party AI for speech-to-text",
            )
        stt_result = await audio_to_text(data, mime_hint=audio_mime or content_type, lang_hint=language, settings=settings)
        return await run_check(
            text=stt_result.text,
            language_hint=language,
            amount=amount,
            request_id=request_id,
            source="stt",
            input_source="stt",
        )

    # 5. Unsupported Media Type Fallback
    raise AppException(
        status_code=422,
        code="unsupported_media_type",
        message="Unsupported media format. Please upload text (.txt), image (PNG/JPEG/WEBP), audio (WAV/MP3/M4A/OGG), or video (MP4/MOV/WEBM).",
    )
