"""Core analysis orchestrator and check endpoints."""

import asyncio
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Request

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.core.schemas import CheckRequest, CheckResult, ModelInfo, RegistryInfo
from app.modules.extractor.claims import (
    Claims,
    PaymentRequest,
    _build_regex_fallback_claims,
    detect_script_language,
    extract_basic_claims,
    extract_claims,
)
from app.modules.guardrails.advice_filter import is_advice_request
from app.modules.model_adapter.contract import ModelOutput
from app.modules.model_adapter.loader import load_model
from app.modules.registry.service import get_registry_service
from app.modules.rules.engine import RuleFlag, get_rule_engine
from app.modules.verdict.engine import assert_no_advice, decide_verdict, sanitize_advice_string
from app.modules.verdict.i18n import get_disclaimer, get_verdict_note, t

router = APIRouter(prefix="/v1", tags=["Analysis"])

INSTAGRAM_LINK_PATTERN = re.compile(
    r"(?i)https?://(?:www\.)?(?:instagram\.com|instagr\.am)/[^\s]+"
)


def detect_instagram_link_hint(text: str, lang: str) -> Optional[str]:
    """If submitted text contains an instagram.com link and under ~30 other characters, return localized hint.

    Ruko never scrapes or downloads from Instagram or any other URL.
    """
    if not text:
        return None
    matches = INSTAGRAM_LINK_PATTERN.findall(text)
    if not matches:
        return None
    # Check non-Instagram text length
    residual = INSTAGRAM_LINK_PATTERN.sub("", text).strip()
    if len(residual) < 30:
        return t("hint_instagram_link", lang)
    return None


