"""Tests for Module M1: Model slot and adapter."""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.modules.model_adapter.adapter import RealModelScorer
from app.modules.model_adapter.contract import ModelOutput, ScamScorer
from app.modules.model_adapter.dummy import DummyScorer
from app.modules.model_adapter.loader import load_model
from app.main import app, create_app


# Helper mock classes simulating teammate model package
class MockRukoModel:
    """Mock RukoModel simulating expected predict.RukoModel behavior."""

    def __init__(self, path: str | None = None) -> None:
        self.path = path

    def check(self, text: str, top: int = 5) -> Dict[str, Any]:
        text_lower = text.lower()
        if "guaranteed" in text_lower or "vip" in text_lower or "returns" in text_lower:
            return {
                "verdict": "FLAGGED_AS_SCAM",  # This string must be ignored by adapter
                "score": 0.88,
                "words_that_raised_risk": ["guaranteed", "returns", "vip"],
                "words_that_lowered_risk": [],
                "note": "High risk pattern detected",
            }
        elif "otp" in text_lower or "credited" in text_lower:
            return {
                "verdict": "LEGITIMATE",
                "score": 0.05,
                "words_that_raised_risk": [],
                "words_that_lowered_risk": ["otp", "credited"],
                "note": "Standard transactional pattern",
            }
        return {
            "verdict": "UNCERTAIN",
            "score": 0.45,
            "words_that_raised_risk": [],
            "words_that_lowered_risk": [],
            "note": "Neutral",
        }


class SlowMockRukoModel:
    """Mock model that hangs to trigger timeout."""

    def __init__(self, delay: float = 3.0) -> None:
        self.delay = delay

    def check(self, text: str, top: int = 5) -> Dict[str, Any]:
        time.sleep(self.delay)
        return {"score": 0.5}


class ErrorMockRukoModel:
    """Mock model that raises an internal exception."""

    def check(self, text: str, top: int = 5) -> Dict[str, Any]:
        raise ValueError("Simulated model internal compute error")


# --- Test Cases ---

def test_dummy_scorer() -> None:
    """Acceptance check: DummyScorer returns available=False and score=None (never fakes score)."""
    dummy = DummyScorer()
    assert dummy.is_available is False

    output = asyncio.run(dummy.score("Guaranteed returns"))
    assert output.available is False
    assert output.score is None
    assert output.top_words == []
    assert output.calming_words == []
    assert output.error is None


def test_empty_or_whitespace_text() -> None:
    """Acceptance check: Empty or whitespace text returns available=True, score=None."""
    scorer = RealModelScorer(MockRukoModel())

    for empty_input in ["", "   ", "\n\t", " \n "]:
        output = asyncio.run(scorer.score(empty_input))
        assert output.available is True
        assert output.score is None
        assert output.top_words == []
        assert output.calming_words == []
        assert output.error is None


def test_real_model_scorer_predictions() -> None:
    """Acceptance check: RealModelScorer consumes score and word lists, ignoring internal verdict."""
    scorer = RealModelScorer(MockRukoModel())

    # High risk input
    scam_text = "Guaranteed 30% monthly returns, join VIP group, send Rs 5000 to trade55@ybl"
    output = asyncio.run(scorer.score(scam_text))
    assert output.available is True
    assert output.score is not None
    assert output.score > 0.80
    assert "guaranteed" in output.top_words
    assert output.error is None

    # Low risk input
    legit_text = "Your OTP is 482913. Do not share it with anyone."
    output_legit = asyncio.run(scorer.score(legit_text))
    assert output_legit.available is True
    assert output_legit.score is not None
    assert output_legit.score < 0.20
    assert "otp" in output_legit.calming_words
    assert output_legit.error is None


def test_model_timeout_path() -> None:
    """Acceptance check: Slow model invocation triggers timeout after 2.0s without crashing."""
    scorer = RealModelScorer(SlowMockRukoModel(delay=2.5), timeout_seconds=0.3)
    output = asyncio.run(scorer.score("Any text"))

    assert output.available is False
    assert output.score is None
    assert output.error == "model_timeout"


