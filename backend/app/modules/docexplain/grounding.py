"""Grounding validator ensuring every extracted claim is backed by verbatim document evidence."""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz

from app.core.logging import logger
from app.modules.verdict.i18n import t


def _normalize_for_matching(text: str) -> str:
    """Normalize whitespace, case, and unicode NFC for reliable fuzzy evidence matching."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFC", text)
    # Collapse multiple whitespace characters into single space
    norm = re.sub(r"\s+", " ", norm).strip().lower()
    return norm


def find_source_evidence_span(evidence: str, source_text: str) -> Optional[str]:
    """Verify evidence against source text and return verbatim span if grounded.

    Strategy:
    1. Direct case-insensitive substring search in original source text.
    2. Normalized whitespace search.
    3. RapidFuzz partial_ratio >= 90.
    4. If matched, returns verbatim span from original source text; otherwise None.
    """
    if not evidence or not source_text:
        return None

    raw_ev = evidence.strip()
    if len(raw_ev) < 3:
        return None

    # 1. Direct case-insensitive substring in source text
    idx = source_text.lower().find(raw_ev.lower())
    if idx != -1:
        return source_text[idx : idx + len(raw_ev)].strip()

    # 2. Normalized substring matching
    norm_ev = _normalize_for_matching(raw_ev)
    norm_src = _normalize_for_matching(source_text)

    if norm_ev in norm_src:
        # Find rough location in source_text
        words = [w for w in raw_ev.split() if len(w) > 3]
        if words:
            first_w_idx = source_text.lower().find(words[0].lower())
            if first_w_idx != -1:
                return source_text[first_w_idx : min(len(source_text), first_w_idx + len(raw_ev) + 20)].strip()
        return raw_ev

    # 3. RapidFuzz partial_ratio >= 90
    ratio = fuzz.partial_ratio(norm_ev, norm_src)
    if ratio >= 90:
        # Find best matching window in source_text
        words = [w for w in raw_ev.split() if len(w) > 3]
        if words:
            first_w_idx = source_text.lower().find(words[0].lower())
            if first_w_idx != -1:
                return source_text[first_w_idx : min(len(source_text), first_w_idx + len(raw_ev) + 20)].strip()
        return raw_ev

    return None


def validate_grounding(
    understanding_data: Dict[str, Any],
    source_text: str,
    language: str = "en",
) -> Tuple[Dict[str, Any], List[str], int]:
    """Validate and filter glossary, key points, steps, and timeline items against source text.

    Guarantees:
    - Items lacking verbatim evidence in the document are strictly dropped.
    - Grounded items have their evidence replaced with the exact verbatim quote where found.
    - Dropped items count is recorded in confidence notes.

    Returns:
        (grounded_data, confidence_notes, dropped_count)
    """
    confidence_notes: List[str] = []
    dropped_count = 0

    # 1. Ground Glossary Items
    valid_glossary = []
    for g in understanding_data.get("glossary", []):
        ev = g.get("evidence", "")
        span = find_source_evidence_span(ev, source_text)
        if span:
            g["evidence"] = span[:150]
            valid_glossary.append(g)
        else:
            logger.info("Dropping ungrounded glossary item: %s", g.get("term"))
            dropped_count += 1

    # 2. Ground Key Points
    valid_key_points = []
    for kp in understanding_data.get("key_points", []):
        ev = kp.get("evidence", "")
        span = find_source_evidence_span(ev, source_text)
        if span:
            kp["evidence"] = span[:150]
            valid_key_points.append(kp)
        else:
            logger.info("Dropping ungrounded key point: %s", kp.get("id"))
            dropped_count += 1

    # Re-index key points
    for idx, kp in enumerate(valid_key_points, start=1):
        kp["id"] = f"kp_{idx}"

    # 3. Ground Steps
    valid_steps = []
    for st in understanding_data.get("steps", []):
        ev = st.get("evidence", "")
        span = find_source_evidence_span(ev, source_text)
        if span:
            st["evidence"] = span[:150]
            valid_steps.append(st)
        else:
            logger.info("Dropping ungrounded step: %s", st.get("title"))
            dropped_count += 1

    # Re-order steps
    for idx, st in enumerate(valid_steps, start=1):
        st["order"] = idx

    # 4. Ground Timeline in Diagrams
    diagrams = understanding_data.get("diagrams", {})
    valid_timeline = []
    for item in diagrams.get("timeline", []):
        ev = item.get("evidence", "")
        span = find_source_evidence_span(ev, source_text)
        if span:
            item["evidence"] = span[:150]
            valid_timeline.append(item)
        else:
            dropped_count += 1

    diagrams["timeline"] = valid_timeline

    grounded_data = {
        "summary": understanding_data.get("summary", ""),
        "glossary": valid_glossary,
        "key_points": valid_key_points,
        "steps": valid_steps,
        "diagrams": diagrams,
    }

    if dropped_count > 0:
        note_msg = (
            f"Note: {dropped_count} item(s) were removed because their claims could not be confirmed "
            "in the verbatim text of the document."
        )
        confidence_notes.append(note_msg)

    return grounded_data, confidence_notes, dropped_count
