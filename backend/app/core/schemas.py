"""Core Pydantic schemas for Ruko API requests, responses, and errors."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


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
    text: Optional[str] = Field(None, description="Extracted message text (for media OCR/STT/video)")
    source: Optional[str] = Field(None, description="Input source (ocr | stt | text | video)")
    input_source: Optional[str] = Field("text", description="Normalized input source: text | ocr | stt | video")
    speech_text: Optional[str] = Field(None, description="Transcribed audio speech from video")
    on_screen_text: Optional[str] = Field(None, description="Extracted on-screen text from video frames")
    hint: Optional[str] = Field(None, description="Contextual user guidance hint, e.g. for Instagram links")


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


# ============================================================================
# Document Explanation Schemas (Module: docexplain)
# ============================================================================

class GlossaryItem(BaseModel):
    """Glossary entry explaining a complex legal or financial term."""

    term: str = Field(..., min_length=1, description="Term or phrase explained")
    meaning: str = Field(..., min_length=1, description="Plain-language explanation")
    evidence: str = Field(..., description="Verbatim quote from source document")

    model_config = ConfigDict(extra="forbid")


class KeyPoint(BaseModel):
    """Grounded key takeaway or clause summary."""

    id: str = Field(..., description="Unique key point identifier, e.g. kp_1")
    category: Literal["obligation", "fee", "deadline", "risk", "right", "other"] = Field(
        ..., description="Category of key point"
    )
    text: str = Field(..., min_length=1, description="Plain-language takeaway")
    evidence: str = Field(..., description="Verbatim quote from source document")

    model_config = ConfigDict(extra="forbid")


class Step(BaseModel):
    """Actionable step or chronological milestone for the user."""

    order: int = Field(..., ge=1, description="Step sequence number")
    title: str = Field(..., min_length=1, description="Step title")
    text: str = Field(..., min_length=1, description="Detailed explanation of the step")
    evidence: str = Field(..., description="Verbatim quote from source document")

    model_config = ConfigDict(extra="forbid")


class GraphNode(BaseModel):
    """Node in a JSON diagram graph."""

    id: str = Field(..., description="Unique node ID")
    label: str = Field(..., max_length=60, description="Node display label (max 60 chars)")
    kind: Literal["start", "step", "decision", "end", "money", "party", "loop"] = Field(
        ..., description="Node visual/functional type"
    )

    model_config = ConfigDict(extra="forbid")


class GraphEdge(BaseModel):
    """Directed edge connecting two nodes in a diagram."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: Optional[str] = Field(None, description="Optional edge transition label")

    model_config = ConfigDict(extra="forbid")


class FlowGraph(BaseModel):
    """Structured graph for flowcharts or process diagrams."""

    title: str = Field(..., description="Diagram title")
    nodes: List[GraphNode] = Field(default_factory=list, description="Diagram nodes (max 12)")
    edges: List[GraphEdge] = Field(default_factory=list, description="Directed edges")

    model_config = ConfigDict(extra="forbid")


class TimelineItem(BaseModel):
    """Event or milestone on a timeline diagram."""

    label: str = Field(..., description="Milestone event description")
    date_text: str = Field(..., description="Date or timeframe text")
    evidence: str = Field(..., description="Verbatim quote from source document")

    model_config = ConfigDict(extra="forbid")


class Diagrams(BaseModel):
    """Collection of validated JSON diagram representations."""

    flowchart: Optional[FlowGraph] = Field(None, description="Process or decision flowchart")
    money_flow: Optional[FlowGraph] = Field(None, description="Financial or payment flow diagram")
    timeline: List[TimelineItem] = Field(default_factory=list, description="Chronological timeline events")

    model_config = ConfigDict(extra="forbid")


class SceneVisual(BaseModel):
    """Visual asset specification for a browser-rendered video scene."""

    type: Literal["title", "bullets", "flowchart", "timeline", "money_flow"] = Field(
        ..., description="Visual scene layout type"
    )
    ref: Optional[str] = Field(None, description="Reference to diagram, key point id, or visual key")

    model_config = ConfigDict(extra="forbid")


