"""Vapi AI Voice Calling Agent module for real-time interactive multilingual breach consultations."""

from app.modules.vapi.client import VapiClient
from app.modules.vapi.prompt import VAPI_SYSTEM_PROMPT, generate_first_message, get_agent_variable_values

__all__ = ["VapiClient", "VAPI_SYSTEM_PROMPT", "generate_first_message", "get_agent_variable_values"]
