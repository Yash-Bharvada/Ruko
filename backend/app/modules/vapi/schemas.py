"""Pydantic schemas for Vapi AI voice calling sessions and webhooks."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VapiSessionRequest(BaseModel):
    """Payload to initiate an interactive WebRTC call session or prepare Vapi config."""

    email: str = Field(..., description="Target email address scanned")
    total_breaches: int = Field(0, description="Total number of breaches found")
    high_risk_count: int = Field(0, description="Count of high-risk incidents")
    financial_exposed: bool = Field(False, description="Whether financial data was leaked")
    breach_names: List[str] = Field(default_factory=list, description="Names of breached platforms")
    exposure_categories: List[str] = Field(default_factory=list, description="Leaked categories")
    language: Optional[str] = Field("en", description="User preferred language code (en, hi, gu)")


class VapiSessionResponse(BaseModel):
    """Configuration returned to the frontend client to start in-browser voice conversation."""

    status: str = Field("ready", description="'ready' or 'simulated' or 'not_configured'")
    assistant_id: Optional[str] = Field(None, description="Configured Vapi assistant ID")
    public_key: Optional[str] = Field(None, description="Vapi public API key for web calling")
    first_message: str = Field(..., description="Dynamic first message to speak")
    system_prompt: str = Field(..., description="Injected system prompt")
    variable_values: Dict[str, Any] = Field(default_factory=dict, description="Variables for template substitution")
    message: Optional[str] = None


class VapiPhoneCallRequest(BaseModel):
    """Payload to place an outbound phone call via Vapi."""

    phone: str = Field(..., description="E.164 phone number to call (e.g. +919876543210)")
    email: str = Field(..., description="Target email address scanned")
    total_breaches: int = Field(0, description="Total number of breaches found")
    high_risk_count: int = Field(0, description="Count of high-risk incidents")
    financial_exposed: bool = Field(False, description="Whether financial data was leaked")
    breach_names: List[str] = Field(default_factory=list, description="Names of breached platforms")
    exposure_categories: List[str] = Field(default_factory=list, description="Leaked categories")
    language: Optional[str] = Field("en", description="Preferred language (en, hi, gu)")


class VapiPhoneCallResponse(BaseModel):
    """Response after placing or simulating an outbound Vapi phone call."""

    status: str = Field(..., description="'dispatched' | 'simulated' | 'error'")
    call_id: Optional[str] = Field(None, description="Vapi call ID")
    message: str = Field(..., description="Human readable status message")
