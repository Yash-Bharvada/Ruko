"""Structured JSON logging with privacy-by-design privacy filters."""

import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional


FORBIDDEN_BODY_FIELDS = {
    "body",
    "request_body",
    "text",
    "image",
    "audio",
    "file",
    "prompt",
    "message_text",
    "raw_text",
    "user_input",
    "content",
}


class PrivacyFilter(logging.Filter):
    """Logging filter that drops any record attempting to log request body or sensitive content."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Check record message for forbidden indicators
        msg_lower = str(record.msg).lower()
        if "request_body" in msg_lower or "body=" in msg_lower:
            return False

        # Check record args
        if isinstance(record.args, dict):
            for key in record.args.keys():
                if str(key).lower() in FORBIDDEN_BODY_FIELDS:
                    return False
        elif isinstance(record.args, (list, tuple)):
            for arg in record.args:
                if isinstance(arg, dict):
                    for key in arg.keys():
                        if str(key).lower() in FORBIDDEN_BODY_FIELDS:
                            return False

        # Check extra attributes on record
        for key in list(record.__dict__.keys()):
            if key.lower() in FORBIDDEN_BODY_FIELDS:
                # Remove the attribute and drop or sanitize
                delattr(record, key)
                return False

        return True


class JsonFormatter(logging.Formatter):
    """Format log records as single-line structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured audit fields if present
        for field in ("request_id", "endpoint", "verdict", "language", "latency_ms", "degraded", "event"):
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured JSON logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(PrivacyFilter())
    root_logger.addHandler(handler)

    app_logger = logging.getLogger("ruko")
    app_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return app_logger


logger = setup_logging()


def log_request(
    request_id: str,
    endpoint: str,
    verdict: str,
    language: str,
    latency_ms: float,
    degraded: Optional[List[str]] = None,
) -> None:
    """Log request metadata strictly complying with Privacy by Design.

    Logs ONLY: request_id, endpoint, verdict, language, latency_ms, degraded flags.
    NEVER logs request bodies, user message content, or any PII.
    """
    if degraded is None:
        degraded = []

    extra = {
        "event": "request_audit",
        "request_id": request_id,
        "endpoint": endpoint,
        "verdict": verdict,
        "language": language,
        "latency_ms": round(latency_ms, 2),
        "degraded": degraded,
    }

    logger.info(
        "Request processed: %s %s verdict=%s language=%s latency_ms=%.2f degraded=%s",
        endpoint,
        request_id,
        verdict,
        language,
        latency_ms,
        degraded,
        extra=extra,
    )
