"""Internationalization (i18n) loader and translator for localized reasons and notes."""

import json
from pathlib import Path
from typing import Dict, Optional

from app.core.logging import logger

# In-memory cached translations: {lang: {code: text}}
_translations: Optional[Dict[str, Dict[str, str]]] = None


def _resolve_i18n_dir() -> Path:
    """Resolve directory holding en.json, hi.json, and gu.json."""
    candidates = [
        Path.cwd() / "data" / "i18n",
        Path.cwd() / "backend" / "data" / "i18n",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "i18n",
    ]
    for c in candidates:
        if c.is_dir() and (c / "en.json").is_file():
            return c.resolve()

    raise FileNotFoundError("Could not locate data/i18n directory with en.json")


def load_translations(force_reload: bool = False) -> Dict[str, Dict[str, str]]:
    """Load translation dictionaries for en, hi, and gu."""
    global _translations
    if _translations is not None and not force_reload:
        return _translations

    i18n_dir = _resolve_i18n_dir()
    translations: Dict[str, Dict[str, str]] = {}

    for lang in ("en", "hi", "gu"):
        path = i18n_dir / f"{lang}.json"
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    translations[lang] = json.load(f)
            except Exception as exc:
                logger.error("Failed to load i18n file for %s at %s: %s", lang, path, exc)
                translations[lang] = {}
        else:
            logger.warning("i18n file not found for %s at %s", lang, path)
            translations[lang] = {}

    _translations = translations
    return _translations


def normalize_lang_code(lang: Optional[str]) -> str:
    """Normalize language code to en, hi, or gu."""
    if not lang or not isinstance(lang, str):
        return "en"
    clean = lang.lower().replace("-", "_").split("_")[0].strip()
    if clean in ("hi", "hindi"):
        return "hi"
    if clean in ("gu", "gujarati"):
        return "gu"
    return "en"


def t(code: str, lang: Optional[str] = "en") -> str:
    """Translate reason code or verdict note with fallback chain lang -> en.

    Guarantees:
    - Never raises KeyError on missing code or language.
    - Falls back gracefully to English with a warning log.
    - If missing in all languages, logs an error and returns '[code]'.
    """
    translations = load_translations()
    target_lang = normalize_lang_code(lang)

    # 1. Try target language
    lang_dict = translations.get(target_lang, {})
    if code in lang_dict:
        return lang_dict[code]

    # 2. Fallback to English
    if target_lang != "en":
        logger.warning("Missing translation for key '%s' in language '%s', falling back to English", code, target_lang)

    en_dict = translations.get("en", {})
    if code in en_dict:
        return en_dict[code]

    # 3. Missing in English as well
    logger.error("Missing translation key '%s' in all languages", code)
    return f"[{code}]"


def get_disclaimer(lang: Optional[str] = "en") -> str:
    """Retrieve localized educational disclaimer."""
    return t("disclaimer", lang)


def get_verdict_note(verdict: str, lang: Optional[str] = "en") -> str:
    """Retrieve localized honest verdict note."""
    return t(f"note_{verdict}", lang)
