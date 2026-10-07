"""API endpoints for Vapi AI voice calling integration."""

from fastapi import APIRouter, Request
from app.core import config
from app.core.logging import logger
from app.modules.vapi.client import VapiClient
from app.modules.vapi.prompt import VAPI_SYSTEM_PROMPT, generate_first_message, get_agent_variable_values
from app.modules.vapi.schemas import (
    VapiPhoneCallRequest,
    VapiPhoneCallResponse,
    VapiSessionRequest,
    VapiSessionResponse,
)

router = APIRouter(prefix="/v1/vapi", tags=["Vapi Voice Assistant"])


@router.post("/session", response_model=VapiSessionResponse)
async def get_vapi_session(request: Request, payload: VapiSessionRequest) -> VapiSessionResponse:
    """Prepare Vapi AI voice session context for in-browser WebRTC calling.

    Injects the scan's breach context, tailored first greeting in user's language,
    and system instructions.
    """
    settings = getattr(request.app.state, "settings", None) or config.get_settings()

    first_message = generate_first_message(
        email=payload.email,
        total_breaches=payload.total_breaches,
        financial_exposed=payload.financial_exposed,
        language=payload.language,
    )
    variable_values = get_agent_variable_values(
        email=payload.email,
        total_breaches=payload.total_breaches,
        high_risk_count=payload.high_risk_count,
        financial_exposed=payload.financial_exposed,
        breach_names=payload.breach_names,
        exposure_categories=payload.exposure_categories,
    )

    public_key = getattr(settings, "VAPI_PUBLIC_KEY", "") or getattr(settings, "VAPI_API_KEY", "")
    assistant_id = getattr(settings, "VAPI_ASSISTANT_ID", "")
    is_simulate = getattr(settings, "VAPI_SIMULATE", False) or not bool(public_key)

    return VapiSessionResponse(
        status="simulated" if is_simulate else "ready",
        assistant_id=assistant_id if assistant_id else None,
        public_key=public_key if public_key else None,
        first_message=first_message,
        system_prompt=VAPI_SYSTEM_PROMPT,
        variable_values=variable_values,
        message="VAPI_SIMULATE=true: Dry-run active. Zero Vapi credits consumed."
        if is_simulate
        else "Session prepared with breach exposure context.",
    )


@router.post("/call/phone", response_model=VapiPhoneCallResponse)
async def trigger_vapi_phone_call(request: Request, payload: VapiPhoneCallRequest) -> VapiPhoneCallResponse:
    """Trigger an outbound phone call with Vapi AI to discuss breach findings."""
    settings = getattr(request.app.state, "settings", None) or config.get_settings()
    client = VapiClient(settings)

    status_str, call_id, msg = await client.create_outbound_call(
        phone_e164=payload.phone,
        email=payload.email,
        total_breaches=payload.total_breaches,
        high_risk_count=payload.high_risk_count,
        financial_exposed=payload.financial_exposed,
        breach_names=payload.breach_names,
        exposure_categories=payload.exposure_categories,
        language=payload.language or "en",
    )

    return VapiPhoneCallResponse(
        status=status_str,
        call_id=call_id,
        message=msg,
    )


@router.post("/webhook")
async def vapi_webhook(request: Request) -> dict:
    """Webhook for Vapi assistant events (call end, transcript, status)."""
    try:
        body = await request.json()
        message_type = body.get("message", {}).get("type", "unknown")
        logger.info("Received Vapi webhook event: %s", message_type)
    except Exception as exc:
        logger.debug("Failed parsing Vapi webhook body: %s", exc)
    return {"status": "ok"}
