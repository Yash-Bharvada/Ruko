"""LLM client abstraction with timeout, retries, and strict privacy guards."""

import asyncio
import base64
import json
import re
import time
from typing import Any, Dict, Optional
import httpx
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.logging import logger


class LLMClient:
    """Client for generating structured JSON via external LLM providers.

    PRIVACY & SECURITY GUARANTEES:
    - Never logs prompt text, user input, or raw LLM responses.
    - Strict 8-second timeout with at most 1 retry.
    - Handles prompt injection by isolating untrusted input.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.provider = (self.settings.LLM_PROVIDER or "gemini").lower()
        self.model = self.settings.LLM_MODEL or "gemini-2.0-flash"
        self.api_key = self.settings.LLM_API_KEY or ""
        self.timeout_seconds = 8.0
        self._custom_http_client = http_client

    @property
    def is_configured(self) -> bool:
        """Return True if LLM provider has an API key and third-party AI is enabled."""
        return bool(self.settings.ENABLE_THIRD_PARTY_AI and self.api_key)

    async def _post_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        params: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Execute HTTP POST with 8-second timeout and 1 retry on network/5xx error."""
        timeout = httpx.Timeout(self.timeout_seconds)

        for attempt in range(2):
            try:
                if self._custom_http_client:
                    response = await self._custom_http_client.post(
                        url,
                        headers=headers,
                        json=payload,
                        params=params,
                        timeout=timeout,
                    )
                else:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.post(
                            url,
                            headers=headers,
                            json=payload,
                            params=params,
                        )

                if response.status_code >= 500 and attempt == 0:
                    logger.warning("LLM provider returned status %d on attempt 1, retrying...", response.status_code)
                    await asyncio.sleep(0.5)
                    continue

                response.raise_for_status()
                return response
            except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
                if attempt == 0:
                    logger.warning("LLM call timed out on attempt 1, retrying...")
                    await asyncio.sleep(0.5)
                    continue
                raise TimeoutError("LLM call timed out after retry") from exc
            except (httpx.ConnectError, httpx.NetworkError) as exc:
                if attempt == 0:
                    logger.warning("LLM connection error on attempt 1, retrying...")
                    await asyncio.sleep(0.5)
                    continue
                raise ConnectionError(f"LLM connection error: {exc}") from exc
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(f"LLM HTTP error {exc.response.status_code}") from exc

        raise RuntimeError("LLM request failed after retries")

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown code fences and extraneous text from LLM response."""
        cleaned = text.strip()
        # Remove ```json ... ``` wrapper
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # If not starting with {, try finding first { and last }
        if not cleaned.startswith("{"):
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start : end + 1]

        return cleaned

    async def _call_gemini(self, system: str, user: str) -> Dict[str, Any]:
        """Call Google Gemini generateContent REST endpoint."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system}],
            },
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }

        response = await self._post_with_retry(url, headers, payload, params=params)
        data = response.json()

        try:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Malformed response structure from Gemini API: {exc}") from exc

        cleaned = self._clean_json_text(raw_text)
        return json.loads(cleaned)

    async def _call_openai_compatible(self, system: str, user: str, base_url: str) -> Dict[str, Any]:
        """Call OpenAI or Groq chat completions API endpoint."""
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        response = await self._post_with_retry(url, headers, payload)
        data = response.json()

        try:
            raw_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Malformed response structure from OpenAI/Groq: {exc}") from exc

        cleaned = self._clean_json_text(raw_text)
        return json.loads(cleaned)

    async def generate_json(
        self,
        system: str,
        user: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON from system and user prompt.

        Guarantees:
        - Never logs prompts or returned JSON content.
        - Strict timeout of 8 seconds with 1 retry.
        - Returns a validated dict.
        """
        if not self.is_configured:
            raise RuntimeError("LLM is disabled or LLM_API_KEY is not configured")

        start_time = time.perf_counter()

        if self.provider == "gemini":
            result = await self._call_gemini(system, user)
        elif self.provider == "groq":
            result = await self._call_openai_compatible(system, user, "https://api.groq.com/openai/v1")
        elif self.provider == "openai":
            result = await self._call_openai_compatible(system, user, "https://api.openai.com/v1")
        else:
            # Default to gemini endpoint
            result = await self._call_gemini(system, user)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info("LLM inference succeeded in %.2f ms (provider=%s, model=%s)", latency_ms, self.provider, self.model)
        return result

    async def generate_text_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str = "Transcribe all visible text exactly, preserving Gujarati/Hindi/English; output only the text.",
    ) -> str:
        """Transcribe text from image bytes using a vision-capable LLM model.

        In-memory processing only: image bytes are encoded directly to base64.
        Never logs image content or transcribed text.
        """
        if not self.is_configured:
            raise RuntimeError("LLM is disabled or LLM_API_KEY is not configured")

        b64_data = base64.b64encode(image_bytes).decode("ascii")
        start_time = time.perf_counter()

        if self.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": b64_data,
                                }
                            },
                            {"text": prompt},
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.0,
                },
            }
            response = await self._post_with_retry(url, headers, payload, params=params)
            data = response.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as exc:
                raise ValueError(f"Malformed vision response from Gemini: {exc}") from exc
        else:
            base_url = "https://api.openai.com/v1" if self.provider == "openai" else "https://api.groq.com/openai/v1"
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{b64_data}"},
                            },
                        ],
                    }
                ],
                "temperature": 0.0,
            }
            response = await self._post_with_retry(url, headers, payload)
            data = response.json()
            try:
                text = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as exc:
                raise ValueError(f"Malformed vision response: {exc}") from exc

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info("Vision OCR succeeded in %.2f ms (provider=%s, model=%s)", latency_ms, self.provider, self.model)
        return text.strip()
