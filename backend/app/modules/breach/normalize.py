"""Stateless email and phone normalization utilities."""

import re
from app.core.errors import AppException


_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$"
)

_E164_REGEX = re.compile(
    r"^\+[1-9]\d{7,14}$"
)


def normalize_email(email: str) -> str:
    """Normalize and validate email address.

    Trims whitespace, converts to lowercase, and enforces valid email syntax.
    Raises AppException(422) if invalid.
    """
    if not email or not isinstance(email, str):
        raise AppException(
            status_code=422,
            code="invalid_email",
            message="A valid email address is required.",
        )

    cleaned = email.strip().lower()
    if len(cleaned) < 5 or len(cleaned) > 320 or not _EMAIL_REGEX.match(cleaned):
        raise AppException(
            status_code=422,
            code="invalid_email",
            message="Please provide a valid email format (e.g. user@example.com).",
        )

    return cleaned


def normalize_phone_e164(phone: str) -> str:
    """Normalize and validate phone number to E.164 format (+[country_code][number]).

    Strips hyphens, spaces, and parentheses. Requires leading '+' with 8-15 digits.
    Raises AppException(422) if invalid.
    """
    if not phone or not isinstance(phone, str):
        raise AppException(
            status_code=422,
            code="invalid_phone",
            message="A valid E.164 phone number is required.",
        )

    cleaned = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not cleaned.startswith("+"):
        # If user forgot '+', but passed 10-12 digits starting with country code, or starts with 91
        if len(cleaned) == 10 and cleaned.isdigit():
            # Default to India (+91) for standard 10-digit Indian numbers
            cleaned = f"+91{cleaned}"
        else:
            cleaned = f"+{cleaned}"

    if not _E164_REGEX.match(cleaned):
        raise AppException(
            status_code=422,
            code="invalid_phone",
            message="Phone number must be in valid international E.164 format (e.g. +919876543210).",
        )

    return cleaned
