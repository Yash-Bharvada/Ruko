"""Stateless breach exposure check orchestrator module."""

import uuid
from typing import Optional

from app.core.config import Settings, get_settings
from app.core.errors import AppException
from app.core.schemas import BreachCheckResult
from app.modules.breach.normalize import normalize_email
from app.modules.breach.providers import get_breach_provider


DATA_SAFETY_GUARANTEES = [
    "Minimal data collection: queries email address only with explicit user consent.",
    "No passwords, OTPs, PINs, CVVs, or banking credentials are ever accepted or stored.",
    "No raw leaked credentials stored or processed.",
    "Zero persistence: processed strictly in-memory and discarded after response.",
    "No identifiers or PII stored on disk or server databases.",
]


async def run_breach_check(
    email: str,
    consent: bool,
    settings: Optional[Settings] = None,
    request_id: Optional[str] = None,
) -> BreachCheckResult:
    """Perform a stateless email breach check with consent enforcement and risk evaluation.

    Guarantees:
    - Rejects request if consent is False.
    - Normalizes and validates email syntax.
    - Never stores identifiers or query records.
    - Honest status handling (returns 'scan_unavailable' on upstream provider failure).
    """
    conf = settings or get_settings()
    req_id = request_id or str(uuid.uuid4())

    if not consent:
        raise AppException(
            status_code=422,
            code="consent_required",
            message="Explicit consent is required to perform a breach exposure query.",
        )

    clean_email = normalize_email(email)
    provider = get_breach_provider(conf)

    status, exposures, is_demo, degraded_flags = await provider.check_email(clean_email, conf)

    # Compute aggregate exposure metrics
    high_risk_count = sum(1 for e in exposures if e.risk_level == "HIGH")
    financial_count = sum(1 for e in exposures if e.financial_exposure)

    # Set honest, non-judgmental notice
    if status == "scan_unavailable":
        notice = "Breach scan service is temporarily unavailable. Please retry shortly. Never assume an unverified account is safe."
    elif len(exposures) == 0:
        notice = "No public data breach records were found matching this email. A lack of found records does not guarantee total account safety."
    else:
        notice = (
            f"Found {len(exposures)} known data breach exposure record(s). "
            "A breach exposure indicates your information appeared in a past incident, "
            "but does not necessarily mean your account is currently compromised. "
            "Follow the remediation steps for each exposure."
        )

    return BreachCheckResult(
        request_id=req_id,
        status=status,
        is_demo=is_demo,
        exposures=exposures,
        total_exposures=len(exposures),
        high_risk_count=high_risk_count,
        financial_exposure_count=financial_count,
        notice=notice,
        data_safety=DATA_SAFETY_GUARANTEES,
        degraded=degraded_flags,
    )
