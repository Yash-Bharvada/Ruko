"""Verdict engine and multilingual reason localization module."""

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

__all__ = [
    "VerdictOutcome",
    "decide_verdict",
    "assert_no_advice",
    "sanitize_advice_string",
    "t",
    "get_disclaimer",
    "get_verdict_note",
    "load_translations",
]
