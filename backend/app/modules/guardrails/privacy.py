"""Privacy disclosure and zero-storage policy manager."""

from typing import Any, Dict, List
from app.core.config import Settings, get_settings


def get_privacy_disclosure(settings: Settings | None = None) -> Dict[str, Any]:
    """Return privacy policies, data retention rules, and active third-party processor disclosures.

    RUKO PRIVACY GUARANTEES:
    1. Zero persistence of user messages, images, audio, video reels, or PII.
    2. In-memory processing only; no disk or database storage of user inputs.
    3. Video reel processing uses private in-memory tempfs (/dev/shm) wiped immediately in a finally block.
    4. Logging is strictly limited to metadata (request_id, endpoint, verdict, language, latency_ms, degraded).
    5. Third-party disclosures dynamically reflect active configuration.
    """
    conf = settings or get_settings()

    processors: List[Dict[str, Any]] = []

    # Check external third-party AI status
    if conf.ENABLE_THIRD_PARTY_AI:
        # LLM Provider disclosure
        if conf.LLM_API_KEY:
            processors.append(
                {
                    "name": f"{conf.LLM_PROVIDER.title()} AI",
                    "role": "LLM Structured Claim Extraction & Vision OCR",
                    "endpoint": f"Configured {conf.LLM_PROVIDER} API endpoint",
                    "data_sent": "User message text (isolated in untrusted data delimiters), screenshot bytes, or extracted video frame bytes for OCR",
                    "storage_policy": "Episodic API processing only; Ruko retains zero data",
                    "authority": "Extracts structured factual entities only; never decides the scam verdict",
                }
            )

        # Sarvam AI STT & TTS disclosure
        if conf.SARVAM_API_KEY:
            processors.append(
                {
                    "name": "Sarvam AI",
                    "role": "Indic Speech-to-Text & Text-to-Speech",
                    "endpoint": conf.SARVAM_STT_URL,
                    "data_sent": "User voice-note bytes or extracted video audio bytes (for transcription) or safe templated script (for TTS)",
                    "storage_policy": "Episodic audio transcription; Ruko retains zero audio data",
                    "authority": "Speech recognition and voice synthesis only",
                }
            )

    local_components = [
        {
            "name": "Ruko Local ML Model",
            "role": "Scam Risk Classification",
            "execution": "100% on-device/local inference via Scikit-Learn; no external network transmission",
        },
        {
            "name": "Ruko Rules Engine",
            "role": "Deterministic Red-Flag Pattern Matching",
            "execution": "100% local compiled regex pattern evaluation; no external network transmission",
        },
        {
            "name": "SEBI Intermediary Registry Snapshot",
            "role": "Offline Registration Verification",
            "execution": f"100% local offline CSV snapshot search; dated snapshot ({getattr(conf, 'SEBI_SNAPSHOT_DATE', '2026-03-01')})",
        },
        {
            "name": "Local Video Demuxer & Tempfs",
            "role": "In-Memory Frame Extraction & Audio Splitting",
            "execution": "Local ffmpeg execution inside private directory (0700/0600) wiped immediately upon completion",
        },
    ]

    return {
        "policy": "zero_persistence_by_design",
        "description": "Ruko is designed for strict privacy. We do not store, database, or sell your messages or media.",
        "storage": {
            "user_messages": "none",
            "images": "none",
            "audio": "none",
            "videos": "none",
            "video_frames": "none",
            "pii": "none",
            "database_present": False,
        },
        "audit_logging": {
            "allowed_fields": [
                "request_id",
                "endpoint",
                "verdict",
                "language",
                "latency_ms",
                "degraded",
            ],
            "forbidden_fields": [
                "request_body",
                "message_text",
                "image_data",
                "audio_data",
                "video_data",
                "video_frames",
                "transcripts",
                "prompts",
                "llm_responses",
                "phone_numbers",
                "upi_ids",
                "temp_files",
            ],
        },
        "third_party_ai_enabled": conf.ENABLE_THIRD_PARTY_AI,
        "third_party_processors": processors,
        "local_components": local_components,
        "registry_source": {
            "type": "offline_dated_snapshot",
            "official_portal": conf.SEBI_VERIFY_URL,
            "disclaimer": "Snapshot is not real-time SEBI live data. Absence in snapshot indicates 'not confirmed', never 'fake'.",
        },
    }
