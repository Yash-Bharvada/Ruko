"""Output-side advice filter and URL sanitizer for document explanations."""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import logger
from app.modules.guardrails.advice_filter import ADVICE_REQUEST_PATTERNS

# Additional output-side patterns detecting recommendations, safety claims, or directives
OUTPUT_ADVICE_PATTERNS = ADVICE_REQUEST_PATTERNS + [
    # Action directives
    re.compile(r"(?i)\b(?:you\s+should|you\s+must|we\s+recommend|it\s+is\s+advised\s+to)\s+(?:sign|accept|invest|pay|proceed|buy|sell|transfer)\b"),
    re.compile(r"(?i)\b(?:do\s+not\s+hesitate\s+to|strongly\s+recommended\s+to)\b"),
    # Safety and guarantee claims
    re.compile(r"(?i)\b(?:this\s+is\s+100%\s+safe|this\s+is\s+completely\s+safe|it\s+is\s+safe\s+to|guaranteed\s+returns?|zero\s+risk|risk[\s-]free|legally\s+sound|fraud[\s-]free)\b"),
    re.compile(r"(?i)\b(?:great\s+deal|fair\s+terms|highly\s+profitable|multibagger)\b"),
    # Hindi / Hinglish output directives
    re.compile(r"(?i)\b(?:aapko|apko)\s*(?:sign\s*karna\s*chahiye|invest\s*karna\s*chahiye|paisa\s*lagana\s*chahiye|kharidna\s*chahiye)\b"),
    re.compile(r"(?i)\b(?:yeh|ye)\s*(?:surakshit|safe|risk\s*free|guaranteed)\s*hai\b"),
    re.compile(r"आपको\s*(?:हस्ताक्षर\s*करना\s*चाहिए|निवेश\s*करना\s*चाहिए|खरीदना\s*चाहिए)"),
    re.compile(r"यह\s*(?:पूरी\s*तरह\s*सुरक्षित|सुरक्षित|गारंटीड)\s*है"),
    # Gujarati / Gujlish output directives
    re.compile(r"(?i)\b(?:tamare|tamne)\s*(?:sign\s*karvu\s*joie|invest\s*karvu\s*joie|rokan\s*karvu\s*joie)\b"),
    re.compile(r"(?i)\b(?:aa|a)\s*(?:safe|surakshit|guaranteed)\s*che\b"),
    re.compile(r"તમારે\s*(?:રોકાણ\s*કરવું\s*જોઈએ|સહી\s*કરવી\s*જોઈએ)"),
    re.compile(r"આ\s*(?:સંપૂર્ણ\s*સુરક્ષિત|સુરક્ષિત|ગેરંટીવાળું)\s*છે"),
]

# URL / Domain / Phone regexes
URL_PATTERN = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>{}\[\]]+\b")
DOMAIN_PATTERN = re.compile(r"(?i)\b[a-z0-9.-]+\.(?:com|org|net|in|io|co|me|xyz|biz|info)\b")
PHONE_PATTERN = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}\b")


def contains_advice_or_safety_claim(text: Optional[str]) -> bool:
    """Check if text contains financial advice, action directive, or safety claim."""
    if not text or not isinstance(text, str):
        return False
    for pattern in OUTPUT_ADVICE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_text_field(text: str, source_text: str) -> Tuple[str, bool]:
    """Sanitize a text field: neutralize advice/safety phrases and strip unquoted URLs/phones.

    Returns:
        (sanitized_text, was_modified)
    """
    if not text:
        return "", False

    modified = False
    clean = text

    # 1. Neutralize advice / safety claims
    for pattern in OUTPUT_ADVICE_PATTERNS:
        if pattern.search(clean):
            clean = pattern.sub("[statement removed for objective reporting]", clean)
            modified = True

    # 2. Strip URLs not present in the original document
    for match in URL_PATTERN.finditer(clean):
        url = match.group(0)
        if url.lower() not in source_text.lower():
            clean = clean.replace(url, "[external-link-removed]")
            modified = True

    # 3. Strip standalone domains not present in source text
    for match in DOMAIN_PATTERN.finditer(clean):
        domain = match.group(0)
        if domain.lower() not in source_text.lower() and not domain.endswith((".pdf", ".docx", ".txt")):
            clean = clean.replace(domain, "[domain-removed]")
            modified = True

    # 4. Strip phone numbers not present in source text
    for match in PHONE_PATTERN.finditer(clean):
        phone = match.group(0)
        if phone not in source_text:
            clean = clean.replace(phone, "[phone-removed]")
            modified = True

    return clean.strip(), modified


def filter_explanation_output(data: Dict[str, Any], source_text: str) -> Tuple[Dict[str, Any], bool]:
    """Filter all generated explanation fields to ensure zero financial advice and zero promotion.

    Returns:
        (filtered_data, advice_filtered_flag)
    """
    any_filtered = False

    # 1. Summary
    if "summary" in data and isinstance(data["summary"], str):
        cleaned, mod = sanitize_text_field(data["summary"], source_text)
        data["summary"] = cleaned
        if mod:
            any_filtered = True

    # 2. Glossary
    sanitized_glossary = []
    for item in data.get("glossary", []):
        if not isinstance(item, dict):
            continue
        meaning, mod_m = sanitize_text_field(item.get("meaning", ""), source_text)
        term, mod_t = sanitize_text_field(item.get("term", ""), source_text)
        item["meaning"] = meaning
        item["term"] = term
        if mod_m or mod_t:
            any_filtered = True
        sanitized_glossary.append(item)
    data["glossary"] = sanitized_glossary

    # 3. Key Points
    sanitized_key_points = []
    for kp in data.get("key_points", []):
        if not isinstance(kp, dict):
            continue
        kp_text, mod = sanitize_text_field(kp.get("text", ""), source_text)
        kp["text"] = kp_text
        if mod:
            any_filtered = True
        sanitized_key_points.append(kp)
    data["key_points"] = sanitized_key_points

    # 4. Steps
    sanitized_steps = []
    for st in data.get("steps", []):
        if not isinstance(st, dict):
            continue
        st_title, mod_t = sanitize_text_field(st.get("title", ""), source_text)
        st_text, mod_x = sanitize_text_field(st.get("text", ""), source_text)
        st["title"] = st_title
        st["text"] = st_text
        if mod_t or mod_x:
            any_filtered = True
        sanitized_steps.append(st)
    data["steps"] = sanitized_steps

    return data, any_filtered
