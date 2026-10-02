"""Screenshot and image OCR ingestion module."""

from typing import Literal, Optional, Tuple
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.errors import AppException, PayloadTooLargeError
from app.core.logging import logger
from app.modules.extractor.llm_client import LLMClient


class IngestResult(BaseModel):
    """Result of OCR or STT ingestion."""

    text: str = Field(..., description="Extracted transcribed text")
    confidence_note: Optional[str] = Field(None, description="Optional confidence indicator")
    language: Optional[str] = Field(None, description="Detected language code if available")
    source: Literal["ocr", "stt"] = Field(..., description="ocr | stt")


def sniff_image_mime(image_bytes: bytes) -> Optional[str]:
    """Sniff magic bytes to verify PNG, JPEG, or WEBP image format.

    Rejects files whose headers do not strictly match genuine image signatures,
    preventing executable, shell, or disguised payloads.
    """
    if len(image_bytes) < 12:
        return None

    # PNG: \x89PNG\r\n\x1a\n
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # JPEG: \xff\xd8\xff
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # WEBP: RIFF....WEBP
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"

    return None


async def image_to_text(
    image_bytes: bytes,
    mime_hint: Optional[str] = None,
    settings: Optional[Settings] = None,
    client: Optional[LLMClient] = None,
) -> IngestResult:
    """Extract text from screenshot or image bytes in-memory using vision LLM.

    Guarantees:
    - In-memory only: zero disk persistence.
    - Magic byte sniffing rejects disguised files.
    - Enforces MAX_IMAGE_MB with 413.
    - 503 if third-party AI is disabled.
    - 422 'not_enough_text' if extracted text < 10 chars.
    - Never logs image bytes or extracted content.
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
    max_bytes = conf.MAX_IMAGE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise PayloadTooLargeError(
            message=f"Image size ({len(image_bytes)} bytes) exceeds limit of {conf.MAX_IMAGE_MB}MB"
        )

    # 3. Magic byte sniffing
    detected_mime = sniff_image_mime(image_bytes)
    if not detected_mime:
        raise AppException(
            status_code=422,
            code="invalid_image_format",
            message="Unsupported or invalid image file. Allowed formats: PNG, JPEG, WEBP.",
        )

    # 4. LLM client check
    llm = client or LLMClient(settings=conf)
    if not llm.is_configured:
        raise AppException(
            status_code=503,
            code="service_unavailable",
            message="image/voice checking needs third-party AI; paste the text instead",
        )

    # 5. Execute Vision OCR in memory
    try:
        raw_text = await llm.generate_text_from_image(
            image_bytes=image_bytes,
            mime_type=detected_mime,
            prompt="Transcribe all visible text exactly, preserving Gujarati/Hindi/English; output only the text.",
        )
    except Exception as exc:
        logger.warning("Vision OCR failed: %s", exc)
        raise AppException(
            status_code=502,
            code="ocr_failed",
            message="Could not read text from the image. Please upload a clearer screenshot or paste the text.",
        ) from exc

    clean_text = raw_text.strip()

    # 6. Minimum character length check (>= 10 chars)
    if len(clean_text) < 10:
        raise AppException(
            status_code=422,
            code="not_enough_text",
            message=f"Not enough readable text found in image ({len(clean_text)} characters). Please upload a clearer screenshot or paste the text directly.",
        )

    return IngestResult(
        text=clean_text,
        confidence_note="vision_ocr",
        source="ocr",
    )
