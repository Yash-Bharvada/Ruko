"""Hardening, evaluation, and demo reliability acceptance tests for Module M10."""

import json
from pathlib import Path
import pytest
from app.api.routes_check import run_check
from app.core.config import Settings
from scripts.demo_smoke import load_demo_cases, run_smoke_test
from scripts.eval_pipeline import evaluate_suite


def test_demo_cases_schema_and_completeness() -> None:
    """Acceptance check: Verify data/demo_cases.json contains 10 valid, multi-lingual scenarios."""
    cases = load_demo_cases()
    assert len(cases) == 10, f"Expected 10 demo cases, got {len(cases)}"

    languages = set()
    verdicts = set()

    for c in cases:
        assert "id" in c and isinstance(c["id"], str)
        assert "title" in c and isinstance(c["title"], str)
        assert "category" in c and isinstance(c["category"], str)
        assert "language" in c and c["language"] in ("gu", "hi", "en")
        assert "text" in c and len(c["text"].strip()) > 10
        assert "expected_verdict" in c and c["expected_verdict"] in (
            "strong_red_flags",
            "cannot_verify",
            "no_red_flags_found",
            "out_of_scope",
        )
        languages.add(c["language"])
        verdicts.add(c["expected_verdict"])

    # Must cover Gujarati, Hindi, English
    assert "gu" in languages
    assert "hi" in languages
    assert "en" in languages

    # Must cover both scam verdicts and out_of_scope
    assert "strong_red_flags" in verdicts
    assert "out_of_scope" in verdicts


@pytest.mark.asyncio
async def test_all_10_demo_cases_pass_pipeline() -> None:
    """Acceptance check: Verify all 10 demo cases execute through run_check with expected verdicts."""
    cases = load_demo_cases()
    settings = Settings()

    for case in cases:
        result = await run_check(
            text=case["text"],
            language_hint=case.get("language"),
            amount=case.get("amount"),
            settings=settings,
        )
        assert (
            result.verdict == case["expected_verdict"]
        ), f"Case '{case['id']}' failed: expected {case['expected_verdict']}, got {result.verdict}"
        # Advice cases must have 0.0 score and zero reasons
        if case["expected_verdict"] == "out_of_scope":
            assert result.score == 0.0
            assert len(result.reasons) == 0


@pytest.mark.asyncio
async def test_demo_smoke_script_execution() -> None:
    """Acceptance check: Verify demo_smoke.py executes without error and reports 10/10 success."""
    success = await run_smoke_test()
    assert success is True, "Demo smoke test reported failure on demo cases"


@pytest.mark.asyncio
async def test_evaluation_pipeline_metrics_and_report() -> None:
    """Acceptance check: Verify eval_pipeline.py generates report and meets all quality thresholds."""
    report = await evaluate_suite()

    metrics = report["metrics"]
    assert metrics["scam_recall"] >= 0.90, f"Scam recall {metrics['scam_recall']} is below 90%"
    assert metrics["false_positive_rate"] == 0.0, "Benign false positive rate must be 0.0%"
    assert metrics["advice_redirection_accuracy"] == 1.0, "Advice interception accuracy must be 100%"

    # Check generated markdown report
    report_file = Path(__file__).resolve().parent.parent / "reports" / "eval.md"
    assert report_file.is_file(), f"Evaluation report not found at {report_file}"
    content = report_file.read_text(encoding="utf-8")
    assert "Ruko Backend Evaluation & Benchmark Report" in content
    assert "Executive Summary" in content


def test_dockerfile_security_and_standards() -> None:
    """Acceptance check: Verify Dockerfile enforces non-root execution and healthcheck."""
    dockerfile_path = Path(__file__).resolve().parent.parent / "Dockerfile"
    assert dockerfile_path.is_file(), "Dockerfile missing from backend directory"

    content = dockerfile_path.read_text(encoding="utf-8")

    # Non-root user check
    assert "useradd" in content or "adduser" in content
    assert "USER appuser" in content

    # Healthcheck check
    assert "HEALTHCHECK" in content
    assert "/health" in content

    # Port check
    assert "EXPOSE 8000" in content


def test_locked_dependencies_pinned() -> None:
    """Acceptance check: Verify all dependencies in requirements.txt are strictly pinned."""
    req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
    assert req_path.is_file(), "requirements.txt missing"

    lines = [
        line.strip()
        for line in req_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    for line in lines:
        assert "==" in line, f"Dependency '{line}' is not pinned with '=='"

    dep_names = [line.split("==")[0].lower() for line in lines]
    assert "fastapi" in dep_names
    assert "scikit-learn" in dep_names
    assert "rapidfuzz" in dep_names
    assert "icalendar" in dep_names
