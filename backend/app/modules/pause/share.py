"""User-initiated WhatsApp share link generator for family and trusted advisers."""

import urllib.parse
from typing import Tuple

from app.modules.verdict.engine import assert_no_advice
from app.modules.verdict.i18n import normalize_lang_code

# Localized verdict phrases for share message
VERDICT_PHRASES = {
    "en": {
        "strong_red_flags": "Strong red flags were detected",
        "cannot_verify": "Could not verify authenticity",
        "no_red_flags_found": "No known red flags were found (caution advised)",
        "out_of_scope": "Analysis out of scope",
    },
    "hi": {
        "strong_red_flags": "गंभीर रेड फ्लैग (धोखाधड़ी के संकेत) पाए गए",
        "cannot_verify": "सत्यता की पुष्टि नहीं हो सकी",
        "no_red_flags_found": "कोई जाना-पहचाना रेड फ्लैग नहीं मिला (फिर भी सावधानी बरतें)",
        "out_of_scope": "विश्लेषण के दायरे से बाहर",
    },
    "gu": {
        "strong_red_flags": "ગંભીર રેડ ફ્લેગ (છેતરપિંડીના સંકેત) મળ્યા",
        "cannot_verify": "વિશ્વસનીયતાની પુષ્ટિ થઈ શકી નથી",
        "no_red_flags_found": "કોઈ જાણીતો રેડ ફ્લેગ મળ્યો નથી (તેમ છતાં સાવચેતી રાખો)",
        "out_of_scope": "વિશ્લેષણના ક્ષેત્ર બહાર",
    },
}

SHARE_TEMPLATES = {
    "en": "I checked an investment message with Ruko: {phrase}. Please talk to me before I pay anyone.",
    "hi": "मैंने रुको (Ruko) ऐप पर एक निवेश संदेश की जांच की: {phrase}। कृपया पैसे भेजने से पहले मुझसे बात करें।",
    "gu": "મેં રૂકો (Ruko) એપ પર એક રોકાણ સંદેશની તપાસ કરી: {phrase}। મહેરબાની કરીને કોઈને નાણાં મોકલતા પહેલા મારી સાથે વાત કરો.",
}


def build_whatsapp_share_link(
    verdict: str,
    lang: str = "en",
) -> Tuple[str, str]:
    """Generate user-initiated WhatsApp share link with templated summary.

    PRIVACY & INTEGRITY GUARANTEES:
    - Never includes raw user message text, numbers, or URLs.
    - Completely user-initiated: backend never contacts third parties or recipients.
    - Scanned with assert_no_advice.
    - Returns (share_url, share_text).
    """
    target_lang = normalize_lang_code(lang)
    lang_phrases = VERDICT_PHRASES.get(target_lang, VERDICT_PHRASES["en"])
    phrase = lang_phrases.get(verdict, lang_phrases["cannot_verify"])

    template = SHARE_TEMPLATES.get(target_lang, SHARE_TEMPLATES["en"])
    raw_share_text = template.format(phrase=phrase)

    # Safety check
    share_text = assert_no_advice(raw_share_text)
    encoded_text = urllib.parse.quote(share_text)
    share_url = f"https://wa.me/?text={encoded_text}"

    return share_url, share_text
