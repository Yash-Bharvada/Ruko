"""API endpoints for Document Explanation and Verified Audio Synthesis."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.config import get_settings
from app.core.errors import AppException
from app.core.schemas import DocExplanation, ExplainSpeakRequest
from app.modules.docexplain import explain_document
from app.modules.docexplain.advice_filter import (
    contains_advice_or_safety_claim,
    sanitize_text_field,
)
from app.modules.docexplain.signing import verify_speak_token
from app.modules.guardrails.advice_filter import is_advice_request
from app.modules.voice.tts import synthesize_speech

router = APIRouter(prefix="/v1", tags=["Document Explanation"])


@router.post("/explain", response_model=DocExplanation)
async def explain_document_endpoint(
    request: Request,
    file: Optional[UploadFile] = File(None, description="PDF, DOCX, or Image document to explain"),
    text: Optional[str] = Form(None, description="Pasted document text to explain"),
    language: str = Form("en", description="Target language: en | hi | gu | hinglish | gujlish"),
    include_storyboard: bool = Form(True, description="Whether to include browser video storyboard"),
    crosscheck: bool = Form(True, description="Whether to crosscheck red flags against Ruko rules"),
) -> DocExplanation:
    """Upload a complex document or paste text to receive a grounded plain-language explanation."""
    settings = get_settings()

    if not getattr(settings, "EXPLAIN_ENABLED", True):
        raise AppException(
            status_code=503,
            code="feature_disabled",
            message="The Document Explanation feature is currently disabled.",
        )

    # Validate that exactly one of file or text is supplied
    has_file = file is not None and bool(file.filename)
    has_text = text is not None and bool(text.strip())

    if (has_file and has_text) or (not has_file and not has_text):
        raise AppException(
            status_code=422,
            code="invalid_input",
            message="Please provide exactly one of 'file' or 'text'.",
        )

    file_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None

    if has_file and file is not None:
        file_bytes = await file.read()
        filename = file.filename
        content_type = file.content_type

    request_id = getattr(request.state, "request_id", None)

    return await explain_document(
        data=file_bytes,
        filename=filename,
        content_type=content_type,
        plain_text=text,
        language=language,
        include_storyboard=include_storyboard,
        crosscheck=crosscheck,
        request_id=request_id,
        settings=settings,
    )


@router.post("/explain/speak")
async def explain_speak_endpoint(
    req: ExplainSpeakRequest,
    request: Request,
) -> Dict[str, Any]:
    """Synthesize audio for a verified storyboard scene narration with tamper-proof HMAC check."""
    settings = get_settings()

    if not getattr(settings, "EXPLAIN_ENABLED", True):
        raise AppException(
            status_code=503,
            code="feature_disabled",
            message="The Document Explanation feature is currently disabled.",
        )

    # 1. Enforce length constraint
    if len(req.narration.strip()) > 300:
        raise AppException(
            status_code=422,
            code="narration_too_long",
            message="Narration exceeds maximum allowed length of 300 characters.",
        )

    # 2. Verify tamper-proof HMAC token and TTL
    is_valid_token = verify_speak_token(
        request_id=req.request_id,
        scene_id=req.scene_id,
        language=req.language,
        issued_at=req.issued_at,
        narration=req.narration,
        speak_token=req.speak_token,
        settings=settings,
    )

    if not is_valid_token:
        raise AppException(
            status_code=403,
            code="invalid_speak_token",
            message="The provided speak token is invalid, expired, or the narration was tampered with.",
        )

    # 3. Output-side guardrail check on narration
    if contains_advice_or_safety_claim(req.narration) or is_advice_request(req.narration):
        raise AppException(
            status_code=422,
            code="advice_prohibited",
            message="Narration contains prohibited advisory statements.",
        )

    clean_narration, _ = sanitize_text_field(req.narration, source_text=req.narration)

    # 4. Map voice language (hinglish -> hi, gujlish -> gu)
    voice_lang = req.language.lower().strip()
    if voice_lang == "hinglish":
        voice_lang = "hi"
    elif voice_lang == "gujlish":
        voice_lang = "gu"
    elif voice_lang not in ("en", "hi", "gu"):
        voice_lang = "en"

    # 5. Synthesize speech via Sarvam / Browser fallback
    result = await synthesize_speech(
        text=clean_narration,
        lang=voice_lang,
        settings=settings,
    )

    return result.model_dump()