class Scene(BaseModel):
    """Individual scene in a browser-rendered storyboard."""

    scene_id: str = Field(..., description="Unique scene identifier, e.g. scene_1")
    narration: str = Field(..., max_length=300, description="TTS-friendly spoken script (<= 300 chars)")
    caption: str = Field(..., max_length=80, description="On-screen text subtitle/caption (<= 80 chars)")
    visual: SceneVisual = Field(..., description="Visual configuration for this scene")
    issued_at: int = Field(..., description="Unix timestamp (seconds) when speak token was signed")
    speak_token: str = Field(..., description="HMAC-SHA256 signature for safe audio synthesis")

    model_config = ConfigDict(extra="forbid")


class DocExplanation(BaseModel):
    """Comprehensive grounded document explanation output."""

    request_id: str = Field(..., description="Unique request UUID")
    language: str = Field(..., description="Requested or detected explanation language")
    input_source: str = Field(..., description="Input source type: pdf | docx | text | ocr")
    doc_type_guess: str = Field(..., description="Inferred document type (e.g. loan_agreement, insurance_policy)")
    summary: str = Field(..., description="Plain-language comprehensive summary")
    glossary: List[GlossaryItem] = Field(default_factory=list, description="Grounded term explanations")
    key_points: List[KeyPoint] = Field(default_factory=list, description="Categorized grounded takeaways")
    steps: List[Step] = Field(default_factory=list, description="Chronological actionable steps")
    diagrams: Diagrams = Field(default_factory=Diagrams, description="JSON diagram representations")
    storyboard: List[Scene] = Field(default_factory=list, description="4-8 browser video storyboard scenes")
    ruko_flags: List[Reason] = Field(default_factory=list, description="Red flags surfaced by Ruko rules/checker")
    registry: Optional[RegistryInfo] = Field(None, description="SEBI snapshot lookup details if claimed")
    ocr_quality: Literal["good", "low", "n/a"] = Field("n/a", description="OCR quality assessment")
    confidence_notes: List[str] = Field(default_factory=list, description="Honest uncertainty and limitation notes")
    disclaimer: str = Field(..., description="Localized educational disclaimer")
    degraded: List[str] = Field(default_factory=list, description="Non-blocking degradation flags")

    model_config = ConfigDict(extra="forbid")


class ExplainSpeakRequest(BaseModel):
    """Request payload to synthesize speech for a verified storyboard scene."""

    request_id: str = Field(..., description="Request UUID matching the scene")
    scene_id: str = Field(..., description="Scene ID to synthesize")
    language: str = Field("en", description="Target language (en | hi | gu | hinglish | gujlish)")
    narration: str = Field(..., max_length=300, description="Exact verified narration text (<= 300 chars)")
    issued_at: int = Field(..., description="Timestamp issued in storyboard")
    speak_token: str = Field(..., description="HMAC-SHA256 signature token")

    model_config = ConfigDict(extra="forbid")


# =============================================================================
# Breach Exposure Check Schemas (Stateless)
# =============================================================================

class ExposureRecord(BaseModel):
    """Normalized, sanitized record of a specific data breach exposure."""

    breach_name: str = Field(..., description="Name of the service or incident")
    breach_date: str = Field(..., description="Approximate date or year of exposure")
    exposure_categories: List[str] = Field(default_factory=list, description="Sanitized data categories exposed")
    risk_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Conservative deterministic risk assessment")
    financial_exposure: bool = Field(False, description="True ONLY if banking, card, or payment data was exposed")
    provider: str = Field(..., description="Provider source: mock | hibp")
    remediation_notes: List[str] = Field(default_factory=list, description="Actionable safety recommendations")

    model_config = ConfigDict(extra="forbid")


class BreachCheckRequest(BaseModel):
    """Stateless breach check request payload."""

    email: str = Field(..., min_length=3, max_length=320, description="Email address to check")
    consent: bool = Field(..., description="Explicit user consent to query breach index (must be true)")

    model_config = ConfigDict(extra="forbid")


