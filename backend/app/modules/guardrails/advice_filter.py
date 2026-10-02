"""Advice filter guardrail detecting when users seek investment tips or price predictions."""

import re
from typing import Optional

# Comprehensive patterns detecting investment advice requests (en, hi, gu, roman)
ADVICE_REQUEST_PATTERNS = [
    # English queries
    re.compile(r"(?i)\b(?:which|what)\s*(?:stock|share|crypto|mutual\s*fund|coin)\s*(?:should|can|to)\s*(?:i|we)\s*(?:buy|invest|purchase|pick)\b"),
    re.compile(r"(?i)\b(?:give|tell|suggest|recommend)\s*(?:me|us)?\s*(?:some|a|good|best|multibagger)?\s*(?:stocks?|shares?|tips?|calls?)\b"),
    re.compile(r"(?i)\b(?:best|top)\s*(?:stocks?|shares?|cryptos?)\s*(?:to\s*buy|for\s*10x|for\s*2026|for\s*tomorrow)\b"),
    re.compile(r"(?i)\b(?:target\s*price|price\s*target|forecast)\s*(?:for|of)\b"),
    re.compile(r"(?i)\b(?:is\s*it\s*good\s*time\s*to\s*buy|will\s*it\s*go\s*up)\b"),
    # Hindi / Roman Hindi queries
    re.compile(r"(?i)\b(?:kaunsa|konsa|kisme|kis)\s*(?:share|stock|company)\s*(?:lu|kharidu|me\s*invest\s*karu|me\s*paisa\s*lagau)\b"),
    re.compile(r"(?i)\b(?:share|stock)\s*(?:kaunsa\s*kharidu|batao|suggest\s*karo)\b"),
    re.compile(r"(?i)\b(?:trading|intraday)\s*(?:tips?|calls?)\s*(?:do|chahiye)\b"),
    re.compile(r"कौन\s*सा\s*शेयर\s*(?:खरीदूं|लूं|खरीदना\s*चाहिए)"),
    re.compile(r"किस\s*कंपनी\s*में\s*(?:निवेश\s*करें|पैसा\s*लगाएं)"),
    # Gujarati / Roman Gujarati queries
    re.compile(r"(?i)\b(?:kayo|kainso|kya)\s*(?:share|stock)\s*(?:kharidvo|kharidu|levo|leva\s*jevo\s*che)\b"),
    re.compile(r"(?i)\b(?:kya\s*stock\s*ma|kya\s*share\s*ma)\s*(?:paisa\s*lagavva|rokan\s*karvu)\b"),
    re.compile(r"કયો\s*શેર\s*(?:ખરીદવો|લેવો|લેવા\s*જેવો\s*છે)"),
    re.compile(r"કયા\s*(?:સ્ટોક|શેર)માં\s*રોકાણ\s*કરવું"),
]


def is_advice_request(text: Optional[str]) -> bool:
    """Detect whether user input is an investment advice request.

    If True, the platform returns 'out_of_scope' verdict since Ruko is strictly
    an educational scam detection tool, never a stock adviser or financial planner.
    """
    if not text or not isinstance(text, str):
        return False

    cleaned = text.strip()
    for pattern in ADVICE_REQUEST_PATTERNS:
        if pattern.search(cleaned):
            return True

    return False
