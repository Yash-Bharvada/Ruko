"""Pause plan builder providing decision card, cooling-off reminder, and loss arithmetic."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from app.modules.pause.ics import generate_cooling_off_ics
from app.modules.pause.share import build_whatsapp_share_link
from app.modules.verdict.engine import assert_no_advice
from app.modules.verdict.i18n import normalize_lang_code

# Exactly 3 localized decision questions
DECISION_QUESTIONS = {
    "en": [
        "Why am I doing this?",
        "Who benefits if I pay?",
        "Could I afford to lose this money?",
    ],
    "hi": [
        "मैं यह निवेश क्यों कर रहा हूँ?",
        "अगर मैं पैसे चुकाता हूँ, तो वास्तव में किसका फायदा होगा?",
        "क्या मैं यह पूरा पैसा खोने का जोखिम उठा सकता हूँ?",
    ],
    "gu": [
        "હું આ રોકાણ શા માટે કરી રહ્યો છું?",
        "જો હું પૈસા ચૂકવીશ, તો ખરેખર કોને ફાયદો થશે?",
        "શું હું આ બધા પૈસા ગુમાવવાનું જોખમ ઉઠાવી શકું છું?",
    ],
}

LOSS_SENTENCE_TEMPLATES = {
    "en": "This is about {months} months of your living expenses.",
    "hi": "यह राशि आपके लगभग {months} महीनों के घरेलू खर्च के बराबर है।",
    "gu": "આ રકમ તમારા આશરે {months} મહિનાના ઘરખર્ચ બરાબર છે.",
}


class LossArithmetic(BaseModel):
    """Pure arithmetic comparison of proposed amount vs monthly expenses.

    NO predictions, NO return projections, NO statistics.
    """

    amount: float = Field(..., description="Proposed investment amount")
    months_of_expenses: float = Field(..., description="Amount divided by monthly expenses (1 decimal)")
    sentence: str = Field(..., description="Localized factual sentence")


class PausePlanRequest(BaseModel):
    """Request payload to construct a pause decision plan."""

    verdict: Literal["strong_red_flags", "cannot_verify", "no_red_flags_found", "out_of_scope"] = Field(
        ...,
        description="Verdict for contextualizing the pause plan",
    )
    language: Optional[str] = Field("en", description="Target language (gu, hi, en)")
    amount: Optional[float] = Field(None, ge=0, description="Optional investment amount mentioned")
    monthly_expenses: Optional[float] = Field(None, ge=0, description="Optional monthly household living expenses")


class PausePlan(BaseModel):
    """Full pause and cooling-off plan returned to user."""

    decision_questions: List[str] = Field(..., description="Exactly 3 localized self-reflection questions")
    cooling_off_hours: int = Field(24, description="Recommended cooling-off hours before moving money")
    loss_arithmetic: Optional[LossArithmetic] = Field(None, description="Pure arithmetic of expenses if provided")
    calendar_ics: str = Field(..., description="RFC 5545 calendar event text for 24h reminder")
    calendar_data_uri: str = Field(..., description="Data URI for downloading the .ics calendar file")
    share_link: str = Field(..., description="WhatsApp share link to discuss with family before paying")
    share_text: str = Field(..., description="Unencoded templated text for sharing")


def build_plan(
    verdict: str,
    lang: Optional[str] = "en",
    amount: Optional[float] = None,
    monthly_expenses: Optional[float] = None,
) -> PausePlan:
    """Build a comprehensive cooling-off decision plan.

    Guarantees:
    - Exactly 3 localized self-reflection questions.
    - Loss arithmetic computed ONLY if both amount and monthly_expenses > 0.
    - 24-hour RFC 5545 cooling-off calendar event with alarm.
    - User-initiated WhatsApp share link containing zero raw message text.
    - Scanned with assert_no_advice.
    """
    target_lang = normalize_lang_code(lang)

    # 1. Decision questions (exactly 3)
    raw_questions = DECISION_QUESTIONS.get(target_lang, DECISION_QUESTIONS["en"])
    decision_questions = [assert_no_advice(q) for q in raw_questions]

    # 2. Loss arithmetic (pure arithmetic, NO predictions)
    loss_arithmetic: Optional[LossArithmetic] = None
    if (
        amount is not None
        and monthly_expenses is not None
        and amount > 0
        and monthly_expenses > 0
    ):
        months_ratio = round(amount / monthly_expenses, 1)
        template = LOSS_SENTENCE_TEMPLATES.get(target_lang, LOSS_SENTENCE_TEMPLATES["en"])
        sentence = template.format(months=f"{months_ratio:.1f}")
        loss_arithmetic = LossArithmetic(
            amount=amount,
            months_of_expenses=months_ratio,
            sentence=assert_no_advice(sentence),
        )

    # 3. Calendar .ics
    ics_text, data_uri = generate_cooling_off_ics(lang=target_lang, delay_hours=24)

    # 4. WhatsApp share link
    share_link, share_text = build_whatsapp_share_link(verdict=verdict, lang=target_lang)

    return PausePlan(
        decision_questions=decision_questions,
        cooling_off_hours=24,
        loss_arithmetic=loss_arithmetic,
        calendar_ics=ics_text,
        calendar_data_uri=data_uri,
        share_link=share_link,
        share_text=share_text,
    )