class BreachCheckResult(BaseModel):
    """Stateless summary and exposure findings for an email query."""

    request_id: str = Field(..., description="Request tracing UUID")
    status: Literal["ok", "incomplete", "scan_unavailable"] = Field(..., description="Scan execution status")
    is_demo: bool = Field(False, description="True if mock/synthetic demo records are returned")
    exposures: List[ExposureRecord] = Field(default_factory=list, description="List of normalized breach exposures")
    total_exposures: int = Field(0, description="Total count of exposures found")
    high_risk_count: int = Field(0, description="Count of HIGH risk exposures")
    financial_exposure_count: int = Field(0, description="Count of exposures with financial data")
    notice: str = Field(..., description="Educational honest guidance note")
    data_safety: List[str] = Field(default_factory=list, description="Explicit data safety guarantees")
    degraded: List[str] = Field(default_factory=list, description="Non-blocking degradation or error notices")

    model_config = ConfigDict(extra="forbid")


class PhoneStartRequest(BaseModel):
    """Request payload to initiate phone verification via Twilio Verify."""

    phone: str = Field(..., min_length=8, max_length=20, description="E.164 phone number (+91...)")
    consent: bool = Field(..., description="User consent to receive verification OTP")
    channel: Literal["sms", "call"] = Field("sms", description="Verification delivery channel: sms or call")

    model_config = ConfigDict(extra="forbid")


class PhoneStartResponse(BaseModel):
    """Response indicating verification code dispatch."""

    status: Literal["ok", "sms_unavailable_try_call"] = Field("ok", description="Dispatch status")
    message: str = Field(..., description="Human-friendly status explanation")

    model_config = ConfigDict(extra="forbid")


class PhoneVerifyRequest(BaseModel):
    """Request payload to verify OTP against Twilio Verify."""

    phone: str = Field(..., min_length=8, max_length=20, description="E.164 phone number")
    code: str = Field(..., min_length=4, max_length=8, pattern=r"^\d{4,8}$", description="Verification code (4 to 8 digits)")

    model_config = ConfigDict(extra="forbid")


class PhoneVerifyResponse(BaseModel):
    """Stateless phone authorization token valid for 15 minutes."""

    phone_token: str = Field(..., description="Signed token confirming phone possession")

    model_config = ConfigDict(extra="forbid")


class BreachAlertRequest(BaseModel):
    """Request payload to trigger an automated emergency voice alert call."""

    phone: str = Field(..., min_length=8, max_length=20, description="Verified E.164 phone number")
    phone_token: str = Field(..., description="Valid 15-minute phone authorization token")
    voice_opt_in: bool = Field(..., description="Explicit opt-in to receive automated voice alert call")
    exposures_high_risk_new: bool = Field(False, description="Flag indicating high-risk exposure state")
    email: Optional[str] = Field(None, description="Scanned email address for alert context")
    total_breaches: int = Field(0, description="Total count of exposures")
    financial_exposed: bool = Field(False, description="Whether financial records were exposed")
    breach_names: List[str] = Field(default_factory=list, description="Names of exposed platforms")
    exposure_categories: List[str] = Field(default_factory=list, description="Leaked categories")
    is_test_call: bool = Field(True, description="Whether this is a user-initiated test call (bypasses quiet hours)")

    model_config = ConfigDict(extra="ignore")


class BreachAlertResponse(BaseModel):
    """Outcome of alert call dispatch eligibility check."""

    status: Literal["ok", "rejected", "disabled", "simulated"] = Field(..., description="Alert dispatch status")
    message: str = Field(..., description="Explanation of dispatch decision")
    call_placed: bool = Field(False, description="True if voice call was successfully dispatched")
    script: Optional[str] = Field(None, description="Exact text of the fixed security alert script")
    hint: Optional[str] = Field(None, description="Actionable hint for client UI e.g. live_calls_unavailable")

    model_config = ConfigDict(extra="forbid")
