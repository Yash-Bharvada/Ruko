"""Deterministic verdict engine and safety advice filter."""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.core.schemas import ModelInfo, Reason, RegistryInfo
from app.modules.model_adapter.contract import ModelOutput
from app.modules.rules.engine import RuleFlag
from app.modules.verdict.i18n import get_disclaimer, get_verdict_note, t

# Severity sort priority
SEVERITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
    "info": 3,
}

# Forbidden investment advice patterns (English, Hindi, Gujarati, Roman)
FORBIDDEN_ADVICE_PATTERNS = [
    re.compile(r"(?i)\b(?:you\s*should\s*)?(?:buy|sell|hold)\s*(?:this|these)?\s*(?:stock|share|crypto|fund|token|script)\b"),
    re.compile(r"(?i)\b(?:invest\s*in|put\s*money\s*in)\s+(?:this|these|the)\b"),
    re.compile(r"(?i)\b(?:target\s*price|stop\s*loss|price\s*target)\b"),
    re.compile(r"(?i)\b(?:strong\s*buy|strong\s*sell|accumulate)\b"),
    # Hindi / Roman Hindi
    re.compile(r"(?i)\b(?:share|stock|paisa)\s*(?:kharido|kharid\s*lo|becho|bech\s*do|lagao)\b"),
    re.compile(r"(?i)\b(?:kharido|becho)\b"),
    re.compile(r"खरीदें|बेचें|निवेश\s*करें"),
    # Gujarati / Roman Gujarati
    re.compile(r"(?i)\b(?:share|stock)\s*(?:kharido|kharidvo|vecho|vechvo)\b"),
    re.compile(r"ખરીદો|વેચો|રોકાણ\s*કરો"),
]

NEUTRAL_FALLBACK_TEXT = "Educational scam analysis only. Ruko does not provide financial or investment advice."


def sanitize_advice_string(text: str) -> str:
    """Check text for forbidden investment advice. If found, replace with neutral text and log error."""
    if not text or not isinstance(text, str):
        return text

    for pattern in FORBIDDEN_ADVICE_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.error("CRITICAL: Forbidden investment advice detected: '%s'", match.group(0))
            return NEUTRAL_FALLBACK_TEXT

    return text


