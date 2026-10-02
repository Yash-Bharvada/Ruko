"""Uniform error handling for Ruko API."""

import uuid
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """Base application exception with status code and error code."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "bad_request",
        message: str = "A request error occurred",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class PayloadTooLargeError(AppException):
    """Raised when the request payload exceeds configured limits."""

    def __init__(self, message: str = "Request payload exceeds allowed limit") -> None:
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="payload_too_large",
            message=message,
        )


class NotFoundError(AppException):
    """Raised when an endpoint or resource is not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            message=message,
        )


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later.") -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="rate_limit_exceeded",
            message=message,
        )


def _get_request_id(request: Request) -> str:
    """Retrieve or generate request_id safely from request state or headers."""
    if hasattr(request, "state") and getattr(request.state, "request_id", None):
        return str(request.state.request_id)
    header_id = request.headers.get("x-request-id")
    if header_id:
        return header_id
    return str(uuid.uuid4())


def build_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
) -> JSONResponse:
    """Build uniform error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    req_id = _get_request_id(request)
    return build_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        request_id=req_id,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic request validation errors."""
    req_id = _get_request_id(request)
    # Check if this was a max_length violation
    errors = exc.errors()
    code = "validation_error"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    messages = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "invalid value")
        err_type = err.get("type", "")
        if "too_long" in err_type or "string_too_long" in err_type:
            code = "payload_too_large"
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        messages.append(f"{loc}: {msg}" if loc else msg)

    summary_msg = "; ".join(messages) if messages else "Invalid request data"
    return build_error_response(
        status_code=status_code,
        code=code,
        message=summary_msg,
        request_id=req_id,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle Starlette / FastAPI HTTP exceptions (including 404, 405)."""
    req_id = _get_request_id(request)
    code_map = {
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "payload_too_large",
        status.HTTP_429_TOO_MANY_REQUESTS: "rate_limit_exceeded",
    }
    code = code_map.get(exc.status_code, f"http_{exc.status_code}")
    message = str(exc.detail) if exc.detail else "HTTP error"
    return build_error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        request_id=req_id,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for unexpected errors. Never exposes internal stack trace."""
    req_id = _get_request_id(request)
    return build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_server_error",
        message="An unexpected internal server error occurred",
        request_id=req_id,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all uniform error handlers on the FastAPI application."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
