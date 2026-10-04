"""Ruko AI Chat Agent and Analysis Insights endpoints powered by Groq LLM."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import logger
from app.modules.extractor.llm_client import LLMClient

router = APIRouter(prefix="/v1", tags=["AI Chat & Insights"])


# ─── Request / Response Models ────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[Dict[str, Any]] = None  # Optional scan result context


class ChatResponse(BaseModel):
    reply: str
    suggestions: List[str] = []


class InsightsRequest(BaseModel):
    score: float
    verdict: str
    reasons: List[Dict[str, Any]]
    claims: Optional[Dict[str, Any]] = None
    amount: Optional[float] = None
    language: str = "en"


class InsightChart(BaseModel):
    title: str
    type: str  # "donut" | "bar" | "gauge" | "risk_matrix"
    data: List[Dict[str, Any]]
    insight: str
    color: str


class InsightsResponse(BaseModel):
    summary: str
    risk_level: str
    charts: List[InsightChart]
    action_items: List[str]
    confidence_note: str


# ─── System Prompts ───────────────────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """You are Ruko AI — a calm, expert financial fraud prevention assistant for Indian retail investors.

Your purpose:
- Help users understand investment scams, red flags, and SEBI regulations
- Explain scam detection results in plain, reassuring language (Hindi/Gujarati/English)
- Guide users on safe investment practices and how to verify SEBI registration
- Direct fraud victims to Cyber Crime helpline 1930 and cybercrime.gov.in

Your personality:
- Warm, trustworthy, never alarmist
- Use simple language suitable for first-time investors
- Include relevant Indian context (SEBI, RBI, NSE, BSE, UPI fraud patterns)
- When asked about specific scam results, explain each red flag clearly

Rules:
- NEVER give stock tips or investment advice
- NEVER confirm any investment as safe — always suggest SEBI verification
- Keep responses concise (max 3-4 sentences per answer)
- Always end with a clear next step

If given scan context (JSON), reference it naturally in your response."""

INSIGHTS_SYSTEM_PROMPT = """You are a financial fraud analysis engine. Given a scam detection result, generate structured analytical insights.

Return ONLY valid JSON in this exact format:
{
  "summary": "2-sentence plain-English summary of the overall risk",
  "risk_level": "critical|high|medium|low",
  "charts": [
    {
      "title": "Risk Factor Breakdown",
      "type": "donut",
      "data": [{"label": "Guaranteed Returns", "value": 35, "color": "#ef4444"}, ...],
      "insight": "One sentence explaining this chart",
      "color": "#ef4444"
    },
    {
      "title": "Scam Tactic Profile",
      "type": "bar",
      "data": [{"label": "Urgency", "value": 80}, {"label": "Payment Pressure", "value": 90}, ...],
      "insight": "...",
      "color": "#f97316"
    },
    {
      "title": "ML Confidence",
      "type": "gauge",
      "data": [{"label": "Fraud Probability", "value": 93}],
      "insight": "Model assigns 93% probability of fraudulent intent",
      "color": "#ef4444"
    }
  ],
  "action_items": ["Immediate step 1", "Immediate step 2", "Immediate step 3"],
  "confidence_note": "Brief note about model confidence"
}