async def run_check(
    text: str,
    language_hint: Optional[str] = None,
    amount: Optional[float] = None,
    request_id: Optional[str] = None,
    source: Optional[str] = None,
    input_source: Optional[str] = None,
    speech_text: Optional[str] = None,
    on_screen_text: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> CheckResult:
    """Orchestrate the full multi-module analysis pipeline concurrently.

    Pipeline phases:
    1. Language detection (via Unicode script blocks with hint precedence).
    2. Safety guardrail check: intercept stock tips / investment advice requests -> out_of_scope.
    3. Instagram link guardrail: return user hint if message is predominantly an Instagram link.
    4. Concurrent execution: Rules Engine, ML Model Scorer, Claims Extractor (bounded by 8.0s timeout).
    5. Optional amount merging into claims.
    6. Registry verification against dated local SEBI snapshot.
    7. Deterministic verdict decision table execution (M6 + TRANSCRIBED_NEVER_CLEAR).
    8. Strict anti-advice sweep (blocking forbidden stock tips).
    9. Zero-retention privacy audit logging (metadata only; NO text or bodies logged).
    """
    conf = settings or get_settings()
    req_id = request_id or str(uuid.uuid4())
    cleaned_text = (text or "").strip()
    resolved_source = input_source or source or "text"

    # Phase 1: Script/Language detection
    detected_lang = detect_script_language(cleaned_text, language_hint)

    # Phase 2: Advice request guardrail
    if is_advice_request(cleaned_text):
        logger.info(
            "Verdict generated: request_id=%s, verdict=out_of_scope, lang=%s, score=0.0, degraded=[]",
            req_id,
            detected_lang,
        )
        return CheckResult(
            request_id=req_id,
            language=detected_lang,
            verdict="out_of_scope",
            score=0.0,
            reasons=[],
            registry=RegistryInfo(
                status="not_checked",
                matches=[],
                snapshot_date="2026-03-01",
                is_sample_data=True,
                verify_url=conf.SEBI_VERIFY_URL,
            ),
            model=ModelInfo(available=True, score=0.0, top_words=[], calming_words=[]),
            claims={},
            note=sanitize_advice_string(get_verdict_note("out_of_scope", detected_lang)),
            degraded=[],
            disclaimer=sanitize_advice_string(get_disclaimer(detected_lang)),
            text=cleaned_text if source else None,
            source=resolved_source,
            input_source=resolved_source,
            speech_text=speech_text,
            on_screen_text=on_screen_text,
            hint=None,
        )

    # Phase 3: Instagram link guardrail
    instagram_hint = detect_instagram_link_hint(cleaned_text, detected_lang)

    # Phase 4: Concurrent execution of Rules, Model, and Claims Extractor
    rule_engine = get_rule_engine()
    scorer, model_degraded = load_model(conf)

    async def _evaluate_rules() -> Tuple[List[RuleFlag], List[str]]:
        try:
            flags = rule_engine.evaluate(cleaned_text)
            return flags, []
        except Exception as exc:
            logger.warning("Rules evaluation encountered an issue: %s", exc)
            return [], ["rules_degraded"]

    async def _evaluate_model() -> Tuple[ModelOutput, List[str]]:
        if not scorer.is_available:
            return ModelOutput(available=False, score=None, top_words=[], calming_words=[]), ["model_unavailable"]
        try:
            output = await scorer.score(cleaned_text)
            deg = [] if output.available else ["model_unavailable"]
            return output, deg
        except Exception as exc:
            logger.warning("Model inference encountered an issue: %s", exc)
            return ModelOutput(available=False, score=None, top_words=[], calming_words=[]), ["model_unavailable"]

    async def _evaluate_extractor() -> Tuple[Claims, List[str]]:
        try:
            return await extract_claims(cleaned_text, lang_hint=detected_lang, settings=conf)
        except Exception as exc:
            logger.warning("Extractor encountered an issue: %s", exc)
            regex_facts = extract_basic_claims(cleaned_text)
            return _build_regex_fallback_claims(regex_facts, detected_lang), ["llm_unavailable"]

    try:
        (rule_flags, rules_deg), (model_output, model_deg), (claims, extr_deg) = await asyncio.wait_for(
            asyncio.gather(_evaluate_rules(), _evaluate_model(), _evaluate_extractor()),
            timeout=7.5,
        )
    except asyncio.TimeoutError:
        logger.warning("Analysis pipeline timeout exceeded (>7.5s)")
        rule_flags, rules_deg = rule_engine.evaluate(cleaned_text), []
        model_output, model_deg = (
            ModelOutput(available=False, score=None, top_words=[], calming_words=[]),
            ["model_unavailable", "pipeline_timeout"],
        )
        regex_facts = extract_basic_claims(cleaned_text)
        claims, extr_deg = _build_regex_fallback_claims(regex_facts, detected_lang), ["llm_unavailable"]

    # Phase 5: Amount injection into claims if provided
    if amount is not None and amount > 0:
        already_has_amount = any(
            p.amount is not None and abs(p.amount - amount) < 0.01 for p in claims.payment_requests
        )
        if not already_has_amount:
            claims.payment_requests.append(PaymentRequest(amount=amount, method="other", target=None))

    claims_dict = claims.model_dump()

    # Phase 6: Registry verification against snapshot
    registry_service = get_registry_service()
    registry_info, reg_deg = registry_service.check(claims_dict)

    # Phase 7: Deterministic verdict engine evaluation with TRANSCRIBED_NEVER_CLEAR
    verdict_outcome = decide_verdict(
        rule_flags=rule_flags,
        model_output=model_output,
        registry_info=registry_info,
        lang=detected_lang,
        settings=conf,
        input_source=resolved_source,
    )

    # Phase 8: Anti-advice sweep & reason sanitization
    verdict_outcome = assert_no_advice(verdict_outcome)

    all_degraded = list(
        dict.fromkeys(rules_deg + model_deg + extr_deg + reg_deg + verdict_outcome.degraded)
    )

    # Phase 9: Zero-retention privacy audit logging (NO text/bodies logged!)
    logger.info(
        "Verdict generated: request_id=%s, verdict=%s, lang=%s, score=%.2f, degraded=%s",
        req_id,
        verdict_outcome.verdict,
        detected_lang,
        verdict_outcome.score,
        all_degraded,
    )

    model_info = ModelInfo(
        available=model_output.available,
        score=model_output.score,
        top_words=model_output.top_words,
        calming_words=model_output.calming_words,
    )

    return CheckResult(
        request_id=req_id,
        language=detected_lang,
        verdict=verdict_outcome.verdict,
        score=verdict_outcome.score,
        reasons=verdict_outcome.reasons,
        registry=registry_info,
        model=model_info,
        claims=claims_dict,
        note=verdict_outcome.note,
        degraded=all_degraded,
        disclaimer=verdict_outcome.disclaimer,
        text=cleaned_text if source else None,
        source=resolved_source,
        input_source=resolved_source,
        speech_text=speech_text,
        on_screen_text=on_screen_text,
        hint=instagram_hint,
    )


@router.post("/check", response_model=CheckResult)
async def check_text(req: CheckRequest, request: Request) -> CheckResult:
    """Analyze suspicious investment message text and return an explainable verdict."""
    request_id = getattr(request.state, "request_id", None)
    return await run_check(
        text=req.text,
        language_hint=req.language,
        amount=req.amount,
        request_id=request_id,
        source="text",
        input_source="text",
    )
