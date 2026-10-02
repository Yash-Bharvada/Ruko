"""Tests for M0: scaffold, config, errors, logging, and health endpoint."""

import io
import json
import logging
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import (
    AppException,
    PayloadTooLargeError,
    build_error_response,
)
from app.core.logging import (
    FORBIDDEN_BODY_FIELDS,
    JsonFormatter,
    PrivacyFilter,
    log_request,
    logger,
)
from app.core.schemas import CheckRequest, CheckResult, HealthResponse
from app.main import app, create_app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a test client for the FastAPI app."""
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Acceptance check: GET /health returns 200 with ok status and module states."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "modules" in data

    # All modules must be registered (disabled in M0)
    expected_modules = [
        "model_adapter",
        "rules",
        "registry",
        "extractor",
        "ingest",
        "verdict",
        "voice",
        "pause",
        "guardrails",
    ]
    for module_name in expected_modules:
        assert module_name in data["modules"]
        assert data["modules"][module_name] in ("active", "degraded", "disabled")

    # Verify X-Request-ID and timing headers are present
    assert "x-request-id" in response.headers
    assert "x-response-time-ms" in response.headers


def test_unknown_route_returns_uniform_error(client: TestClient) -> None:
    """Acceptance check: unknown route returns uniform JSON error."""
    response = client.get("/v1/non_existent_route")
    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert "message" in data["error"]
    assert "request_id" in data["error"]
    assert data["error"]["request_id"] != ""


def test_oversized_body_via_content_length_header(client: TestClient) -> None:
    """Acceptance check: oversized request body returns uniform error JSON (413)."""
    # Exceed maximum allowed MB size (e.g. 50 MB)
    large_size = 50 * 1024 * 1024
    response = client.post(
        "/health",
        headers={"Content-Length": str(large_size)},
        content=b"test",
    )
    assert response.status_code == 413

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "payload_too_large"
    assert "message" in data["error"]
    assert "request_id" in data["error"]


def test_oversized_text_validation_error() -> None:
    """Acceptance check: text exceeding MAX_TEXT_CHARS fails validation with payload_too_large."""
    test_app = create_app()

    @test_app.post("/test-check")
    async def check_endpoint(req: CheckRequest) -> dict:
        return {"status": "ok"}

    with TestClient(test_app) as custom_client:
        # 4001 characters should trigger payload_too_large
        oversized_text = "A" * 4001
        response = custom_client.post("/test-check", json={"text": oversized_text})
        assert response.status_code == 413

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "payload_too_large"
        assert "request_id" in data["error"]


def test_logging_request_never_emits_body_text() -> None:
    """Acceptance check: logging a request never emits the body text or PII."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(PrivacyFilter())

    test_logger = logging.getLogger("test_ruko_audit")
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(handler)

    # 1. Verify standard log_request fields
    secret_body_text = "SECRET_INVESTMENT_SCAM_BODY_PAY_ME_RS_50000"
    log_request(
        request_id="req-test-12345",
        endpoint="/v1/check",
        verdict="strong_red_flags",
        language="gu",
        latency_ms=35.42,
        degraded=["model_unavailable"],
    )

    # 2. Attempt to log a record with forbidden request_body/body extra
    test_logger.info("Attempted audit", extra={"body": secret_body_text})
    test_logger.info("Another attempt with text", extra={"request_body": secret_body_text})

    # The filter must drop any record containing forbidden body fields
    output = stream.getvalue()
    assert secret_body_text not in output, "CRITICAL: Request body was leaked into logs!"


def test_cors_settings() -> None:
    """Verify CORS configuration parsing."""
    settings = Settings(CORS_ORIGINS="http://localhost:3000, http://localhost:5173")
    origins = settings.get_cors_origins()
    assert origins == ["http://localhost:3000", "http://localhost:5173"]

    wildcard_settings = Settings(CORS_ORIGINS="*")
    assert wildcard_settings.get_cors_origins() == ["*"]


def test_custom_app_exception() -> None:
    """Verify AppException and build_error_response consistency."""
    err_resp = build_error_response(400, "bad_input", "Something went wrong", "req-999")
    assert err_resp.status_code == 400
    body = json.loads(err_resp.body)
    assert body["error"]["code"] == "bad_input"
    assert body["error"]["message"] == "Something went wrong"
    assert body["error"]["request_id"] == "req-999"
