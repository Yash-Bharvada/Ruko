"""Deterministic red-flag evaluation engine and claim extraction."""

import re
import unicodedata
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.modules.rules.loader import CompiledRule, load_rules


class RuleFlag(BaseModel):
    """Detected red flag with localized evidence from the original message."""

    code: str = Field(..., description="Unique rule code")
    severity: str = Field(..., description="high | medium | low | info")
    evidence: str = Field(..., description="Exact quoted substring from input text")
    source: str = Field("rule", description="Source of flag")


class RuleEngine:
    """Evaluates text against compiled red-flag rules deterministically."""

    def __init__(self, rules: Optional[List[CompiledRule]] = None) -> None:
        self.rules = rules or load_rules()

    def _is_negated(self, text: str, rule: CompiledRule) -> bool:
        """Check if the rule's claim is explicitly negated in the text."""
        # 1. Check compiled negation regexes
        for neg_re in rule.compiled_negation_regexes:
            if neg_re.search(text):
                return True

        # 2. Check negation phrases
        text_lower = text.lower()
        for neg_phrase in rule.all_negations:
            if neg_phrase.lower() in text_lower:
                return True

        return False

    def evaluate(self, text: Optional[str]) -> List[RuleFlag]:
        """Evaluate message text against red-flag rules.

        Guarantees:
        - Never raises on any input (None, empty, emojis, fuzzed strings).
        - Evidence is ALWAYS an exact substring of the original text (<= 80 chars).
        - Deduplicated by code (first match preserved).
        """
        if not text or not isinstance(text, str):
            return []

        # Normalize unicode NFC for consistent matching while preserving original string for evidence
        norm_text = unicodedata.normalize("NFC", text)
        flags: List[RuleFlag] = []
        seen_codes = set()

        for rule in self.rules:
            if rule.code in seen_codes:
                continue

            # Check negations first
            if rule.all_negations and self._is_negated(norm_text, rule):
                continue

            matched_span: Optional[tuple[int, int]] = None

            # 1. Match compiled regex patterns
            for regex in rule.compiled_regexes:
                m = regex.search(norm_text)
                if m:
                    matched_span = m.span()
                    break

            # 2. Match individual phrases if regex did not hit
            if not matched_span and rule.all_phrases:
                for phrase in rule.all_phrases:
                    # Case-insensitive substring match
                    idx = norm_text.lower().find(phrase.lower())
                    if idx != -1:
                        matched_span = (idx, idx + len(phrase))
                        break

            if matched_span:
                start, end = matched_span
                # Extract evidence directly from the original string
                raw_evidence = text[start:end].strip()
                if not raw_evidence:
                    raw_evidence = text[start:min(len(text), start + 80)].strip()

                # Ensure max 80 characters without breaking substring property
                trimmed_evidence = raw_evidence[:80]

                flags.append(
                    RuleFlag(
                        code=rule.code,
                        severity=rule.severity,
                        evidence=trimmed_evidence,
                        source="rule",
                    )
                )
                seen_codes.add(rule.code)

        return flags


# Global cached engine instance
_engine: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    """Get or initialize singleton RuleEngine."""
    global _engine
    if _engine is None:
        _engine = RuleEngine()
    return _engine


def evaluate_rules(text: Optional[str]) -> List[RuleFlag]:
    """Convenience helper to evaluate text with singleton engine."""
    return get_rule_engine().evaluate(text)


def extract_basic_claims(text: Optional[str]) -> Dict[str, Any]:
    """Extract structured facts (registration numbers, UPI IDs, phones, URLs, percentages) via regex.

    Used when LLM extraction is disabled or unavailable.
    """
    if not text or not isinstance(text, str):
        return {
            "registration_numbers": [],
            "upi_ids": [],
            "phones": [],
            "urls": [],
            "percentages": [],
        }

    # 1. Registration Numbers (SEBI formats)
    reg_no_pattern = re.compile(r"\b(?:INA|INH|INZ|INP|INF|INR|INM)\d{6,12}\b", re.IGNORECASE)
    reg_matches = [m.group(0).upper() for m in reg_no_pattern.finditer(text)]

    # 2. UPI IDs
    upi_pattern = re.compile(
        r"\b[a-zA-Z0-9.\-_]{2,49}@(oksbi|okhdfcbank|okicici|okaxis|ybl|paytm|upi|apl|ibl|axl|postbank|ptsbi|ptaxis|pthdfc|fam|airtel|fbl|idfcbank|[a-zA-Z]{3,})\b",
        re.IGNORECASE,
    )
    upi_matches = [m.group(0).lower() for m in upi_pattern.finditer(text)]

    # 3. Indian Phone Numbers
    phone_pattern = re.compile(r"(?:\+?91[\-\s]?)?[6-9]\d{9}\b")
    phone_matches = [m.group(0).strip() for m in phone_pattern.finditer(text)]

    # 4. URLs
    url_pattern = re.compile(r"https?://[^\s]+", re.IGNORECASE)
    url_matches = [m.group(0) for m in url_pattern.finditer(text)]

    # 5. Percentages
    pct_pattern = re.compile(r"\b(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
    pct_matches = [float(m.group(1)) for m in pct_pattern.finditer(text)]

    # Deduplicate while preserving order
    return {
        "registration_numbers": list(dict.fromkeys(reg_matches)),
        "upi_ids": list(dict.fromkeys(upi_matches)),
        "phones": list(dict.fromkeys(phone_matches)),
        "urls": list(dict.fromkeys(url_matches)),
        "percentages": list(dict.fromkeys(pct_matches)),
    }