def test_model_exception_graceful_handling() -> None:
    """Acceptance check: Exceptions inside model.check are caught and returned safely."""
    scorer = RealModelScorer(ErrorMockRukoModel(), timeout_seconds=1.0)
    output = asyncio.run(scorer.score("Any text"))

    assert output.available is False
    assert output.score is None
    assert "Simulated model internal compute error" in str(output.error)


def test_loader_missing_directory(tmp_path: Path) -> None:
    """Acceptance check: Missing model directory falls back to DummyScorer with model_unavailable."""
    fake_path = tmp_path / "non_existent_model_dir"
    settings = Settings(MODEL_DIR=str(fake_path), MODEL_REQUIRED=False)

    scorer, degraded = load_model(settings)
    assert isinstance(scorer, DummyScorer)
    assert "model_unavailable" in degraded


def test_loader_missing_required_files(tmp_path: Path) -> None:
    """Acceptance check: Missing common.py or predict.py or model.joblib falls back gracefully."""
    model_dir = tmp_path / "partial_model"
    model_dir.mkdir()

    # Create only model.joblib (missing common.py and predict.py)
    (model_dir / "model.joblib").write_text("stub", encoding="utf-8")
    settings = Settings(MODEL_DIR=str(model_dir), MODEL_REQUIRED=False)

    scorer, degraded = load_model(settings)
    assert isinstance(scorer, DummyScorer)
    assert "model_unavailable" in degraded

    # Add predict.py but still missing common.py
    (model_dir / "predict.py").write_text("class RukoModel: pass", encoding="utf-8")
    scorer2, degraded2 = load_model(settings)
    assert isinstance(scorer2, DummyScorer)
    assert "model_unavailable" in degraded2


def test_loader_model_required_raises(tmp_path: Path) -> None:
    """Acceptance check: If MODEL_REQUIRED=True and files are missing, loader raises RuntimeError."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    settings = Settings(MODEL_DIR=str(empty_dir), MODEL_REQUIRED=True)

    with pytest.raises(RuntimeError) as exc_info:
        load_model(settings)
    assert "missing required files" in str(exc_info.value)


def test_loader_version_mismatch_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """Acceptance check: sklearn version mismatch logs WARNING and adds model_version_mismatch."""
    model_dir = tmp_path / "version_test_model"
    model_dir.mkdir()

    (model_dir / "model.joblib").write_text("stub", encoding="utf-8")
    (model_dir / "common.py").write_text("# common.py\ndef preprocess(): pass\n", encoding="utf-8")
    (model_dir / "predict.py").write_text(
        "class RukoModel:\n"
        "    def __init__(self, path=None):\n"
        "        pass\n"
        "    def check(self, text, top=5):\n"
        "        return {'score': 0.5, 'words_that_raised_risk': [], 'words_that_lowered_risk': []}\n",
        encoding="utf-8",
    )
    # Write model_card.json with a deliberately mismatched version
    (model_dir / "model_card.json").write_text(
        json.dumps({"sklearn_version": "0.19.0", "trained_on": "2020-01-01"}),
        encoding="utf-8",
    )

    settings = Settings(MODEL_DIR=str(model_dir), MODEL_REQUIRED=False)

    with caplog.at_level(logging.WARNING):
        scorer, degraded = load_model(settings)

    assert "model_version_mismatch" in degraded
    assert any("Scikit-learn version mismatch" in rec.message for rec in caplog.records)


def test_health_with_no_model_files() -> None:
    """Acceptance check: With NO files in model_store, /health reports degraded model status."""
    # Create test app with empty model_store
    settings = Settings(MODEL_DIR="model_store", MODEL_REQUIRED=False)
    test_app = create_app(settings)

    with TestClient(test_app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["modules"]["model_adapter"] == "degraded"
        assert data["model"] == "degraded"
