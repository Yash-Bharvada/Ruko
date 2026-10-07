"""Deterministic, conservative risk classifier for breach exposure categories."""

from typing import List, Tuple, Set


# Explicit financial categories that trigger financial_exposure=True
_FINANCIAL_KEYWORDS: Set[str] = {
    "bank account",
    "bank accounts",
    "credit card",
    "credit cards",
    "debit card",
    "debit cards",
    "card details",
    "cvv",
    "payment info",
    "payment histories",
    "payment history",
    "financial transactions",
    "credit card details",
    "salary",
    "banking",
    "financial data",
    "upi",
    "tax records",
}

# High-risk credentials & identity documents
_HIGH_RISK_KEYWORDS: Set[str] = {
    "password",
    "passwords",
    "password hashes",
    "plaintext passwords",
    "auth token",
    "auth tokens",
    "authentication tokens",
    "security question",
    "security questions",
    "private key",
    "private keys",
    "social security number",
    "ssn",
    "aadhaar",
    "pan",
    "passport",
    "passports",
    "driver's license",
    "driver licenses",
    "national id",
    "government issued id",
    "identity document",
    "identity documents",
    "biometric",
    "credentials",
}

# Medium-risk personal contact & identity data
_MEDIUM_RISK_KEYWORDS: Set[str] = {
    "phone number",
    "phone numbers",
    "mobile number",
    "physical address",
    "home address",
    "date of birth",
    "dates of birth",
    "dob",
    "personal address",
    "reused-password indication",
    "personal profile",
    "family members",
}


def classify_exposure(categories: List[str]) -> Tuple[str, bool]:
    """Classify risk level and financial exposure based strictly on explicit categories.

    Returns:
        (risk_level: "HIGH" | "MEDIUM" | "LOW", financial_exposure: bool)
    """
    normalized_cats = [cat.strip().lower() for cat in categories if cat and isinstance(cat, str)]

    # 1. Check for explicit financial exposure
    has_financial = False
    for cat in normalized_cats:
        for fin_kw in _FINANCIAL_KEYWORDS:
            if fin_kw in cat:
                has_financial = True
                break
        if has_financial:
            break

    # 2. Check for HIGH risk triggers (financial, credentials, identity docs)
    is_high = has_financial
    if not is_high:
        for cat in normalized_cats:
            for high_kw in _HIGH_RISK_KEYWORDS:
                if high_kw in cat:
                    is_high = True
                    break
            if is_high:
                break

    if is_high:
        return "HIGH", has_financial

    # 3. Check for MEDIUM risk triggers (phone, address, dob, personal profile combos)
    has_medium = False
    for cat in normalized_cats:
        for med_kw in _MEDIUM_RISK_KEYWORDS:
            if med_kw in cat:
                has_medium = True
                break
        if has_medium:
            break

    # Phone + Email or Personal profile combos
    has_email = any("email" in cat for cat in normalized_cats)
    has_phone = any("phone" in cat or "mobile" in cat for cat in normalized_cats)
    if has_phone or has_medium or (has_email and len(normalized_cats) >= 3):
        return "MEDIUM", has_financial

    # Default to LOW (username-only, website activity, or public profile)
    return "LOW", has_financial

