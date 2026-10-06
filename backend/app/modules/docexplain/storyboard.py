"""Storyboard builder generating 4-8 scenes for browser-rendered video with signed TTS tokens."""

import re
import time
from typing import Any, Dict, List, Optional

from app.core.config import Settings, get_settings
from app.core.schemas import Diagrams, FlowGraph, GlossaryItem, KeyPoint, Scene, SceneVisual, Step, TimelineItem
from app.modules.docexplain.advice_filter import sanitize_text_field
from app.modules.docexplain.signing import generate_speak_token
from app.modules.verdict.i18n import get_disclaimer, t


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences without splitting on numbers, decimals, or inside abbreviations."""
    # Split on space following:
    # 1. Any of ! ? ; । ॥
    # 2. A period preceded by a non-digit non-space character
    # 3. A period preceded by a digit when followed by an uppercase letter or Indic character
    pattern = r'(?<=[!?;।॥])\s+|(?<=[^\d\s]\.)\s+|(?<=\d\.)\s+(?=[A-Z\u0900-\u0D7F])'
    raw = re.split(pattern, text)
    return [s.strip() for s in raw if s.strip()]


def clean_symbols_and_urls(text: str, language: str = "en") -> str:
    """TTS-friendly symbol/URL cleaning."""
    clean = text
    pct_word = " percent"
    if language == "hi":
        pct_word = " प्रतिशत"
    elif language == "gu":
        pct_word = " ટકા"

    clean = clean.replace("%", pct_word)
    clean = clean.replace("&", " and ")
    clean = clean.replace("@", " at ")
    # Replace parentheses and brackets with spaces (e.g. '(24 EMIs)' -> ' 24 EMIs ')
    clean = re.sub(r'[\(\)\[\]\{\}]', ' ', clean)
    # Remove markdown asterisks, hashes, underscores, backticks, tildes, pipes, carrots
    clean = re.sub(r'[*#_`~|\\^<>]', '', clean)
    # Remove URLs if any
    clean = re.sub(r'https?://\S+|www\.\S+|t\.me/\S+', '', clean)
    # Collapse multiple hyphens or em dashes to comma pause
    clean = re.sub(r'--+|—+', ', ', clean)
    return " ".join(clean.split())


def normalize_narration(text: str) -> str:
    """Normalize whitespace and collapse multiple punctuation (no '..' anywhere)."""
    text = re.sub(r'\s+', ' ', text)
    # Collapse repeated dots
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'।{2,}', '।', text)
    text = re.sub(r'([.!?।॥])\s*([.!?।॥])+', r'\1', text)
    # Remove space before punctuation
    text = re.sub(r'\s+([.!?,;।॥])', r'\1', text)
    # Insert space after punctuation only if followed by a letter (never between digits)
    text = re.sub(r'([.!?,;।॥])([A-Za-z\u0900-\u0D7F])', r'\1 \2', text)
    return text.strip()


def truncate_narration(text: str, max_chars: int = 300, language: str = "en") -> str:
    """Shorten narration to max_chars taking whole sentences or cutting at safe word boundary."""
    clean = clean_symbols_and_urls(text, language=language)
    clean = normalize_narration(clean)
    if len(clean) <= max_chars:
        return clean

    sentences = split_into_sentences(clean)
    terminal_char = "।" if (language in ("hi", "gu") and "।" in clean) else "."

    accumulated: List[str] = []
    current_len = 0
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if not re.search(r'[.!?।॥]$', s_clean):
            s_clean += terminal_char

        needed_len = (current_len + 1 + len(s_clean)) if accumulated else len(s_clean)
        if needed_len <= max_chars:
            accumulated.append(s_clean)
            current_len = needed_len
        else:
            break

    if accumulated:
        return normalize_narration(" ".join(accumulated))

    # Even the first sentence exceeds max_chars: cut at last safe word boundary
    first = sentences[0]
    cut_limit = max_chars - 1
    candidate = first[:cut_limit]
    if " " in candidate:
        candidate = candidate.rsplit(" ", 1)[0]

    dangling_words = {
        "inr", "rs", "rs.", "usd", "eur", "gbp", "₹",
        "the", "a", "an", "and", "or", "of", "to", "for", "with", "at", "by", "from", "on",
        "रुपये", "રૂપિયા", "અને", "और",
    }

    while candidate:
        candidate = re.sub(r'[\s.,;:\-–—!?।॥]+$', '', candidate)
        last_word = candidate.split()[-1].lower() if candidate.split() else ""
        if last_word in dangling_words:
            candidate = candidate.rsplit(" ", 1)[0]
        elif re.search(r'[\d,]+\.$|[\d]+\,$', candidate):
            candidate = candidate.rsplit(" ", 1)[0]
        else:
            break

    candidate = re.sub(r'[\s.,;:\-–—!?।॥]+$', '', candidate)
    if not candidate:
        return ""

    return normalize_narration(candidate + terminal_char)


def join_items_narration(items: List[str], terminal: str = ".") -> str:
    """Join multiple item strings, stripping trailing sentence punctuation from each before joining."""
    cleaned_items: List[str] = []
    for item in items:
        clean_item = re.sub(r'[\s.,;:\-–—!?।॥]+$', '', item.strip())
        if clean_item:
            cleaned_items.append(clean_item)
    if not cleaned_items:
        return ""
    joined = f"{terminal} ".join(cleaned_items) + terminal
    return normalize_narration(joined)


def _clean_tts_narration(
    text: str,
    source_text: str = "",
    max_chars: int = 300,
    language: str = "en",
) -> str:
    """Prepare a plain sentence string suitable for TTS voice synthesis (no symbols/URLs)."""
    clean, _ = sanitize_text_field(text, source_text)
    return truncate_narration(clean, max_chars=max_chars, language=language)


def _format_flow_nodes(nodes: List[Any], language: str = "en") -> str:
    """Narrate flowchart or money flow nodes in order with localized connector words."""
    if not nodes:
        return ""

    first_conn = t("flow_first", language)
    then_conn = t("flow_then", language)
    finally_conn = t("flow_finally", language)

    # Clean each label of trailing punctuation
    labels = [re.sub(r'[\s.,;:\-–—!?।॥]+$', '', getattr(n, "label", str(n)).strip()) for n in nodes[:4]]
    labels = [l for l in labels if l]

    if not labels:
        return ""
    if len(labels) == 1:
        return f"{first_conn}, {labels[0]}."
    if len(labels) == 2:
        return f"{first_conn}, {labels[0]}. {finally_conn}, {labels[1]}."

    parts = [f"{first_conn}, {labels[0]}."]
    for l in labels[1:-1]:
        parts.append(f"{then_conn}, {l}.")
    parts.append(f"{finally_conn}, {labels[-1]}.")

    return " ".join(parts)


def _format_timeline_items(items: List[TimelineItem], language: str = "en") -> str:
    """Narrate timeline items in order with localized connector words and date_text."""
    if not items:
        return ""

    first_conn = t("flow_first", language)
    then_conn = t("flow_then", language)
    finally_conn = t("flow_finally", language)
    on_conn = t("flow_on", language)

    formatted_items: List[str] = []
    for it in items[:3]:
        lbl = re.sub(r'[\s.,;:\-–—!?।॥]+$', '', it.label.strip())
        dt = re.sub(r'[\s.,;:\-–—!?।॥]+$', '', it.date_text.strip())
        if not lbl and not dt:
            continue
        if dt and dt.lower() not in lbl.lower():
            formatted_items.append(f"{lbl} {on_conn} {dt}")
        else:
            formatted_items.append(lbl or dt)

    if not formatted_items:
        return ""
    if len(formatted_items) == 1:
        return f"{first_conn}, {formatted_items[0]}."
    if len(formatted_items) == 2:
        return f"{first_conn}, {formatted_items[0]}. {finally_conn}, {formatted_items[1]}."

    parts = [f"{first_conn}, {formatted_items[0]}."]
    for fi in formatted_items[1:-1]:
        parts.append(f"{then_conn}, {fi}.")
    parts.append(f"{finally_conn}, {formatted_items[-1]}.")

    return " ".join(parts)


def build_storyboard(
    request_id: str,
    summary: str,
    glossary: List[GlossaryItem],
    key_points: List[KeyPoint],
    steps: List[Step],
    diagrams: Diagrams,
    language: str = "en",
    source_text: str = "",
    settings: Optional[Settings] = None,
) -> List[Scene]:
    """Assemble 4 to 8 scenes from grounded content and sign each narration.

    Scene Sequence:
    1. Scene 1: Title & Overview (Summary)
    2. Scene 2..N: Key Points & Critical Clauses
    3. Scene Flowchart / Timeline (if available)
    4. Scene Next Steps
    5. Final Scene: Educational Disclaimer (mandatory)
    """
    conf = settings or get_settings()
    now_ts = int(time.time())
    scenes: List[Scene] = []

    # Helper to add scene
    def add_scene(
        scene_id: str,
        raw_narration: str,
        raw_caption: str,
        visual_type: str,
        visual_ref: Optional[str] = None,
    ) -> None:
        narration = _clean_tts_narration(raw_narration, source_text, max_chars=300, language=language)
        caption = raw_caption[:80].strip()
        token = generate_speak_token(
            request_id=request_id,
            scene_id=scene_id,
            language=language,
            issued_at=now_ts,
            narration=narration,
            settings=conf,
        )
        scenes.append(
            Scene(
                scene_id=scene_id,
                narration=narration,
                caption=caption,
                visual=SceneVisual(type=visual_type, ref=visual_ref),  # type: ignore[arg-type]
                issued_at=now_ts,
                speak_token=token,
            )
        )

    # 1. Scene 1: Document Overview (Title visual)
    intro_narration = summary if summary else "Here is a plain language breakdown of your uploaded document."
    add_scene("scene_1", intro_narration, "Document Overview", "title", "overview")

    # 2. Scene 2: Critical Obligations & Fees (Bullets visual)
    fee_or_risk_kps = [kp for kp in key_points if kp.category in ("fee", "risk", "obligation")]
    if fee_or_risk_kps:
        kp_narrations = join_items_narration([kp.text for kp in fee_or_risk_kps[:2]])
        add_scene(f"scene_{len(scenes) + 1}", kp_narrations, "Key Obligations & Risks", "bullets", "key_obligations")
    elif key_points:
        kp_narrations = join_items_narration([kp.text for kp in key_points[:2]])
        add_scene(f"scene_{len(scenes) + 1}", kp_narrations, "Key Terms", "bullets", "key_points")

    # 3. Scene 3: Flowchart or Money Flow (if available)
    if diagrams.flowchart and diagrams.flowchart.nodes:
        fc_title = diagrams.flowchart.title or "Process Flow"
        fc_narration = _format_flow_nodes(diagrams.flowchart.nodes, language=language)
        add_scene(f"scene_{len(scenes) + 1}", fc_narration, fc_title, "flowchart", "flowchart_1")
    elif diagrams.money_flow and diagrams.money_flow.nodes:
        mf_title = diagrams.money_flow.title or "Payment Flow"
        mf_narration = _format_flow_nodes(diagrams.money_flow.nodes, language=language)
        add_scene(f"scene_{len(scenes) + 1}", mf_narration, mf_title, "money_flow", "money_flow_1")

    # 4. Scene 4: Actionable Steps (if available)
    if steps:
        step_narrations = join_items_narration([f"Step {s.order}: {s.title}" for s in steps[:2]])
        add_scene(f"scene_{len(scenes) + 1}", step_narrations, "Next Steps & Deadlines", "bullets", "steps")

    # 5. Scene 5: Timeline (if available and total scenes < 7)
    if diagrams.timeline and len(scenes) < 7:
        tl_narration = _format_timeline_items(diagrams.timeline, language=language)
        add_scene(f"scene_{len(scenes) + 1}", tl_narration, "Important Deadlines", "timeline", "timeline_1")

    # 6. Final Mandatory Scene: Disclaimer
    disclaimer_text = get_disclaimer("en" if language in ("hinglish", "gujlish") else language)
    add_scene(
        f"scene_{len(scenes) + 1}",
        disclaimer_text,
        "Notice & Educational Disclaimer",
        "title",
        "disclaimer",
    )

    # Ensure scene count is between 4 and 8
    while len(scenes) < 4:
        # Pad with grounded key points or glossary scene before disclaimer
        disc_scene = scenes.pop()
        pad_idx = len(scenes) + 1
        if glossary:
            g = glossary[0]
            add_scene(
                f"scene_{pad_idx}",
                join_items_narration([f"{g.term}: {g.meaning}"]),
                f"Glossary: {g.term[:30]}",
                "bullets",
                "glossary",
            )
        else:
            add_scene(
                f"scene_{pad_idx}",
                "Review all terms carefully before making financial commitments.",
                "Important Consideration",
                "bullets",
                "summary",
            )
        scenes.append(disc_scene)

    if len(scenes) > 8:
        # Keep first scenes and last disclaimer scene
        scenes = scenes[:7] + [scenes[-1]]

    # Re-index scene IDs
    for idx, s in enumerate(scenes, start=1):
        s.scene_id = f"scene_{idx}"
        # Re-sign with updated scene_id
        s.speak_token = generate_speak_token(
            request_id=request_id,
            scene_id=s.scene_id,
            language=language,
            issued_at=s.issued_at,
            narration=s.narration,
            settings=conf,
        )

    return scenes
