"""Dummy scorer used when model is unavailable or disabled."""

from app.modules.model_adapter.contract import ModelOutput, ScamScorer


class DummyScorer(ScamScorer):
    """Fallback scorer when the model package is missing, unloadable, or degraded.

    Guaranteed to NEVER fake a score or make up numbers.
    """

    @property
    def is_available(self) -> bool:
        return False

    async def score(self, text: str) -> ModelOutput:
        """Always returns unavailable with score=None."""
        return ModelOutput(
            available=False,
            score=None,
            top_words=[],
            calming_words=[],
            error=None,
        )
