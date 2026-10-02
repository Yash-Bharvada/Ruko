"""Matcher for entity names and registration numbers using RapidFuzz."""

import re
from typing import Set
from rapidfuzz import fuzz

from app.modules.registry.validators import normalize_reg_no


GENERIC_WORDS: Set[str] = {
    "ltd",
    "limited",
    "pvt",
    "private",
    "advisory",
    "research",
    "services",
    "financial",
    "securities",
    "capital",
    "associates",
    "consultants",
    "india",
    "demo",
    "llp",
    "corp",
    "corporation",
}


def clean_entity_tokens(name: str) -> str:
    """Normalize entity name for fuzzy matching by removing punctuation and generic corporate words."""
    if not name or not isinstance(name, str):
        return ""

    # Replace punctuation with spaces and lowercase
    cleaned = re.sub(r"[^\w\s]", " ", name.lower())
    tokens = [w for w in cleaned.split() if w and w not in GENERIC_WORDS]
    return " ".join(tokens)


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate fuzzy similarity between two entity names using token_set_ratio (0.0 to 100.0)."""
    t1 = clean_entity_tokens(name1)
    t2 = clean_entity_tokens(name2)

    if not t1 or not t2:
        return 0.0

    return float(fuzz.token_set_ratio(t1, t2))
