"""Tests for Module M8: Pause Layer (Decision Card, .ics Calendar, Loss Arithmetic, Share Link, Recovery Checklist)."""

import urllib.parse
from datetime import datetime, timezone
import pytest
import icalendar
from fastapi.testclient import TestClient

from app.main import app
from app.modules.pause.ics import generate_cooling_off_ics
from app.modules.pause.plan import PausePlan, build_plan
from app.modules.pause.resources import get_already_paid_resources
from app.modules.pause.share import build_whatsapp_share_link
from app.modules.verdict.engine import assert_no_advice


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --- 1. Three Decision Questions in Multilingual Parity ---

def test_three_decision_questions_in_all_languages() -> None:
    """Acceptance check: Exactly 3 non-empty decision questions in each of en, hi, gu."""
    for lang in ("en", "hi", "gu"):
        plan = build_plan(verdict="strong_red_flags", lang=lang)
        assert len(plan.decision_questions) == 3
        for q in plan.decision_questions:
            assert len(q.strip()) > 5
            # Scan with assert_no_advice
            assert assert_no_advice(q) == q


# --- 2. Loss Arithmetic ---

def test_loss_arithmetic_calculation_and_null_behavior() -> None:
    """Acceptance check: amount 50000 / expenses 25000 -> 2.0 months; one number missing -> null."""
    # Complete: 50,000 / 25,000 = 2.0
    plan_full = build_plan(
        verdict="strong_red_flags",
        lang="en",
        amount=50000.0,
        monthly_expenses=25000.0,
    )
    assert plan_full.loss_arithmetic is not None
    assert plan_full.loss_arithmetic.amount == 50000.0
    assert plan_full.loss_arithmetic.months_of_expenses == 2.0
    assert "about 2.0 months" in plan_full.loss_arithmetic.sentence

    # Multilingual sentence check in Hindi
    plan_hi = build_plan(
        verdict="strong_red_flags",
        lang="hi",
        amount=50000.0,
        monthly_expenses=25000.0,
    )
    assert plan_hi.loss_arithmetic is not None
    assert "2.0 महीनों" in plan_hi.loss_arithmetic.sentence

    # One number missing -> loss_arithmetic is null
    plan_no_exp = build_plan(verdict="strong_red_flags", lang="en", amount=50000.0, monthly_expenses=None)
    assert plan_no_exp.loss_arithmetic is None

    plan_no_amt = build_plan(verdict="strong_red_flags", lang="en", amount=None, monthly_expenses=25000.0)
    assert plan_no_amt.loss_arithmetic is None

    plan_both_none = build_plan(verdict="strong_red_flags", lang="en", amount=None, monthly_expenses=None)
    assert plan_both_none.loss_arithmetic is None

    # Zero or negative amount -> null
    plan_zero = build_plan(verdict="strong_red_flags", lang="en", amount=0, monthly_expenses=25000.0)
    assert plan_zero.loss_arithmetic is None


# --- 3. RFC 5545 .ics Calendar Generator ---

def test_cooling_off_ics_parses_with_icalendar_and_alarm_is_24h() -> None:
    """Acceptance check: The .ics string parses with icalendar library, alarm is ~24h out, no user text."""
    ics_text, data_uri = generate_cooling_off_ics(lang="en", delay_hours=24)

    # 1. Parse using standard icalendar library
    cal = icalendar.Calendar.from_ical(ics_text)
    assert cal.name == "VCALENDAR"
    assert cal.get("prodid") is not None

    events = [c for c in cal.walk() if c.name == "VEVENT"]
    assert len(events) == 1
    event = events[0]

    # Verify event timing is 24h in future (+- 2 minutes margin)
    now_utc = datetime.now(timezone.utc)
    event_start = event.get("dtstart").dt
    diff_hours = (event_start - now_utc).total_seconds() / 3600.0
    assert 23.9 <= diff_hours <= 24.1

    # Verify VALARM
    alarms = [c for c in event.walk() if c.name == "VALARM"]
    assert len(alarms) >= 1
    assert alarms[0].get("action") == "DISPLAY"

    # Verify Data URI format
    assert data_uri.startswith("data:text/calendar;charset=utf-8,")

    # Verify no advice strings
    assert assert_no_advice(ics_text) == ics_text