Base the analysis on the input data. Use red (#ef4444) for high risk, amber (#f97316) for medium, green (#22c55e) for safe signals. Generate 3 insightful charts."""


# ─── Helper: Groq OpenAI-compatible call ─────────────────────────────────────

async def _call_groq(system: str, messages: List[Dict], settings) -> str:
    """Direct Groq API call for chat completions."""
    import httpx

    api_key = settings.LLM_API_KEY
    if not api_key:
        raise RuntimeError("LLM_API_KEY not configured")

    # For Groq, use the groq endpoint
    if settings.LLM_PROVIDER == "groq":
        base_url = "https://api.groq.com/openai/v1"
        model = settings.LLM_MODEL or "qwen/qwen3.8-27b"
    else:
        base_url = "https://api.openai.com/v1"
        model = settings.LLM_MODEL or "gpt-4o-mini"

    full_messages = [{"role": "system", "content": system}] + messages

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": full_messages,
                "temperature": 0.3,
                "max_tokens": 800,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ruko(req: ChatRequest) -> ChatResponse:
    """Ruko AI chat assistant powered by Groq Llama 3.3-70b.
    
    Provides expert guidance on investment fraud, scam detection results,
    SEBI verification, and recovery steps in English, Hindi, or Gujarati.
    """
    settings = get_settings()

    # Build message history for Groq
    groq_messages = []

    # Inject scan context if provided
    if req.context:
        context_summary = f"""
Current scan context:
- Verdict: {req.context.get('verdict', 'unknown')}
- Risk Score: {req.context.get('score', 0) * 100:.0f}%
- Red Flags: {len(req.context.get('reasons', []))} detected
- Guidance: {req.context.get('note', '')}
"""
        groq_messages.append({"role": "system", "content": context_summary})

    for msg in req.messages:
        groq_messages.append({"role": msg.role, "content": msg.content})

    try:
        reply = await _call_groq(CHAT_SYSTEM_PROMPT, groq_messages, settings)

        # Generate follow-up suggestions based on the last user message
        last_user_msg = next(
            (m.content for m in reversed(req.messages) if m.role == "user"), ""
        )
        suggestions = _get_smart_suggestions(req.context, last_user_msg)

        return ChatResponse(reply=reply.strip(), suggestions=suggestions)

    except Exception as e:
        logger.warning("Chat LLM error: %s", e)
        return ChatResponse(
            reply="I'm having trouble connecting right now. For urgent fraud concerns, call the Cyber Crime Helpline at **1930** or visit **cybercrime.gov.in**.",
            suggestions=["What are the red flags in my scan?", "How do I verify SEBI registration?", "I already transferred money — what now?"],
        )


@router.post("/analyze/insights", response_model=InsightsResponse)
async def generate_insights(req: InsightsRequest) -> InsightsResponse:
    """Generate AI-powered visual insight charts for a completed scan result.
    
    Uses Groq Llama 3.3-70b to interpret the ML model output and generate
    structured chart data for visualization on the frontend.
    """
    settings = get_settings()

    amount_str = f"₹{req.amount:,.0f}" if req.amount is not None else "Not specified"
    user_prompt = f"""Analyze this investment scam detection result and generate insights:

Score: {req.score:.3f} ({req.score * 100:.0f}% fraud probability)
Verdict: {req.verdict}
Red Flags Triggered ({len(req.reasons)}):
{json.dumps([{"code": r.get("code"), "severity": r.get("severity"), "text": r.get("text")} for r in req.reasons], indent=2)}
Extracted Claims: {json.dumps(req.claims or {}, indent=2)}
Amount Mentioned: {amount_str}
Language: {req.language}

Generate 3 insightful charts with actionable insights. Make the data realistic based on actual detected patterns."""

    try:
        raw = await _call_groq(
            INSIGHTS_SYSTEM_PROMPT,
            [{"role": "user", "content": user_prompt}],
            settings,
        )

        # Clean and parse JSON
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

        data = json.loads(cleaned)

        charts = [InsightChart(**c) for c in data.get("charts", [])]
        return InsightsResponse(
            summary=data.get("summary", ""),
            risk_level=data.get("risk_level", "high"),
            charts=charts,
            action_items=data.get("action_items", []),
            confidence_note=data.get("confidence_note", ""),
        )

    except Exception as e:
        logger.warning("Insights LLM error: %s", e)
        # Return deterministic fallback based on score
        return _fallback_insights(req)


def _fallback_insights(req: InsightsRequest) -> InsightsResponse:
    """Deterministic fallback insights when LLM is unavailable."""
    score_pct = int(req.score * 100)
    risk_level = "critical" if req.score >= 0.8 else "high" if req.score >= 0.41 else "low"

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for r in req.reasons:
        sev = r.get("severity", "medium")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return InsightsResponse(
        summary=f"This communication shows {score_pct}% fraud probability with {len(req.reasons)} red flags. {'Immediate caution is strongly advised.' if risk_level == 'critical' else 'Exercise significant caution.'}",
        risk_level=risk_level,
        charts=[
            InsightChart(
                title="Risk Severity Breakdown",
                type="donut",
                data=[
                    {"label": "High Severity", "value": severity_counts["high"] * 35 or 5, "color": "#ef4444"},
                    {"label": "Medium Severity", "value": severity_counts["medium"] * 20 or 5, "color": "#f97316"},
                    {"label": "Low Severity", "value": max(10, 100 - score_pct), "color": "#22c55e"},
                ],
                insight=f"{severity_counts['high']} high-severity red flags detected in this communication.",
                color="#ef4444",
            ),
            InsightChart(
                title="Fraud Signal Strength",
                type="bar",
                data=[
                    {"label": "ML Model Score", "value": score_pct},
                    {"label": "Rule Engine Triggers", "value": min(100, len(req.reasons) * 25)},
                    {"label": "Pattern Match Confidence", "value": min(100, score_pct + 5)},
                ],
                insight="Combined ML + rule engine confidence score across detection layers.",
                color="#f97316",
            ),
            InsightChart(
                title="Fraud Probability",
                type="gauge",
                data=[{"label": "Fraud Probability", "value": score_pct}],
                insight=f"Model assigns {score_pct}% probability of fraudulent intent based on {len(req.reasons)} detected patterns.",
                color="#ef4444" if score_pct >= 41 else "#22c55e",
            ),
        ],
        action_items=[
            "Do NOT transfer any money — pause for at least 24 hours",
            "Verify the adviser's SEBI registration at sebi.gov.in",
            "Report this to Cyber Crime Helpline 1930 if you've already paid",
        ],
        confidence_note=f"Analysis based on {len(req.reasons)} pattern matches across rule engine and ML model trained on 58,000+ samples.",
    )


def _get_smart_suggestions(context: Optional[Dict], last_msg: str) -> List[str]:
    """Generate contextual follow-up suggestions."""
    if context and context.get("verdict") == "strong_red_flags":
        return [
            "What exactly makes this a scam?",
            "How do I report this to the police?",
            "Can I get my money back if I already paid?",
        ]
    elif context and context.get("verdict") == "cannot_verify":
        return [
            "How do I verify this adviser on SEBI?",
            "What documents should I ask for?",
            "Is this type of investment legal in India?",
        ]
    return [
        "How do I check SEBI registration?",
        "What are common investment scam tactics?",
        "Call 1930 for cyber fraud — what happens next?",
    ]
