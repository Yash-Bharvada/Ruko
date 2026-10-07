"""Vapi AI HTTP Client for Outbound Phone and Web Call Sessions."""

from typing import Any, Dict, Optional, Tuple
import httpx

from app.core.config import Settings
from app.core.logging import logger
from app.modules.vapi.prompt import VAPI_SYSTEM_PROMPT, generate_first_message, get_agent_variable_values


class VapiClient:
    """Async client interacting with Vapi API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = getattr(settings, "VAPI_API_KEY", "").strip()
        self.public_key = getattr(settings, "VAPI_PUBLIC_KEY", "").strip()
        self.assistant_id = getattr(settings, "VAPI_ASSISTANT_ID", "").strip()
        self.phone_number_id = getattr(settings, "VAPI_PHONE_NUMBER_ID", "").strip()
        self.base_url = getattr(settings, "VAPI_BASE_URL", "https://api.vapi.ai").rstrip("/")
        self.is_simulate = getattr(settings, "VAPI_SIMULATE", False) or not bool(self.api_key)

    async def create_outbound_call(
        self,
        phone_e164: str,
        email: str,
        total_breaches: int,
        high_risk_count: int,
        financial_exposed: bool,
        breach_names: list[str],
        exposure_categories: list[str],
        language: str = "en",
    ) -> Tuple[str, Optional[str], str]:
        """Trigger an outbound phone call via Vapi API or simulation.

        Returns:
            (status: "dispatched" | "simulated" | "error", call_id, message)
        """
        first_message = generate_first_message(
            email=email,
            total_breaches=total_breaches,
            financial_exposed=financial_exposed,
            language=language,
        )
        variable_values = get_agent_variable_values(
            email=email,
            total_breaches=total_breaches,
            high_risk_count=high_risk_count,
            financial_exposed=financial_exposed,
            breach_names=breach_names,
            exposure_categories=exposure_categories,
        )

        if self.is_simulate or not self.api_key:
            logger.info("Vapi simulation active: simulated outbound call to %s", phone_e164[:4] + "****")
            return (
                "simulated",
                "sim-vapi-call-" + email.split("@")[0],
                f"Simulated outbound call initiated for {email}. Ready to connect when Vapi key is configured.",
            )

        # Call live Vapi API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Build assistant overrides with dynamic prompt and variables
        payload: Dict[str, Any] = {
            "type": "outboundPhoneCall",
            "phoneNumberId": self.phone_number_id,
            "customer": {"number": phone_e164},
            "assistantOverrides": {
                "firstMessage": first_message,
                "variableValues": variable_values,
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": VAPI_SYSTEM_PROMPT,
                        }
                    ],
                },
            },
        }

        if self.assistant_id:
            payload["assistantId"] = self.assistant_id

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{self.base_url}/call/phone", headers=headers, json=payload)
                if res.status_code in (200, 201):
                    data = res.json()
                    call_id = data.get("id")
                    logger.info("Vapi outbound call dispatched successfully: call_id=%s", call_id)
                    return ("dispatched", call_id, "Outbound AI voice consultation call initiated successfully.")
                else:
                    logger.warning("Vapi API returned error %s: %s", res.status_code, res.text)
                    return ("error", None, f"Vapi telephony error ({res.status_code}): {res.text}")
        except Exception as exc:
            logger.error("Failed to connect to Vapi API: %s", exc)
            return ("error", None, f"Network error contacting Vapi: {str(exc)}")
