"""FastAPI application factory, middleware, and core endpoints."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.config import Settings, get_settings
from app.core.errors import (
    AppException,
    PayloadTooLargeError,
    build_error_response,
    register_error_handlers,
)
from app.core.logging import logger
from app.core.schemas import HealthResponse
from app.core.security import SecurityHeadersMiddleware


from app.modules.model_adapter.loader import load_model


class RequestIdAndAuditMiddleware(BaseHTTPMiddleware):
    """Assigns X-Request-ID and tracks request lifecycle without logging request body."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check client request ID or generate a new one
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        # Enforce maximum payload size via Content-Length if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_val = int(content_length)
                settings = get_settings()
                # Maximum allowed payload across media types
                max_bytes = max(settings.MAX_AUDIO_MB, settings.MAX_IMAGE_MB, getattr(settings, "MAX_VIDEO_MB", 25)) * 1024 * 1024
                if length_val > max_bytes:
                    return build_error_response(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        code="payload_too_large",
                        message=f"Request body size ({length_val} bytes) exceeds limit of {max_bytes} bytes",
                        request_id=request_id,
                    )
            except ValueError:
                pass

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # Calculate latency
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and shutdown."""
    settings = getattr(app.state, "settings", None) or get_settings()
    logger.info("Starting Ruko Backend (env=%s, version=%s)", settings.ENV, settings.VERSION)

    # Initialize Model Adapter (M1)
    scorer, degraded = load_model(settings)
    app.state.model = scorer
    app.state.model_degraded = degraded

    # Initialize Rules Engine (M2)
    try:
        from app.modules.rules.engine import get_rule_engine
        app.state.rule_engine = get_rule_engine()
        rules_status = "active"
    except Exception as exc:
        logger.warning("Failed to initialize rule engine: %s", exc)
        rules_status = "degraded"

    # Initialize Registry Service (M3)
    try:
        from app.modules.registry.service import get_registry_service
        reg_svc = get_registry_service()
        app.state.registry_service = reg_svc
        registry_status = "active" if reg_svc.is_available else "degraded"
    except Exception as exc:
        logger.warning("Failed to initialize registry service: %s", exc)
        registry_status = "degraded"

    # Initialize Extractor (M4)
    if not settings.ENABLE_THIRD_PARTY_AI:
        extractor_status = "disabled"
    elif settings.LLM_API_KEY:
        extractor_status = "active"
    else:
        extractor_status = "degraded"

    # Initialize Ingest (M5)
    if not settings.ENABLE_THIRD_PARTY_AI:
        ingest_status = "disabled"
    elif settings.LLM_API_KEY and settings.SARVAM_API_KEY:
        ingest_status = "active"
    else:
        ingest_status = "degraded"

    # Initialize Verdict Engine & i18n (M6)
    try:
        from app.modules.verdict.i18n import load_translations
        load_translations()
        verdict_status = "active"
    except Exception as exc:
        logger.warning("Failed to initialize verdict i18n: %s", exc)
        verdict_status = "degraded"

    # Initialize Voice (M7)
    if not settings.ENABLE_THIRD_PARTY_AI:
        voice_status = "disabled"
    elif settings.SARVAM_API_KEY:
        voice_status = "active"
    else:
        voice_status = "degraded"

    # Initialize Pause Layer (M8)
    pause_status = "active"

    # Initialize Guardrails Layer (M9)
    guardrails_status = "active"

    # Initialize Video Tools (M11)
    import shutil
    import subprocess
    video_status = "active"
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        # Note: External ffmpeg CLI optional; media ingest fallback handlers are active
        logger.info("ffmpeg/ffprobe CLI not found in PATH; fallback video parser ready")
        video_status = "active"

    model_status = "degraded" if degraded else "active"
    app.state.modules = {
        "model_adapter": model_status,
        "rules": rules_status,
        "registry": registry_status,
        "extractor": extractor_status,
        "ingest": ingest_status,
        "verdict": verdict_status,
        "voice": voice_status,
        "pause": pause_status,
        "guardrails": guardrails_status,
        "video": video_status,
    }
    yield
    logger.info("Shutting down Ruko Backend")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Ruko Backend",
        description="Multilingual investor-protection API for suspicious investment tips",
        version=settings.VERSION,
        lifespan=lifespan,
    )
    app.state.settings = settings

    # 1. Uniform Error Handlers
    register_error_handlers(app)

    # 2. CORS Middleware
    origins = settings.get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # 4. Rate Limiting Middleware (30 req/min limit per client IP)
    from app.core.security import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

    # 5. Request ID & Body Limit Middleware
    app.add_middleware(RequestIdAndAuditMiddleware)

    # 6. Core Liveness & Health Endpoint
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health() -> Dict[str, object]:
        """Liveness check and module readiness status."""
        current_modules = getattr(
            app.state,
            "modules",
            {
                "model_adapter": "disabled",
                "rules": "disabled",
                "registry": "disabled",
                "extractor": "disabled",
                "ingest": "disabled",
                "verdict": "disabled",
                "voice": "disabled",
                "pause": "disabled",
                "guardrails": "disabled",
                "video": "disabled",
            },
        )
        model_status = current_modules.get("model_adapter", "disabled")
        return {
            "status": "ok",
            "version": settings.VERSION,
            "modules": current_modules,
            "model": model_status,
        }

    # 7. Mount API routers
    from app.api.routes_check import router as check_router
    from app.api.routes_misc import router as misc_router
    from app.api.routes_media import router as media_router
    from app.api.routes_pause import router as pause_router
    from app.api.routes_ai import router as ai_router
    app.include_router(check_router)
    app.include_router(misc_router)
    app.include_router(media_router)
    app.include_router(pause_router)
    app.include_router(ai_router)

    return app


app = create_app()
