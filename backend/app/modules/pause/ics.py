"""RFC 5545 .ics Calendar generator for 24-hour cooling-off reminder."""

import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from app.modules.verdict.engine import assert_no_advice
from app.modules.verdict.i18n import normalize_lang_code

# Localized calendar summaries and descriptions
CALENDAR_TEXTS = {
    "en": {
        "summary": "Ruko Cooling-Off Reminder: Did you verify before paying?",
        "description": "24-hour pause reminder: Verify the claimed adviser on SEBI's official website (sebi.gov.in) and talk to a trusted family member before transferring any funds.",
    },
    "hi": {
        "summary": "रुको कूलिंग-ऑफ रिमाइंडर: क्या आपने पैसे भेजने से पहले जांच की?",
        "description": "24 घंटे का विचार विराम: पैसे भेजने से पहले सेबी (sebi.gov.in) की आधिकारिक वेबसाइट पर जांच करें और अपने परिवार से सलाह लें।",
    },
    "gu": {
        "summary": "રૂકો કૂલિંગ-ઓફ રીમાઇન્ડર: શું તમે ચૂકવણી કરતા પહેલા ખાતરી કરી?",
        "description": "24 કલાકનો વિચાર વિરામ: કોઈપણ નાણાં મોકલતા પહેલા સેબીની સત્તાવાર વેબસાઇટ (sebi.gov.in) પર ચકાસણી કરો અને પરિવાર સાથે ચર્ચા કરો.",
    },
}


def generate_cooling_off_ics(
    lang: str = "en",
    delay_hours: int = 24,
) -> Tuple[str, str]:
    """Generate RFC 5545 .ics calendar content and data URI.

    Guarantees:
    - 24-hour cooling-off reminder with an alarm.
    - Zero user message text or personal data in .ics.
    - Parses cleanly with standard RFC 5545 parsers.
    - Returns (ics_string, data_uri).
    """
    target_lang = normalize_lang_code(lang)
    texts = CALENDAR_TEXTS.get(target_lang, CALENDAR_TEXTS["en"])
    summary = assert_no_advice(texts["summary"])
    description = assert_no_advice(texts["description"])

    now_utc = datetime.now(timezone.utc)
    start_utc = now_utc + timedelta(hours=delay_hours)
    end_utc = start_utc + timedelta(minutes=15)

    dtstamp_str = now_utc.strftime("%Y%m%dT%H%M%SZ")
    dtstart_str = start_utc.strftime("%Y%m%dT%H%M%SZ")
    dtend_str = end_utc.strftime("%Y%m%dT%H%M%SZ")
    event_uid = f"{uuid.uuid4()}@ruko.investorprotection"

    # RFC 5545 format
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Ruko//Investor Protection Cooling Off//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{event_uid}",
        f"DTSTAMP:{dtstamp_str}",
        f"DTSTART:{dtstart_str}",
        f"DTEND:{dtend_str}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        "STATUS:CONFIRMED",
        "BEGIN:VALARM",
        "TRIGGER:-PT0M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{summary}",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]

    ics_content = "\r\n".join(ics_lines) + "\r\n"
    # URL encode for data URI
    encoded_uri = urllib.parse.quote(ics_content)
    data_uri = f"data:text/calendar;charset=utf-8,{encoded_uri}"

    return ics_content, data_uri
