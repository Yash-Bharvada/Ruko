"""Pause layer endpoints: cooling-off decision plan and recovery checklist."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Query

from app.modules.pause.plan import PausePlan, PausePlanRequest, build_plan
from app.modules.pause.resources import get_already_paid_resources

router = APIRouter(prefix="/v1", tags=["Pause & Recovery"])


@router.post("/pause/plan", response_model=PausePlan)
async def create_pause_plan(req: PausePlanRequest) -> PausePlan:
    """Generate a cooling-off pause plan before money moves.

    Features:
    - 3 localized decision reflection questions.
    - 24-hour cooling-off calendar reminder (.ics text + data URI).
    - WhatsApp family share link.
    - Pure arithmetic of loss vs monthly living expenses.
    """
    return build_plan(
        verdict=req.verdict,
        lang=req.language or "en",
        amount=req.amount,
        monthly_expenses=req.monthly_expenses,
    )


@router.get("/resources/already-paid")
async def get_recovery_resources(
    lang: Optional[str] = Query("en", description="Language code (en, hi, gu)"),
) -> Dict[str, Any]:
    """Retrieve verified recovery checklist for users who already paid money to a scam.

    Includes National Cyber Crime Helpline (1930), Cybercrime portal, and SEBI SCORES portal.
    """
    return get_already_paid_resources(lang=lang)
