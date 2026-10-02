"""Model adapter contracts and schemas."""

from typing import List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class ModelOutput(BaseModel):
    """Normalized output from the ML scam classification model."""

    available: bool = Field(..., description="Whether model inference succeeded")
    score: Optional[float] = Field(None, description="Scam probability score from 0.0 to 1.0, or None")
    top_words: List[str] = Field(default_factory=list, description="Words that raised the risk score")
    calming_words: List[str] = Field(default_factory=list, description="Words that lowered the risk score")
    error: Optional[str] = Field(None, description="Error message if inference failed or timed out")


@runtime_checkable
class ScamScorer(Protocol):
    """Protocol interface for scam prediction scoring."""

    async def score(self, text: str) -> ModelOutput:
        """Score message text asynchronously with timeout protection."""
        ...
