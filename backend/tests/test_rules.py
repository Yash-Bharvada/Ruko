"""Tests for Module M2: Deterministic Rule Engine."""

import random
import string
import pytest
from app.modules.rules.engine import evaluate_rules, extract_basic_claims, get_rule_engine
from app.modules.rules.loader import load_rules


def test_rule_loader_loads_successfully() -> None:
    """Acceptance check: rules load and compile with zero errors."""
    rules = load_rules()
    assert len(rules) >= 12
    codes = {r.code for r in rules}
    expected_codes = {
        "guaranteed_returns",
        "unrealistic_return_claim",
        "upfront_payment_request",
        "personal_upi_payment",
        "otp_pin_request",
        "apk_or_remote_app",
        "authority_impersonation",
        "vip_or_tip_group_invite",
        "urgency_pressure",
        "secrecy_request",
        "suspicious_link",
        "unverified_registration_claim",
    }
    for ec in expected_codes:
        assert ec in codes, f"Missing required rule code: {ec}"


def test_english_investment_scam_message() -> None:
    """Acceptance check: English scam message triggers all 5 expected red flags."""
    text = "Guaranteed 30% monthly returns, SEBI registered, pay Rs 5000 registration fee to vip55@ybl"
    flags = evaluate_rules(text)
    codes = {f.code for f in flags}

    assert "guaranteed_returns" in codes
    assert "unrealistic_return_claim" in codes
    assert "upfront_payment_request" in codes
    assert "personal_upi_payment" in codes
    assert "unverified_registration_claim" in codes

    # Verify each flag's evidence is a real substring of the input text
    for f in flags:
        assert f.evidence in text
        assert len(f.evidence) <= 80


def test_gujarati_script_investment_scam() -> None:
    """Acceptance check: Gujarati script message triggers guaranteed_returns and suspicious_link."""
    text = "100% ગેરંટીડ રિટર્ન, કોઈ જોખમ નહીં. ફ્રી વોટ્સએપ ગ્રુપમાં જોડાવા ક્લિક કરો: https://x.xyz/ab"
    flags = evaluate_rules(text)
    codes = {f.code for f in flags}

    assert "guaranteed_returns" in codes
    assert "suspicious_link" in codes

    for f in flags:
        assert f.evidence in text
        assert len(f.evidence) <= 80


def test_roman_gujarati_investment_scam() -> None:
    """Acceptance check: Roman Gujarati message triggers guaranteed_returns and urgency_pressure."""
    text = "Roj 5% nafo, koi jokham nathi, aaje j jodavo"
    flags = evaluate_rules(text)
    codes = {f.code for f in flags}

    assert "guaranteed_returns" in codes
    assert "urgency_pressure" in codes

    for f in flags:
        assert f.evidence in text
        assert len(f.evidence) <= 80


def test_genuine_bank_sms() -> None:
    """Acceptance check: Genuine transactional bank SMS triggers NO red flags."""
    text = "Rs 5,000 credited to your account XX1234. Ref 123456."
    flags = evaluate_rules(text)
    assert len(flags) == 0, f"Expected 0 flags for legitimate bank SMS, got: {[f.code for f in flags]}"


def test_genuine_education_text_with_negation() -> None:
    """Acceptance check: Educational text negates guarantee and must NOT trigger guaranteed_returns."""
    text = "Returns are never guaranteed. Check that the adviser is SEBI registered."
    flags = evaluate_rules(text)
    codes = {f.code for f in flags}

    # Must NOT raise guaranteed_returns
    assert "guaranteed_returns" not in codes
    # At most unverified_registration_claim
    for code in codes:
        assert code == "unverified_registration_claim"

    for f in flags:
        assert f.evidence in text
        assert len(f.evidence) <= 80


def test_evidence_is_strict_substring() -> None:
    """Verify that evidence for all triggered flags is strictly an exact substring of the original input."""
    messages = [
        "Special offer today only! Share OTP 123456 to receive bonus.",
        "Install anydesk app from link to resolve KYC immediately.",
        "Digital arrest warrant issued by CBI investigation team. Don't tell anyone.",
        "Join VIP group on telegram: https://t.me/super_stock_tips",
    ]
    for msg in messages:
        flags = evaluate_rules(msg)
        assert len(flags) > 0
        for f in flags:
            assert f.evidence in msg
            assert len(f.evidence) <= 80


def test_fuzz_never_raises() -> None:
    """Acceptance check: Fuzz test with 200 random/odd strings never raises an exception."""
    random.seed(42)
    engine = get_rule_engine()

    odd_samples = [
        "",
        "   ",
        None,
        "\n\t\r",
        "🚀🔥💎💰📈" * 20,
        "A" * 15000,  # 15k characters
        "null",
        "undefined",
        "{}[]()<>!@#$%^&*()_+",
        "1234567890",
        "ગેરંટી" * 100,
        "गारंटी" * 100,
    ]

    for sample in odd_samples:
        flags = engine.evaluate(sample)  # type: ignore
        assert isinstance(flags, list)

    # 200 random character strings
    for _ in range(200):
        length = random.randint(0, 500)
        random_chars = "".join(
            random.choice(string.printable + "ગેરંટીનફોજોખમगारंटीमुनाफ़ा🚀💰")
            for _ in range(length)
        )
        flags = engine.evaluate(random_chars)
        assert isinstance(flags, list)
        for f in flags:
            assert f.evidence in random_chars


def test_extract_basic_claims() -> None:
    """Acceptance check: Basic claim extraction correctly parses structured facts."""
    sample = (
        "Adviser INA000012345 promises 25.5% returns. Pay to trader55@oksbi or call +91 9876543210. "
        "Visit https://secure-investment.xyz/join"
    )
    claims = extract_basic_claims(sample)

    assert "INA000012345" in claims["registration_numbers"]
    assert "trader55@oksbi" in claims["upi_ids"]
    assert any("9876543210" in p for p in claims["phones"])
    assert "https://secure-investment.xyz/join" in claims["urls"]
    assert 25.5 in claims["percentages"]


def test_extract_basic_claims_none_or_empty() -> None:
    """Test claims extraction handles None and empty input safely."""
    for empty in [None, "", "   "]:
        claims = extract_basic_claims(empty)
        assert claims["registration_numbers"] == []
        assert claims["upi_ids"] == []
        assert claims["phones"] == []
        assert claims["urls"] == []
        assert claims["percentages"] == []