# --- 4. WhatsApp Share Link ---

def test_whatsapp_share_link_structure_and_no_user_text() -> None:
    """Acceptance check: Share link decodes to templated summary and never contains user message text."""
    share_url, share_text = build_whatsapp_share_link(verdict="strong_red_flags", lang="en")

    assert share_url.startswith("https://wa.me/?text=")
    # Extract query param text
    parsed = urllib.parse.urlparse(share_url)
    params = urllib.parse.parse_qs(parsed.query)
    decoded_text = params["text"][0]

    assert decoded_text == share_text
    assert "I checked an investment message with Ruko: Strong red flags were detected" in decoded_text
    assert "Please talk to me before I pay anyone." in decoded_text

    # Multilingual: Gujarati
    _, share_text_gu = build_whatsapp_share_link(verdict="strong_red_flags", lang="gu")
    assert "રૂકો (Ruko) એપ પર એક રોકાણ સંદેશની તપાસ કરી" in share_text_gu


# --- 5. Recovery Checklist Resources ---

def test_already_paid_recovery_resources() -> None:
    """Acceptance check: Official recovery checklist contains 1930, cybercrime.gov.in, and SEBI SCORES."""
    res_en = get_already_paid_resources("en")
    assert res_en["language"] == "en"
    checklist = res_en["checklist"]
    assert len(checklist) >= 4

    # Check key helplines
    contacts = [item["contact"] for item in checklist]
    assert any("1930" in c for c in contacts)
    assert any("cybercrime.gov.in" in c for c in contacts)
    assert any("scores.sebi.gov.in" in c for c in contacts)

    # All items have verify: True
    for item in checklist:
        assert item["verify"] is True
        assert item["description"] != ""

    # Hindi checklist
    res_hi = get_already_paid_resources("hi")
    assert res_hi["language"] == "hi"
    assert len(res_hi["checklist"]) >= 4


# --- 6. Safety Sweep (assert_no_advice) ---

def test_pause_layer_outputs_zero_advice_hits() -> None:
    """Acceptance check: Scan all pause outputs with assert_no_advice: zero forbidden advice hits."""
    for lang in ("en", "hi", "gu"):
        for verdict in ("strong_red_flags", "cannot_verify", "no_red_flags_found", "out_of_scope"):
            plan = build_plan(verdict=verdict, lang=lang, amount=100000, monthly_expenses=50000)
            dumped = plan.model_dump()
            # Ensure scanning does not alter any string (assert_no_advice returns identical data)
            scanned = assert_no_advice(dumped)
            assert dumped == scanned


# --- 7. HTTP API Route Endpoints ---

def test_api_pause_plan_endpoint(client: TestClient) -> None:
    """Acceptance check: POST /v1/pause/plan returns 200 with complete PausePlan."""
    payload = {
        "verdict": "strong_red_flags",
        "language": "en",
        "amount": 50000,
        "monthly_expenses": 25000,
    }
    response = client.post("/v1/pause/plan", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["decision_questions"]) == 3
    assert data["cooling_off_hours"] == 24
    assert data["loss_arithmetic"]["months_of_expenses"] == 2.0
    assert "data:text/calendar" in data["calendar_data_uri"]
    assert "https://wa.me/" in data["share_link"]


def test_api_recovery_resources_endpoint(client: TestClient) -> None:
    """Acceptance check: GET /v1/resources/already-paid returns 200 with localized checklist."""
    response = client.get("/v1/resources/already-paid?lang=gu")
    assert response.status_code == 200

    data = response.json()
    assert data["language"] == "gu"
    assert len(data["checklist"]) >= 4
    assert any("1930" in item["contact"] for item in data["checklist"])
