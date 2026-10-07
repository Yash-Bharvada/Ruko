"""Application configuration loaded from environment variables (reloaded)."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Ruko backend."""

    ENV: str = "development"
    VERSION: str = "0.1.0"
    CORS_ORIGINS: str = "*"

    # Limits and Thresholds
    MAX_TEXT_CHARS: int = 4000
    MAX_IMAGE_MB: int = 5
    MAX_AUDIO_MB: int = 10
    MAX_VIDEO_MB: int = 25
    MAX_VIDEO_SECONDS: int = 180
    MAX_FRAMES: int = 8
    FRAME_INTERVAL_SECONDS: int = 3
    RATE_LIMIT_PER_MIN: int = 30

    # Feature Flags and Paths
    DEMO_MODE: bool = False
    ENABLE_THIRD_PARTY_AI: bool = True
    ENABLE_URL_VIDEO_INGEST: bool = True
    TRANSCRIBED_NEVER_CLEAR: bool = True
    MODEL_DIR: str = "model_store"
    MODEL_REQUIRED: bool = False
    HIGH_BAND: float = 0.80
    LOW_BAND: float = 0.20
    SARVAM_STT_MAX_SECONDS: int = 60

    # Third Party Provider Placeholders
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-flash-lite-latest"
    SARVAM_API_KEY: str = ""
    SARVAM_STT_URL: str = "https://api.sarvam.ai/speech-to-text"
    SARVAM_STT_MODEL: str = "saaras:v2"
    SARVAM_TTS_URL: str = "https://api.sarvam.ai/text-to-speech"
    SARVAM_TTS_MODEL: str = "bulbul:v1"
    SARVAM_TTS_SPEAKER: str = "meera"
    MAX_TTS_CHARS: int = 500
    GROQ_WHISPER_MODEL: str = "whisper-large-v3-turbo"

    # SEBI Snapshot / Verification URL
    SEBI_VERIFY_URL: str = "https://www.sebi.gov.in"

    # Explain a Document Module Settings
    EXPLAIN_ENABLED: bool = True
    EXPLAIN_MAX_MB: int = 10
    EXPLAIN_MAX_PAGES: int = 20
    EXPLAIN_MAX_CHARS: int = 30000
    EXPLAIN_LLM_TIMEOUT_S: float = 40.0
    EXPLAIN_SIGNING_KEY: str = ""
    EXPLAIN_TOKEN_TTL_S: int = 1800

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_cors_origins(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
