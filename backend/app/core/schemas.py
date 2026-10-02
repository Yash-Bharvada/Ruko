"""Core Pydantic schemas for Ruko API requests, responses, and errors."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


LanguageType = Literal["gu", "hi", "en", "unknown"]
VerdictType = Literal["strong_red_flags", "cannot_verify", "no_red_flags_found", "out_of_scope"]
SeverityType = Literal["high", "medium", "low", "info"]
ReasonSourceType = Literal["rule", "model", "registry"]
RegistryStatusType = Literal["found_in_snapshot", "possible_match", "not_found_in_snapshot", "not_checked"]


class CheckRequest(BaseModel):
    """Incoming request to check investment text."""

    text: str = Field(..., min_length=1, max_length=4000, description="Raw suspicious message text")
    language: Optional[str] = Field(None, description="Optional language hint (gu, hi, en, etc.)")
    amount: Optional[float] = Field(None, ge=0, description="Optional investment amount mentioned")


class Reason(BaseModel):
    """Detailed reason for a red flag or finding."""

    code: str = Field(..., description="Unique machine-readable reason code")
    severity: str = Field(..., description="high | medium | low | info")
    text: str = Field(..., description="Localized explanation sentence")
    evidence: str = Field(..., description="Exact quoted phrase from the message")
    source: str = Field(..., description="rule | model | registry")


class RegistryInfo(BaseModel):
    """Snapshot verification outcome for claimed registration numbers/names."""

    status: str = Field(
        ...,
        description="found_in_snapshot | possible_match | not_found_in_snapshot | not_checked",
    )
    matches: List[Dict[str, Any]] = Field(default_factory=list, description="Matching records from snapshot")
    snapshot_date: str = Field("2026-03-01", description="Date of local registry snapshot")
    is_sample_data: bool = Field(True, description="True if sample/demo data is used")
    verify_url: str = Field(..., description="Official verification URL")


class ModelInfo(BaseModel):
    """Machine learning model prediction details."""

    available: bool = Field(..., description="Whether model inference was available")
    score: Optional[float] = Field(None, description="Model scam risk probability (0.0 to 1.0)")
    top_words: List[str] = Field(default_factory=list, description="Words that increased scam risk score")
    calming_words: List[str] = Field(default_factory=list, description="Words that decreased scam risk score")


class CheckResult(BaseModel):
    """Unified verdict and explainable report returned by Ruko."""

    request_id: str = Field(..., description="Unique request UUID")
    language: str = Field(..., description="Detected or requested language (gu, hi, en, unknown)")
    verdict: str = Field(
        ...,
        description="strong_red_flags | cannot_verify | no_red_flags_found | out_of_scope",
    )
    score: float = Field(..., description="Combined composite score from 0.0 to 1.0")
    reasons: List[Reason] = Field(default_factory=list, description="Ordered reasons for verdict")
    registry: RegistryInfo = Field(..., description="Registry snapshot lookup information")
    model: ModelInfo = Field(..., description="ML model output details")
    claims: Dict[str, Any] = Field(default_factory=dict, description="Extracted claims")
    note: str = Field(..., description="Localized honest summary note")
    degraded: List[str] = Field(default_factory=list, description="List of degraded or unavailable modules")
    disclaimer: str = Field(..., description="Localized legal/educational disclaimer")


class ErrorDetail(BaseModel):
    """Uniform error detail object."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    request_id: str = Field(..., description="Request UUID for tracing")


class ErrorResponse(BaseModel):
    """Top-level uniform JSON error envelope."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    """Liveness and module status response."""

    status: str = Field("ok", description="Overall health status")
    version: str = Field(..., description="Application version")
    modules: Dict[str, str] = Field(..., description="Module availability map (active|degraded|disabled)")
    model: Optional[str] = Field(None, description="Direct model status (active|degraded|disabled)")
