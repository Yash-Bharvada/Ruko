"""Claim extraction module for structured fact identification."""

from app.modules.extractor.claims import (
    Claims,
    PaymentRequest,
    PromisedReturn,
    detect_script_language,
    extract_claims,
)
from app.modules.extractor.llm_client import LLMClient

__all__ = [
    "Claims",
    "PaymentRequest",
    "PromisedReturn",
    "detect_script_language",
    "extract_claims",
    "LLMClient",
]
