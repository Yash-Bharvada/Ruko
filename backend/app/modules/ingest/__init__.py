"""Ingest module for multimodal screenshot OCR and voice-note STT."""

from app.modules.ingest.ocr import IngestResult, image_to_text, sniff_image_mime
from app.modules.ingest.stt import audio_to_text, sniff_audio_mime

__all__ = [
    "IngestResult",
    "image_to_text",
    "audio_to_text",
    "sniff_image_mime",
    "sniff_audio_mime",
]
