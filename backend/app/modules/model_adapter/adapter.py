"""Concrete model adapter wrapping RukoModel with threadpool and timeout protection."""

import asyncio
import anyio
from typing import Any, List, Optional
from app.core.logging import logger
from app.modules.model_adapter.contract import ModelOutput, ScamScorer


class RealModelScorer(ScamScorer):
    """Wraps the underlying RukoModel with asynchronous execution, timeout, and safe degradation."""

    def __init__(self, model_instance: Any, timeout_seconds: float = 2.0) -> None:
        self.model = model_instance
        self.timeout_seconds = timeout_seconds

    @property
    def is_available(self) -> bool:
        return True

    def _predict_sync(self, text: str) -> ModelOutput:
        """Execute synchronous model prediction and extract strictly consumed fields."""
        check_res = self.model.check(text)

        raw_score = check_res.get("score")
        score: Optional[float] = float(raw_score) if raw_score is not None else None

        top_words: List[str] = list(check_res.get("words_that_raised_risk", []))
        calming_words: List[str] = list(check_res.get("words_that_lowered_risk", []))

        # Model's own internal verdict is explicitly ignored per architecture rules.
        return ModelOutput(
            available=True,
            score=score,
            top_words=top_words,
            calming_words=calming_words,
            error=None,
        )

    async def score(self, text: str) -> ModelOutput:
        """Score message text asynchronously with a 2-second timeout.

        Catches all exceptions and falls back safely to ModelOutput(available=False, error=...).
        Whitespace or empty text yields available=True, score=None.
        """
        if not text or not text.strip():
            return ModelOutput(
                available=True,
                score=None,
                top_words=[],
                calming_words=[],
                error=None,
            )

        try:
            return await asyncio.wait_for(
                anyio.to_thread.run_sync(self._predict_sync, text),
                timeout=self.timeout_seconds,
            )
        except (TimeoutError, asyncio.TimeoutError):
            logger.warning("Model scoring timed out after %.1fs", self.timeout_seconds)
            return ModelOutput(
                available=False,
                score=None,
                top_words=[],
                calming_words=[],
                error="model_timeout",
            )
        except Exception as exc:
            logger.warning("Model scoring failed: %s", str(exc))
            return ModelOutput(
                available=False,
                score=None,
                top_words=[],
                calming_words=[],
                error=str(exc),
            )
