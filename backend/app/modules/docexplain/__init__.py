"""DocExplain module orchestrator for grounded plain-language document explanations."""

import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Tuple

from app.core.config import Settings, get_settings
from app.core.logging import log_request, logger
from app.core.schemas import (
    Diagrams,
    DocExplanation,
    GlossaryItem,
    KeyPoint,
    Reason,
    RegistryInfo,
    Scene,
    Step,
)
from app.modules.docexplain.advice_filter import (
    contains_advice_or_safety_claim,
    filter_explanation_output,
)
from app.modules.docexplain.crosscheck import run_crosscheck
from app.modules.docexplain.extract import extract_document_text
from app.modules.docexplain.graphs import validate_diagrams
from app.modules.docexplain.grounding import validate_grounding
from app.modules.docexplain.storyboard import build_storyboard
from app.modules.docexplain.understand import understand_document
from app.modules.extractor.llm_client import LLMClient
from app.modules.verdict.i18n import get_disclaimer, t


async def explain_document(
    data: Optional[bytes] = None,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    plain_text: Optional[str] = None,
    language: str = "en",
    include_storyboard: bool = True,
    crosscheck: bool = True,
    request_id: Optional[str] = None,
    settings: Optional[Settings] = None,
    client: Optional[LLMClient] = None,
) -> DocExplanation:
    """Execute end-to-end document explanation pipeline in-memory.

    Pipeline Steps:
    1. Extract: In-memory MIME sniffing and text extraction (PDF/DOCX/OCR/text).
    2. Understand: Prompt-injection shielded LLM structured extraction (or heuristic fallback).
    3. Grounding: Verbatim source evidence verification; drop ungrounded claims.
    4. Graphs: JSON diagram validation, label trimming, orphan removal, cycle detection.
    5. Storyboard: 4-8 visual scenes with HMAC-signed TTS audio tokens.
    6. Crosscheck: Ruko red-flag rules and SEBI snapshot verification (no verdict).
    7. Output Advice Filter: Strip action directives, safety promises, and unquoted URLs/phones.
    8. Assemble & Audit Log: Return DocExplanation and record zero-PII audit metadata.
    """
    conf = settings or get_settings()
    req_id = request_id or str(uuid.uuid4())
    start_time = time.perf_counter()
    degraded: List[str] = []
    confidence_notes: List[str] = []

    # Target language normalization
    req_lang = (language or "en").lower().strip()
    if req_lang not in ("en", "hi", "gu", "hinglish", "gujlish"):
        req_lang = "en"
    i18n_lang = "en" if req_lang in ("hinglish", "gujlish") else req_lang

    # -------------------------------------------------------------------------
    # Step 1: Extraction & Ingestion
    # -------------------------------------------------------------------------
    input_source = "text"
    if data:
        if filename and filename.lower().endswith(".pdf"):
            input_source = "pdf"
        elif filename and filename.lower().endswith(".docx"):
            input_source = "docx"
        elif content_type and "image" in content_type.lower():
            input_source = "ocr"
        elif filename and any(filename.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")):
            input_source = "ocr"
        else:
            input_source = "pdf" if data.startswith(b"%PDF") else "document"

    extracted_text, doc_type_guess, ocr_quality, extract_deg = await extract_document_text(
        data=data,
        filename=filename,
        content_type=content_type,
        plain_text=plain_text,
        settings=conf,
        client=client,
    )
    degraded.extend(extract_deg)

    if "truncated" in extract_deg:
        confidence_notes.append(
            f"The document was truncated to {conf.EXPLAIN_MAX_CHARS} characters to meet processing limits."
        )

    # -------------------------------------------------------------------------
    # Step 2: Understanding (LLM Extraction with Shielding)
    # -------------------------------------------------------------------------
    raw_understanding: Dict[str, Any] = {}
    try:
        raw_understanding, und_deg = await understand_document(
            text=extracted_text,
            language=req_lang,
            settings=conf,
            client=client,
        )
        degraded.extend(und_deg)
    except Exception as exc:
        logger.warning("DocExplain understanding failed: %s", exc)
        degraded.append("llm_unavailable")

    # -------------------------------------------------------------------------
    # Step 3: Grounding Validation (Evidence verification against source text)
    # -------------------------------------------------------------------------
    grounded_data, ground_notes, dropped_count = validate_grounding(
        understanding_data=raw_understanding,
        source_text=extracted_text,
        language=i18n_lang,
    )
    confidence_notes.extend(ground_notes)

    # -------------------------------------------------------------------------
    # Step 4: Diagram Graphs Validation & Repair
    # -------------------------------------------------------------------------
    validated_diagrams, graph_deg = validate_diagrams(grounded_data.get("diagrams"))
    degraded.extend(graph_deg)

    # Convert dictionary items to Pydantic models
    glossary_items: List[GlossaryItem] = []
    for g in grounded_data.get("glossary", []):
        try:
            glossary_items.append(GlossaryItem(**g))
        except Exception:
            continue

    key_point_items: List[KeyPoint] = []
    for kp in grounded_data.get("key_points", []):
        try:
            key_point_items.append(KeyPoint(**kp))
        except Exception:
            continue

    step_items: List[Step] = []
    for st in grounded_data.get("steps", []):
        try:
            step_items.append(Step(**st))
        except Exception:
            continue

    summary_text = grounded_data.get("summary", "")

    # -------------------------------------------------------------------------
    # Step 5: Storyboard Assembly & HMAC Signing
    # -------------------------------------------------------------------------
    storyboard_scenes: List[Scene] = []
    if include_storyboard:
        try:
            storyboard_scenes = build_storyboard(
                request_id=req_id,
                summary=summary_text,
                glossary=glossary_items,
                key_points=key_point_items,
                steps=step_items,
                diagrams=validated_diagrams,
                language=req_lang,
                source_text=extracted_text,
                settings=conf,
            )
        except Exception as exc:
            logger.warning("Storyboard construction issue: %s", exc)
            degraded.append("storyboard_unavailable")

    # -------------------------------------------------------------------------
    # Step 6: Crosscheck with Ruko Rules & Registry Snapshot
    # -------------------------------------------------------------------------
    ruko_flags: List[Reason] = []
    registry_info: Optional[RegistryInfo] = None
    if crosscheck:
        try:
            ruko_flags, registry_info, cross_deg = await run_crosscheck(
                text=extracted_text,
                language=req_lang,
                settings=conf,
            )
            degraded.extend(cross_deg)
            if ruko_flags:
                confidence_notes.append(
                    "The document contains patterns Ruko's checker flags; run it through Check for a full analysis."
                )
        except Exception as exc:
            logger.warning("DocExplain crosscheck issue: %s", exc)
            degraded.append("crosscheck_unavailable")

    # -------------------------------------------------------------------------
    # Step 7: Output Advice Filtering & URL Stripping
    # -------------------------------------------------------------------------
    explanation_dict = {
        "summary": summary_text,
        "glossary": [g.model_dump() for g in glossary_items],
        "key_points": [kp.model_dump() for kp in key_point_items],
        "steps": [s.model_dump() for s in step_items],
    }

    filtered_dict, was_advice_filtered = filter_explanation_output(explanation_dict, extracted_text)
    if was_advice_filtered:
        degraded.append("advice_filtered")
        confidence_notes.append(
            "Certain advice-oriented statements were neutralized to maintain strictly objective reporting."
        )

    # Re-instantiate filtered models
    summary_text = filtered_dict["summary"]
    glossary_items = [GlossaryItem(**g) for g in filtered_dict["glossary"]]
    key_point_items = [KeyPoint(**kp) for kp in filtered_dict["key_points"]]
    step_items = [Step(**s) for s in filtered_dict["steps"]]

    # -------------------------------------------------------------------------
    # Step 8: Assembly & Structured Audit Logging (Zero PII!)
    # -------------------------------------------------------------------------
    disclaimer = get_disclaimer(i18n_lang)
    final_degraded = list(dict.fromkeys(degraded))

    latency_ms = (time.perf_counter() - start_time) * 1000.0
    log_request(
        request_id=req_id,
        endpoint="/v1/explain",
        verdict="explained",
        language=req_lang,
        latency_ms=latency_ms,
        degraded=final_degraded,
    )

    return DocExplanation(
        request_id=req_id,
        language=req_lang,
        input_source=input_source,
        doc_type_guess=doc_type_guess,
        summary=summary_text,
        glossary=glossary_items,
        key_points=key_point_items,
        steps=step_items,
        diagrams=validated_diagrams,
        storyboard=storyboard_scenes,
        ruko_flags=ruko_flags,
        registry=registry_info,
        ocr_quality=ocr_quality,  # type: ignore[arg-type]
        confidence_notes=confidence_notes,
        disclaimer=disclaimer,
        degraded=final_degraded,
    )
