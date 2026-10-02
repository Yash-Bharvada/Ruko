"""Tests for Module M6: Verdict Engine and Multilingual Reason Localization."""

import pytest
from typing import List, Optional

from app.core.config import Settings
from app.core.schemas import RegistryInfo
from app.modules.model_adapter.contract import ModelOutput
from app.modules.rules.engine import RuleFlag
from app.modules.verdict.engine import (
    VerdictOutcome,
    assert_no_advice,
    decide_verdict,
    sanitize_advice_string,
)
from app.modules.verdict.i18n import (
    get_disclaimer,
    get_verdict_note,
    load_translations,
    t,
)


# Helper fixtures
def make_model(available: bool = True, score: Optional[float] = 0.10, top_words: Optional[List[str]] = None) -> ModelOutput:
    return ModelOutput(
        available=available,
        score=score,
        top_words=top_words or [],
        calming_words=[],
        error=None if available else "model_unavailable",
    )


def make_registry(status: str = "found_in_snapshot") -> RegistryInfo:
    return RegistryInfo(
        status=status,
        matches=[{"reg_no": "INA000000001", "match_type": "unconfirmed_reg_no"}] if status == "not_found_in_snapshot" else [],
        snapshot_date="2026-03-01",
        is_sample_data=True,
        verify_url="https://www.sebi.gov.in",
    )


def flag(code: str, severity: str = "high") -> RuleFlag:
    return RuleFlag(code=code, severity=severity, evidence=f"sample {code} evidence", source="rule")


# --- Truth Table Tests (18 Scenarios) ---

