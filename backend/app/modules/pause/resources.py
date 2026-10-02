"""Recovery checklist and emergency resources loader for victims who already paid."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.logging import logger
from app.modules.verdict.engine import assert_no_advice
from app.modules.verdict.i18n import normalize_lang_code

_resources_data: Optional[Dict[str, Any]] = None


def _resolve_resources_path() -> Path:
    candidates = [
        Path.cwd() / "data" / "resources.json",
        Path.cwd() / "backend" / "data" / "resources.json",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "resources.json",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()

    raise FileNotFoundError("Could not locate data/resources.json")


def load_resources(force_reload: bool = False) -> Dict[str, Any]:
    """Load resources.json file into memory."""
    global _resources_data
    if _resources_data is not None and not force_reload:
        return _resources_data

    path = _resolve_resources_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            _resources_data = json.load(f)
            return _resources_data
    except Exception as exc:
        logger.error("Failed to load recovery resources from %s: %s", path, exc)
        return {}


def get_already_paid_resources(lang: Optional[str] = "en") -> Dict[str, Any]:
    """Retrieve localized 'I already paid' recovery checklist.

    HONESTY & SAFETY GUARANTEES:
    - Zero advice or promotion of any private recovery service.
    - Official government helplines and regulators only (1930, cybercrime.gov.in, SEBI SCORES).
    - Scanned with assert_no_advice.
    """
    data = load_resources()
    target_lang = normalize_lang_code(lang)

    # 1. Try target language
    res = data.get(target_lang)
    if not res:
        # Fallback to English
        logger.warning("Recovery resources for lang '%s' not found, falling back to English", target_lang)
        res = data.get("en", {})

    output = {
        "language": target_lang if target_lang in data else "en",
        "title": res.get("title", "Recovery Steps"),
        "note": res.get("note", ""),
        "checklist": res.get("checklist", []),
    }

    # Ensure no advice phrases leaked into resource text
    return assert_no_advice(output)
