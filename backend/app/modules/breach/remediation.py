"""Safe, actionable remediation guidance tailored to exposure categories and risk level."""

from typing import List


def get_remediation_notes(risk_level: str, financial_exposure: bool, categories: List[str]) -> List[str]:
    """Generate safe, conservative remediation steps without external links."""
    notes: List[str] = []
    norm_cats = [c.strip().lower() for c in categories]

    # Financial Exposure Actions
    if financial_exposure:
        notes.append("Contact your bank directly through its official mobile application or customer care number to monitor accounts.")
        notes.append("Consider requesting a replacement for any exposed debit/credit cards.")
        notes.append("Enable daily transaction limits and SMS/email alerts on your banking channels.")

    # Password / Credential Actions
    has_passwords = any("password" in c or "auth" in c for c in norm_cats)
    if has_passwords or risk_level == "HIGH":
        notes.append("Change your password immediately on the affected service and any other accounts where you reused it.")
        notes.append("Enable Multi-Factor Authentication (MFA) using an authenticator app wherever available.")

    # Contact / Phone / SIM-swap Actions
    has_phone = any("phone" in c or "mobile" in c for c in norm_cats)
    if has_phone:
        notes.append("Be alert against unsolicited verification SMS messages, phishing attempts, or unexpected loss of cellular signal (potential SIM-swap).")

    # General / Profile Actions
    if risk_level == "MEDIUM" and not notes:
        notes.append("Review your recent account login history and connected third-party applications.")
        notes.append("Update security questions and avoid using easily guessable personal details.")

    if not notes:
        notes.append("Monitor your account for unusual activity.")
        notes.append("Ensure you use strong, unique passwords for every online service.")

    return notes