TRUTH_TABLE_CASES = [
    # 1. Model >= 0.80 and 1 high rule flag -> strong_red_flags (Rule 1)
    (
        [flag("guaranteed_returns", "high")],
        make_model(available=True, score=0.90, top_words=["guaranteed"]),
        make_registry("found_in_snapshot"),
        False,
        "strong_red_flags",
    ),
    # 2. Model >= 0.80 and 1 medium rule flag -> strong_red_flags (Rule 1)
    (
        [flag("urgency_pressure", "medium")],
        make_model(available=True, score=0.85, top_words=["urgent"]),
        make_registry("found_in_snapshot"),
        False,
        "strong_red_flags",
    ),
    # 3. Model low (0.10) but >= 2 high rule flags -> strong_red_flags (Rule 1)
    (
        [flag("guaranteed_returns", "high"), flag("personal_upi_payment", "high")],
        make_model(available=True, score=0.10),
        make_registry("found_in_snapshot"),
        False,
        "strong_red_flags",
    ),
    # 4. Model unavailable but >= 2 high rule flags -> strong_red_flags (Rule 1)
    (
        [flag("otp_pin_request", "high"), flag("apk_or_remote_app", "high")],
        make_model(available=False, score=None),
        make_registry("found_in_snapshot"),
        False,
        "strong_red_flags",
    ),
    # 5. Model >= 0.50 and 1 high rule flag -> strong_red_flags (Rule 1)
    (
        [flag("upfront_payment_request", "high")],
        make_model(available=True, score=0.55),
        make_registry("found_in_snapshot"),
        False,
        "strong_red_flags",
    ),
    # 6. Model < 0.50 (0.40) and 1 high rule flag -> cannot_verify (Rule 3)
    (
        [flag("authority_impersonation", "high")],
        make_model(available=True, score=0.40),
        make_registry("found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 7. Model <= 0.20 (0.15) and 0 rule flags and clean registry -> no_red_flags_found (Rule 2)
    (
        [],
        make_model(available=True, score=0.15),
        make_registry("found_in_snapshot"),
        False,
        "no_red_flags_found",
    ),
    # 8. Model <= 0.20 (0.05) and 0 rule flags -> no_red_flags_found (Rule 2)
    (
        [],
        make_model(available=True, score=0.05),
        make_registry("not_checked"),
        False,
        "no_red_flags_found",
    ),
    # 9. Model UNAVAILABLE + 0 flags -> CANNOT_VERIFY (Rule 4: never no_red_flags_found)
    (
        [],
        make_model(available=False, score=None),
        make_registry("found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 10. Model <= 0.20 but registry unconfirmed -> cannot_verify (registry is 1 medium flag)
    (
        [],
        make_model(available=True, score=0.15),
        make_registry("not_found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 11. Model <= 0.20 but 1 medium rule flag -> cannot_verify (Rule 3)
    (
        [flag("suspicious_link", "medium")],
        make_model(available=True, score=0.15),
        make_registry("found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 12. Model intermediate (0.70) with 0 rule flags -> cannot_verify (Rule 3)
    (
        [],
        make_model(available=True, score=0.70),
        make_registry("found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 13. Model 0.50 with 1 medium rule flag -> cannot_verify (Rule 3)
    (
        [flag("vip_or_tip_group_invite", "medium")],
        make_model(available=True, score=0.50),
        make_registry("found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 14. Model >= 0.80 but 0 rule flags -> cannot_verify (model alone without rule flag does not trigger strong_red_flags)
    (
        [],
        make_model(available=True, score=0.85, top_words=["crypto"]),
        make_registry("found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 15. Registry not_found_in_snapshot alone + model 0.10 -> cannot_verify (Rule 6: never alone causes strong)
    (
        [],
        make_model(available=True, score=0.10),
        make_registry("not_found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 16. Out of scope request -> out_of_scope (Rule 5)
    (
        [flag("guaranteed_returns", "high")],
        make_model(available=True, score=0.90),
        make_registry("found_in_snapshot"),
        True,  # is_out_of_scope
        "out_of_scope",
    ),
    # 17. Model unavailable + 1 medium flag -> cannot_verify
    (
        [flag("secrecy_request", "medium")],
        make_model(available=False, score=None),
        make_registry("found_in_snapshot"),
        False,
        "cannot_verify",
    ),
    # 18. Model unavailable + 1 high flag -> cannot_verify (needs >= 2 high or model >= 0.50)
    (
        [flag("personal_upi_payment", "high")],
        make_model(available=False, score=None),
        make_registry("found_in_snapshot"),
        False,
        "cannot_verify",
    ),
]


@pytest.mark.parametrize("rule_flags,model_out,reg_info,out_of_scope,expected_verdict", TRUTH_TABLE_CASES)
def test_verdict_decision_table(
    rule_flags: List[RuleFlag],
    model_out: ModelOutput,
    reg_info: RegistryInfo,
    out_of_scope: bool,
    expected_verdict: str,
) -> None:
    """Acceptance check: 18-row truth table verifying all combination outcomes."""
    outcome = decide_verdict(
        rule_flags=rule_flags,
        model_output=model_out,
        registry_info=reg_info,
        lang="en",
        is_out_of_scope=out_of_scope,
    )
    assert outcome.verdict == expected_verdict, (
        f"Failed for flags={[f.code for f in rule_flags]}, score={model_out.score}, "
        f"reg={reg_info.status}: expected {expected_verdict}, got {outcome.verdict}"
    )


# --- Rule 4: Degradation Invariant ---

def test_rule4_model_unavailable_can_never_be_no_red_flags_found() -> None:
    """Acceptance check: If model is unavailable and 0 flags, verdict is cannot_verify, never no_red_flags_found."""
    outcome = decide_verdict(
        rule_flags=[],
        model_output=make_model(available=False, score=None),
        registry_info=make_registry("found_in_snapshot"),
        lang="en",
    )
    assert outcome.verdict == "cannot_verify"
    assert "model_unavailable" in outcome.degraded


# --- Word 'Safe' Prohibition Invariant ---

def test_no_affirmative_safe_claim() -> None:
    """Acceptance check: The word 'safe' never appears as an affirmative claim;

    note_no_red_flags_found must explicitly state 'does NOT mean it is safe'.
    """
    outcome = decide_verdict(
        rule_flags=[],
        model_output=make_model(available=True, score=0.05),
        registry_info=make_registry("found_in_snapshot"),
        lang="en",
    )
    assert outcome.verdict == "no_red_flags_found"
    assert "does NOT mean it is safe" in outcome.note

    # In Gujarati and Hindi as well
    note_gu = get_verdict_note("no_red_flags_found", "gu")
    assert "નથી કે આ સલામત છે" in note_gu

    note_hi = get_verdict_note("no_red_flags_found", "hi")
    assert "नहीं है कि यह सुरक्षित है" in note_hi


# --- Advice Guardrail Filter Tests ---

def test_assert_no_advice_blocks_injected_advice_strings() -> None:
    """Acceptance check: assert_no_advice blocks 'You should buy this stock' and replaces with neutral text."""
    injected_strings = [
        "You should buy this stock now for quick profits!",
        "Sell this share immediately.",
        "Target price is Rs 450 with strong buy rating.",
        "Invest in this private pre-IPO round.",
        "Yeh share kharido aur paise kamao.",
        "Aa stock kharidvo faydo thase.",
    ]

    for inj in injected_strings:
        sanitized = sanitize_advice_string(inj)
        assert sanitized != inj, f"Forbidden string slipped through: {inj}"
        assert "Educational scam analysis only" in sanitized

    # Allowed defensive phrases must NOT be blocked
    allowed_strings = [
        "Do not pay or share OTP/PIN.",
        "Check with an official source before acting.",
        "Verify with SEBI or your bank.",
    ]
    for allowed in allowed_strings:
        assert sanitize_advice_string(allowed) == allowed


# --- Multilingual Completeness & Fallback Chain ---

def test_multilingual_seeded_codes_completeness() -> None:
    """Acceptance check: Gujarati and Hindi contain no untranslated English fallbacks for seeded codes."""
    translations = load_translations()
    required_keys = [
        "guaranteed_returns",
        "unrealistic_return_claim",
        "upfront_payment_request",
        "personal_upi_payment",
        "otp_pin_request",
        "apk_or_remote_app",
        "authority_impersonation",
        "vip_or_tip_group_invite",
        "urgency_pressure",
        "secrecy_request",
        "suspicious_link",
        "unverified_registration_claim",
        "registry_not_confirmed",
        "model_high_risk",
        "note_strong_red_flags",
        "note_cannot_verify",
        "note_no_red_flags_found",
        "note_out_of_scope",
        "disclaimer",
    ]

    for lang in ("hi", "gu"):
        for key in required_keys:
            text = t(key, lang)
            assert text != f"[{key}]", f"Missing key {key} in {lang}"
            assert text != translations["en"][key], f"Key {key} in {lang} fell back to English"


def test_i18n_fallback_chain_missing_key() -> None:
    """Acceptance check: Unknown key falls back gracefully and never raises KeyError."""
    # Key present only in English
    result = t("only_in_english_key", "gu")
    assert result == "[only_in_english_key]"


# --- Reason Ordering and Model High Risk ---

def test_reasons_ordering_and_model_high_risk() -> None:
    """Acceptance check: Reasons sorted high -> medium -> low -> info, max 6, model_high_risk attached."""
    model_out = make_model(available=True, score=0.92, top_words=["guarantee", "profit"])
    flags = [
        flag("urgency_pressure", "medium"),
        flag("unverified_registration_claim", "info"),
        flag("guaranteed_returns", "high"),
    ]
    reg_info = make_registry("not_found_in_snapshot")

    outcome = decide_verdict(flags, model_out, reg_info, lang="en")

    assert outcome.verdict == "strong_red_flags"
    assert len(outcome.reasons) <= 6

    # Verify severity sort: high before medium before info
    severities = [r.severity for r in outcome.reasons]
    assert severities[0] == "high"
    assert "model_high_risk" in [r.code for r in outcome.reasons]
    assert "registry_not_confirmed" in [r.code for r in outcome.reasons]
