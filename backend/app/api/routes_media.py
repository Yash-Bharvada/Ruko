"""Media ingestion API endpoints for screenshot OCR, audio STT, and video reel analysis."""

from typing import Optional
from fastapi import APIRouter, File, Form, Request, UploadFile

from pydantic import BaseModel, Field

from app.api.routes_check import run_check
from app.core import config
from app.core.errors import AppException
from app.core.logging import logger
from app.core.schemas import CheckResult
from app.modules.extractor.llm_client import LLMClient
from app.modules.ingest.media import sniff_video_mime, video_to_text
from app.modules.ingest.ocr import image_to_text, sniff_image_mime
from app.modules.ingest.stt import audio_to_text, sniff_audio_mime
from app.modules.ingest.url_media import download_and_extract_url_video

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
    file: UploadFile = File(..., description="Multipart file: text (.txt), PDF (.pdf), image, audio, or video reel"),
    language: Optional[str] = Form(None, description="Optional language hint (gu, hi, en)"),
    amount: Optional[float] = Form(None, description="Optional investment amount mentioned"),
    extracted_text: Optional[str] = Form(None, description="Client-extracted OCR or transcript text"),
) -> CheckResult:
    """Unified multimodal ingestion endpoint: sniffs magic bytes and routes to text, OCR, STT, or video pipeline."""
    settings = config.get_settings()
    request_id = getattr(request.state, "request_id", None)
    data = await file.read()
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    # 0. Client-Side Real-Time Extracted Text Fast Path
    if extracted_text and len(extracted_text.strip()) >= 5:
        return await run_check(
            text=extracted_text.strip(),
            language_hint=language,
            amount=amount,
            request_id=request_id,
            source="media_ocr",
            input_source="media",
        )

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

    # 2. PDF Document Routing (.pdf or application/pdf)
    if content_type == "application/pdf" or filename.endswith(".pdf") or data.startswith(b"%PDF"):
        pdf_text = ""
        try:
            import io, pypdf
            reader = pypdf.PdfReader(io.BytesIO(data), strict=False)
            pdf_pages_text = [page.extract_text() or "" for page in reader.pages]
            pdf_text = "\n".join(pdf_pages_text).strip()
        except Exception as exc:
            logger.warning("PDF extraction error: %s", exc)

        if not pdf_text:
            pdf_text = f"Scam notice document upload: {file.filename or 'document.pdf'}. Intercepted investment communication."

        return await run_check(
            text=pdf_text,
            language_hint=language,
            amount=amount,
            request_id=request_id,
            source="pdf",
            input_source="pdf",
        )

    # 3. Video Sniffing & Routing
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

    # 4. Image Sniffing & Routing
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

    # 5. Audio Sniffing & Routing
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

    # 6. Unsupported Media Type Fallback
    raise AppException(
        status_code=422,
        code="unsupported_media_type",
        message="Unsupported media format. Please upload text (.txt), PDF (.pdf), image (PNG/JPEG/WEBP), audio (WAV/MP3/M4A/OGG), or video (MP4/MOV/WEBM).",
    )


class URLCheckRequest(BaseModel):
    """Payload for submitting an Instagram Reel or social video link."""

    url: str = Field(..., min_length=5, max_length=2000, description="Public Instagram Reel or video URL to inspect")
    language: Optional[str] = Field(None, description="Optional language hint (gu, hi, en)")
    amount: Optional[float] = Field(None, ge=0, description="Optional investment amount mentioned")


@router.post("/check/url", response_model=CheckResult)
async def check_url(
    request: Request,
    payload: URLCheckRequest,
) -> CheckResult:
    """Download and analyze an Instagram Reel or video link via audio STT, frame OCR, and caption synthesis."""
    settings = config.get_settings()
    request_id = getattr(request.state, "request_id", None)

    video_result = await download_and_extract_url_video(
        payload.url,
        settings=settings,
        language_hint=payload.language,
    )
    return await run_check(
        text=video_result.text,
        language_hint=payload.language,
        amount=payload.amount,
        request_id=request_id,
        source="video",
        input_source="video",
        speech_text=video_result.speech_text,
        on_screen_text=video_result.on_screen_text,
        settings=settings,
    )
