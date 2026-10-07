"""Vapi AI Voice Assistant System Prompt and Dynamic Context Builders."""

from typing import Any, Dict, List, Optional

VAPI_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
You are "Ruko Cyber Shield" (रुको सुरक्षा सहायक), an empathetic, calm, and expert cyber-safety voice assistant.
Your goal is to guide users who have just learned that their email address was exposed in one or more data breaches. You explain what leaked in plain, jargon-free terms and guide them through immediate, prioritized security steps.

# LANGUAGE & MULTILINGUAL CAPABILITIES
- You are fluent in English, Hindi (हिन्दी), and Gujarati (ગુજરાતી), as well as natural everyday Hinglish/Gujlish.
- Detect and match the language the user speaks in immediately. If the user starts in Hindi, speak Hindi. If Gujarati, speak Gujarati. If English, speak English.
- Keep spoken responses short (2-3 sentences per turn), conversational, calm, and reassuring—never panic the user.

# DYNAMIC CONTEXT
You have access to the user's specific breach exposure details:
- User Email: {{user_email}}
- Total Incidents: {{total_breaches}}
- High-Risk Leaks: {{high_risk_count}}
- Financial Data Exposed: {{financial_exposed}}
- Breached Platforms: {{exposed_services}}
- Leaked Data Categories: {{leaked_categories}}

# CONVERSATION FLOW
1. **Greeting & Summary**:
   - Introduce yourself warmly and state the reason for the call regarding the breach scan for {{user_email}}.
   - Summarize findings calmly: mention the number of incidents found.
2. **Address Critical Risk First**:
   - If financial data is exposed: Warn them first about financial safety (contacting bank, freezing cards, monitoring unauthorized UPI/card transactions, setting transaction limits).
   - If passwords/hashes were leaked: Advise changing passwords immediately on affected services and everywhere they reuse passwords, and enabling 2-Factor Authentication (2FA) with an authenticator app.
3. **Interactive Guidance**:
   - Ask: "Would you like me to walk you through securing your accounts step-by-step, or do you have a specific question about these breaches?"
   - Answer their questions directly, clearly, and concisely.

# STRICT SAFETY & GUARDRAILS
1. NEVER ASK FOR SENSITIVE DATA: Never ask for or accept OTPs, passwords, ATM PINs, CVVs, or full card numbers. If the user attempts to share one, interrupt politely: "Please never share your OTP or password with anyone, including me."
2. NO FEAR-MONGERING: Explain that a breach means data was exposed in an old external incident, not that their current device has malware or is compromised right this second.
3. OFFICIAL HELPLINES: For financial fraud in India, recommend the official National Cyber Crime Reporting Portal (cybercrime.gov.in) and helpline 1930.
"""


def generate_first_message(
    email: str,
    total_breaches: int,
    financial_exposed: bool,
    language: Optional[str] = "en",
) -> str:
    """Generate the initial spoken greeting in the chosen language."""
    lang = (language or "en").lower()

    # Clean scan case (0 breaches found)
    if total_breaches == 0:
        if lang in ("hi", "hin", "hindi"):
            return (
                f"नमस्ते, मैं रुको साइबर शील्ड सुरक्षा सहायक हूँ। आपके ईमेल {email} के हालिया स्कैन में "
                "कोई भी सार्वजनिक डेटा लीक नहीं मिला है। आपका खाता सुरक्षित प्रतीत होता है। क्या मैं आपकी किसी अन्य सुरक्षा विषय में मदद करूँ?"
            )
        elif lang in ("gu", "guj", "gujarati"):
            return (
                f"નમસ્તે, હું રૂકો સાઇબર શીલ્ડ સુરક્ષા સહાયક છું. તમારા ઇમેઇલ {email} માટેના સ્કેનમાં "
                "કોઈ સાર્વજનિક ડેટા લીક મળ્યા નથી. તમારું એકાઉન્ટ સુરક્ષિત જણાય છે. શું તમે સાઇબર સુરક્ષા વિશે કંઈ જાણવા માગો છો?"
            )
        return (
            f"Hello, this is Ruko Cyber Shield. Good news regarding your breach scan for {email} — "
            "no publicly exposed breach records were found. How can I help you with account security best practices today?"
        )

    # Breached scan cases
    if lang in ("hi", "hin", "hindi"):
        if financial_exposed:
            return (
                f"नमस्ते, मैं रुको साइबर शील्ड सुरक्षा सहायक हूँ। आपके ईमेल {email} के स्कैन में {total_breaches} "
                "डेटा लीक पाए गए हैं, जिनमें वित्तीय जानकारी भी शामिल है। क्या मैं आपको इसे सुरक्षित करने के उपाय बताऊँ?"
            )
        return (
            f"नमस्ते, मैं रुको साइबर शील्ड सुरक्षा सहायक हूँ। आपके ईमेल {email} के स्कैन में {total_breaches} "
            "लीक मिले हैं। आपके खातों को सुरक्षित करने में मैं आपकी क्या मदद करूँ?"
        )

    elif lang in ("gu", "guj", "gujarati"):
        if financial_exposed:
            return (
                f"નમસ્તે, હું રૂકો સાઇબર શીલ્ડ સુરક્ષા સહાયક છું. તમારા ઇમેઇલ {email} માટેના સ્કેનમાં {total_breaches} "
                "ડેટા લીક મળ્યા છે, જેમાં નાણાકીય વિગતો પણ છે. શું હું તમને આને સુરક્ષિત કરવાના પગલાં જણાવું?"
            )
        return (
            f"નમસ્તે, હું રૂકો સાઇબર શીલ્ડ સુરક્ષા સહાયક છું. તમારા ઇમેઇલ {email} માટેના સ્કેનમાં {total_breaches} "
            "લીક મળ્યા છે. તમારા એકાઉન્ટ્સને સુરક્ષિત કરવામાં હું તમને કેવી રીતે મદદ કરી શકું?"
        )

    # Default English
    if financial_exposed:
        return (
            f"Hello, this is Ruko Cyber Shield. I am calling regarding your breach scan for {email}. "
            f"We found {total_breaches} incidents, including potential financial exposure. "
            "Would you like me to walk you through securing your accounts right away?"
        )
    return (
        f"Hello, this is Ruko Cyber Shield. I am calling regarding your recent breach scan for {email}. "
        f"We identified {total_breaches} past security incidents. How can I help you secure your accounts today?"
    )


def get_agent_variable_values(
    email: str,
    total_breaches: int,
    high_risk_count: int,
    financial_exposed: bool,
    breach_names: List[str],
    exposure_categories: List[str],
) -> Dict[str, Any]:
    """Map scan results into structured variable values for Vapi template substitution."""
    if total_breaches == 0:
        services_str = "None (No breaches detected)"
        cats_str = "None (Clean account)"
    else:
        services_str = ", ".join(breach_names[:6]) if breach_names else "Multiple platforms"
        cats_str = ", ".join(sorted(list(set(exposure_categories)))) if exposure_categories else "General account info"

    return {
        "user_email": email,
        "total_breaches": str(total_breaches),
        "high_risk_count": str(high_risk_count),
        "financial_exposed": "YES (Critical)" if financial_exposed else "NO",
        "exposed_services": services_str,
        "leaked_categories": cats_str,
    }
