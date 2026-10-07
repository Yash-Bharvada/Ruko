"""Crosscheck integration evaluating document text against Ruko red-flag rules and SEBI snapshot."""

from typing import Any, Dict, List, Optional, Tuple

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.core.schemas import Reason, RegistryInfo
from app.modules.registry.service import get_registry_service
from app.modules.rules.engine import evaluate_rules, extract_basic_claims
from app.modules.verdict.i18n import t


async def run_crosscheck(
    text: str,
    language: str = "en",
    settings: Optional[Settings] = None,
) -> Tuple[List[Reason], Optional[RegistryInfo], List[str]]:
    """Evaluate document text against Ruko's red-flag rule patterns and SEBI registry snapshot.

    MANDATE:
    - Never computes or assigns a scam verdict.
    - Surfaces factual rule flags (e.g. guaranteed returns, personal UPI) with localized explanations.
    - Provides dated SEBI snapshot lookup if registration numbers or entity names are claimed.

    Returns:
        (ruko_flags, registry_info, degraded_flags)
    """
    conf = settings or get_settings()
    degraded: List[str] = []
    ruko_reasons: List[Reason] = []
    target_lang = "en" if language in ("hinglish", "gujlish") else language

    # 1. Run deterministic rule evaluation
    try:
        rule_flags = evaluate_rules(text)
        for flag in rule_flags:
            ruko_reasons.append(
                Reason(
                    code=flag.code,
                    severity=flag.severity,  # type: ignore[arg-type]
                    text=t(flag.code, target_lang),
                    evidence=flag.evidence,
                    source="rule",
                )
            )
    except Exception as exc:
        logger.warning("DocExplain crosscheck rule evaluation issue: %s", exc)
        degraded.append("crosscheck_unavailable")

    # 2. Extract registration facts for SEBI verification
    registry_info: Optional[RegistryInfo] = None
    try:
        basic_facts = extract_basic_claims(text)
        reg_nos = basic_facts.get("registration_numbers", [])

        if reg_nos:
            reg_service = get_registry_service()
            registry_info, reg_flags, reg_deg = reg_service.verify_claims(
                claimed_reg_nos=reg_nos,
                claimed_names=[],
            )
            degraded.extend(reg_deg)

            for flag in reg_flags:
                ruko_reasons.append(
                    Reason(
                        code=flag.code,
                        severity=flag.severity,  # type: ignore[arg-type]
                        text=t(flag.code, target_lang),
                        evidence=flag.evidence,
                        source="registry",
                    )
                )
    except Exception as exc:
        logger.warning("DocExplain crosscheck registry verification issue: %s", exc)
        degraded.append("crosscheck_unavailable")

    return ruko_reasons, registry_info, list(dict.fromkeys(degraded))
