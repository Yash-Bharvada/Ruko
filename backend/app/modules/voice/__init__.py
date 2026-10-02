"""Voice output and speech synthesis module."""

from app.modules.voice.tts import (
    AudioResult,
    BrowserSpeechFallback,
    SpeakRequest,
    build_spoken_script,
    map_language_to_bcp47,
    synthesize_speech,
)

__all__ = [
    "AudioResult",
    "BrowserSpeechFallback",
    "SpeakRequest",
    "build_spoken_script",
    "map_language_to_bcp47",
    "synthesize_speech",
]
