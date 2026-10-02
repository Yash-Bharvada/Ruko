"""Validators and normalizers for SEBI registration numbers."""

import re
from typing import Optional, Tuple


# Common SEBI intermediary prefixes mapped to categories
# TODO-VERIFY: Confirm full SEBI intermediary prefix specification against latest master list
SEBI_PREFIX_CATEGORIES = {
    "INA": "Investment Adviser",
    "INH": "Research Analyst",
    "INZ": "Stock Broker",
    "INP": "Portfolio Manager",
    "INF": "Mutual Fund",
    "INR": "Registrar and Share Transfer Agent",
    "INM": "Merchant Banker",
    "INB": "Stock Broker (Cash Segment)",
    "INF": "Stock Broker (Derivatives Segment)",
    "IN0": "Depository Participant",
    "IN-DP": "Depository Participant",
}

# General regex for common SEBI registration number formats
_SEBI_REG_REGEX = re.compile(r"^IN[A-Z0-9]{8,14}$", re.IGNORECASE)


def normalize_reg_no(reg_no: str) -> str:
    """Normalize registration number by removing spaces, hyphens, slashes, and uppercasing.

    Example: 'ina-0000 00001' -> 'INA000000001'
    """
    if not reg_no or not isinstance(reg_no, str):
        return ""
    # Strip whitespace, dashes, slashes, dots
    cleaned = re.sub(r"[\s\-_/.]", "", reg_no)
    return cleaned.upper()


def validate_reg_no_format(reg_no: str) -> Tuple[bool, Optional[str]]:
    """Check if string matches standard SEBI registration format.

    IMPORTANT: Format validation is a structural hint only.
    A well-formed registration number is NEVER proof of actual registration.
    """
    norm = normalize_reg_no(reg_no)
    if not norm:
        return False, None

    is_valid_format = bool(_SEBI_REG_REGEX.match(norm))
    inferred_category = None

    for prefix, cat in SEBI_PREFIX_CATEGORIES.items():
        clean_prefix = re.sub(r"[\s\-_/.]", "", prefix).upper()
        if norm.startswith(clean_prefix):
            inferred_category = cat
            break

    return is_valid_format, inferred_category
