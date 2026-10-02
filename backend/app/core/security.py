"""Security, rate limiting, and security header utilities."""

import time
from collections import defaultdict
from typing import Dict, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import get_settings
from app.core.errors import RateLimitError, build_error_response


class InMemoryRateLimiter:
    """Simple in-memory sliding-window rate limiter per client IP."""

    def __init__(self, limit_per_minute: int = 30) -> None:
        self.limit = limit_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        # Filter timestamps within current 60s window
        timestamps = [t for t in self.requests[client_ip] if t > window_start]
        self.requests[client_ip] = timestamps

        if len(timestamps) >= self.limit:
            return False

        self.requests[client_ip].append(now)
        return True

    def reset(self) -> None:
        self.requests.clear()


# Default singleton rate limiter
_default_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get the global in-memory rate limiter singleton."""
    global _default_limiter
    return _default_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces rate limiting across endpoints, returning uniform 429 JSON on violation."""

    def __init__(self, app: object, limiter: Optional[InMemoryRateLimiter] = None) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        settings = get_settings()
        self.limiter = limiter or get_rate_limiter()
        self.limiter.limit = getattr(settings, "RATE_LIMIT_PER_MIN", 30)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Exclude liveness and documentation endpoints from rate limiting
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client_ip = "127.0.0.1"
        if request.client and request.client.host:
            client_ip = request.client.host
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        if not self.limiter.is_allowed(client_ip):
            req_id = getattr(request.state, "request_id", "") or request.headers.get("x-request-id", "")
            return build_error_response(
                status_code=429,
                code="rate_limit_exceeded",
                message=f"Rate limit of {self.limiter.limit} requests per minute exceeded. Please try again later.",
                request_id=req_id,
            )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response
