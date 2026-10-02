"""Loader and compiler for deterministic red-flag detection rules."""

import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

from app.core.logging import logger


class RuleDefinition(BaseModel):
    """Raw rule definition parsed from patterns.yaml."""

    code: str
    severity: str
    description: str
    phrases: Dict[str, List[str]] = Field(default_factory=dict)
    negations: Dict[str, List[str]] = Field(default_factory=dict)
    regex: List[str] = Field(default_factory=list)


class CompiledRule(BaseModel):
    """Rule compiled once for fast in-memory execution."""

    code: str
    severity: str
    description: str
    all_phrases: List[str]
    all_negations: List[str]
    compiled_regexes: List[re.Pattern]
    compiled_negation_regexes: List[re.Pattern]

    model_config = {
        "arbitrary_types_allowed": True,
    }


def _resolve_rules_path(custom_path: Optional[str] = None) -> Path:
    """Resolve path to patterns.yaml."""
    if custom_path:
        p = Path(custom_path)
        if p.is_file():
            return p.resolve()

    # Try relative to cwd or backend root
    candidates = [
        Path.cwd() / "data" / "rules" / "patterns.yaml",
        Path.cwd() / "backend" / "data" / "rules" / "patterns.yaml",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "rules" / "patterns.yaml",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()

    raise FileNotFoundError("Could not locate data/rules/patterns.yaml")


def load_rules(file_path: Optional[str] = None) -> List[CompiledRule]:
    """Load, strictly validate, and precompile rules from patterns.yaml.

    Fails loudly with clear error messages on malformed YAML or invalid regular expressions.
    """
    path = _resolve_rules_path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "rules" not in data:
        raise ValueError(f"No 'rules' root key found in {path}")

    compiled_rules: List[CompiledRule] = []

    for idx, rule_raw in enumerate(data["rules"]):
        try:
            rule_def = RuleDefinition(**rule_raw)
        except Exception as exc:
            raise ValueError(f"Invalid rule definition at index {idx} in {path}: {exc}") from exc

        # Flatten and normalize all phrases
        all_phrases: List[str] = []
        for lang_key, phrases in rule_def.phrases.items():
            for phrase in phrases:
                if phrase and phrase.strip():
                    norm = unicodedata.normalize("NFC", phrase.strip())
                    all_phrases.append(norm)

        # Flatten and normalize all negation phrases
        all_negations: List[str] = []
        for lang_key, negs in rule_def.negations.items():
            for neg in negs:
                if neg and neg.strip():
                    norm = unicodedata.normalize("NFC", neg.strip())
                    all_negations.append(norm)

        # Precompile regular expressions (fail loudly if any regex is invalid)
        compiled_regexes: List[re.Pattern] = []
        for regex_str in rule_def.regex:
            try:
                c_re = re.compile(regex_str)
                compiled_regexes.append(c_re)
            except re.error as re_err:
                raise ValueError(
                    f"Invalid regular expression in rule '{rule_def.code}': '{regex_str}'. Error: {re_err}"
                ) from re_err

        # Precompile phrase matching regex if phrases exist
        # Sort by length descending to match longest phrases first
        compiled_negation_regexes: List[re.Pattern] = []
        for neg in all_negations:
            try:
                # Escape phrase for safe regex matching
                escaped = re.escape(neg)
                compiled_negation_regexes.append(re.compile(f"(?i)(?:^|\\b|\\s){escaped}(?:\\b|\\s|$)"))
            except Exception as exc:
                logger.warning("Failed to compile negation phrase '%s': %s", neg, exc)

        compiled_rule = CompiledRule(
            code=rule_def.code,
            severity=rule_def.severity,
            description=rule_def.description,
            all_phrases=all_phrases,
            all_negations=all_negations,
            compiled_regexes=compiled_regexes,
            compiled_negation_regexes=compiled_negation_regexes,
        )
        compiled_rules.append(compiled_rule)

    logger.info("Successfully compiled %d red-flag rules from %s", len(compiled_rules), path)
    return compiled_rules