def assert_no_advice(obj: Any) -> Any:
    """Recursively scan data structures for forbidden investment advice strings."""
    if isinstance(obj, str):
        return sanitize_advice_string(obj)
    elif isinstance(obj, dict):
        return {k: assert_no_advice(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [assert_no_advice(item) for item in obj]
    elif hasattr(obj, "text") and hasattr(obj, "evidence"):
        # Pydantic Reason model
        obj.text = sanitize_advice_string(obj.text)
        obj.evidence = sanitize_advice_string(obj.evidence)
        return obj
    return obj


class VerdictOutcome:
    """Structured decision output from the verdict engine."""

    def __init__(
        self,
        verdict: str,
        score: float,
        reasons: List[Reason],
        note: str,
        disclaimer: str,
        degraded: List[str],
    ) -> None:
        self.verdict = verdict
        self.score = score
        self.reasons = reasons
        self.note = note
        self.disclaimer = disclaimer
        self.degraded = degraded


def decide_verdict(
    rule_flags: List[RuleFlag],
    model_output: ModelOutput,
    registry_info: RegistryInfo,
    lang: str = "en",
    settings: Optional[Settings] = None,
    is_out_of_scope: bool = False,
) -> VerdictOutcome:
    """Combine rules, model predictions, and registry verification into a final explainable verdict.

    DETERMINISTIC VERDICT RULES (Strictly Enforced):
    1. 'out_of_scope' if user is asking for stock advice (handled via guardrail flag).
    2. 'strong_red_flags' if:
       - model score >= HIGH_BAND (0.80) and at least 1 rule flag, OR
       - >= 2 high-severity rule flags, OR
       - 1 high-severity flag + model score >= 0.50.
    3. 'no_red_flags_found' ONLY IF:
       - model is available AND score <= LOW_BAND (0.20) AND zero rule flags.
       - Never say 'safe'.
    4. Everything else -> 'cannot_verify'.
    5. If model is unavailable (degraded):
       - verdict can NEVER be 'no_red_flags_found'; best is 'cannot_verify'.
    6. 'not_found_in_snapshot' counts as ONE medium flag ('registry_not_confirmed');
       it never alone causes 'strong_red_flags'.
    """
    conf = settings or get_settings()
    high_band = getattr(conf, "HIGH_BAND", 0.80)
    low_band = getattr(conf, "LOW_BAND", 0.20)

    degraded_flags: List[str] = []
    if not model_output.available:
        degraded_flags.append("model_unavailable")

    # 1. Check Out of Scope (Advice requests)
    if is_out_of_scope:
        note = get_verdict_note("out_of_scope", lang)
        disclaimer = get_disclaimer(lang)
        return VerdictOutcome(
            verdict="out_of_scope",
            score=0.0,
            reasons=[],
            note=sanitize_advice_string(note),
            disclaimer=sanitize_advice_string(disclaimer),
            degraded=degraded_flags,
        )

    # 2. Build Reason list and categorize severity counts
    reasons: List[Reason] = []
    seen_codes = set()

    high_rule_count = 0
    medium_rule_count = 0

    # Add rule flags
    for flag in rule_flags:
        if flag.code in seen_codes:
            continue
        if flag.severity == "high":
            high_rule_count += 1
        elif flag.severity == "medium":
            medium_rule_count += 1

        localized_text = t(flag.code, lang)
        reasons.append(
            Reason(
                code=flag.code,
                severity=flag.severity,
                text=sanitize_advice_string(localized_text),
                evidence=sanitize_advice_string(flag.evidence),
                source="rule",
            )
        )
        seen_codes.add(flag.code)

    # Add registry unconfirmed reason if applicable
    if registry_info.status == "not_found_in_snapshot":
        medium_rule_count += 1
        # Extract unconfirmed reg_no evidence if present in matches
        reg_evidence = "SEBI registration claimed but not confirmed in snapshot"
        for m in registry_info.matches:
            if m.get("match_type") == "unconfirmed_reg_no" and m.get("reg_no"):
                reg_evidence = f"Claimed SEBI Reg: {m['reg_no']}"
                break

        if "registry_not_confirmed" not in seen_codes:
            reasons.append(
                Reason(
                    code="registry_not_confirmed",
                    severity="medium",
                    text=sanitize_advice_string(t("registry_not_confirmed", lang)),
                    evidence=sanitize_advice_string(reg_evidence),
                    source="registry",
                )
            )
            seen_codes.add("registry_not_confirmed")

    # Add model_high_risk reason if model score >= HIGH_BAND
    model_score = model_output.score if model_output.available else None
    if model_output.available and model_score is not None and model_score >= high_band:
        evidence_words = ", ".join(model_output.top_words[:3]) if model_output.top_words else "Statistical scam risk"
        if "model_high_risk" not in seen_codes:
            reasons.append(
                Reason(
                    code="model_high_risk",
                    severity="high",
                    text=sanitize_advice_string(t("model_high_risk", lang)),
                    evidence=sanitize_advice_string(evidence_words),
                    source="model",
                )
            )
            seen_codes.add("model_high_risk")

    total_rule_flags = len(rule_flags)
    total_effective_flags = total_rule_flags + (1 if registry_info.status == "not_found_in_snapshot" else 0)

    # 3. Apply Decision Table
    verdict: str
    composite_score: float

    # Rule 1: strong_red_flags
    # - model score >= 0.80 and at least 1 rule flag, OR
    # - >= 2 high-severity rule flags, OR
    # - 1 high-severity flag + model score >= 0.50
    has_high_model = (model_score is not None) and (model_score >= high_band)
    has_medium_model = (model_score is not None) and (model_score >= 0.50)

    is_strong = (
        (has_high_model and total_rule_flags >= 1)
        or (high_rule_count >= 2)
        or (high_rule_count >= 1 and has_medium_model)
    )

    if is_strong:
        verdict = "strong_red_flags"
        if model_score is not None:
            composite_score = max(model_score, 0.85)
        else:
            composite_score = 0.85 + (0.05 * min(high_rule_count, 3))
    # Rule 2: no_red_flags_found
    # - model is available AND score <= 0.20 AND zero rule flags (AND registry not unconfirmed)
    elif (
        model_output.available
        and model_score is not None
        and model_score <= low_band
        and total_effective_flags == 0
    ):
        verdict = "no_red_flags_found"
        composite_score = min(model_score, 0.15)
    # Rule 3 & 4: cannot_verify
    # (Including whenever model is unavailable and no strong red flags)
    else:
        verdict = "cannot_verify"
        if model_score is not None:
            composite_score = model_score
        else:
            # Estimate reasonable uncertainty score
            if high_rule_count == 1:
                composite_score = 0.60
            elif medium_rule_count >= 1:
                composite_score = 0.50
            else:
                composite_score = 0.35

    composite_score = round(min(max(composite_score, 0.0), 1.0), 2)

    # 4. Sort and cap reasons: high -> medium -> low -> info, max 6
    reasons.sort(key=lambda r: SEVERITY_ORDER.get(r.severity, 99))
    reasons = reasons[:6]

    # 5. Localized note and disclaimer
    note = get_verdict_note(verdict, lang)
    disclaimer = get_disclaimer(lang)

    # Final safety sweep for advice
    note = sanitize_advice_string(note)
    disclaimer = sanitize_advice_string(disclaimer)

    return VerdictOutcome(
        verdict=verdict,
        score=composite_score,
        reasons=reasons,
        note=note,
        disclaimer=disclaimer,
        degraded=degraded_flags,
    )
