"""CLI script to verify and test the model adapter on sample texts."""

import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path so app imports work when executed directly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.modules.model_adapter.loader import load_model


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_model.py \"<text to analyze>\"")
        sys.exit(1)

    text = sys.argv[1]
    settings = get_settings()
    scorer, degraded = load_model(settings)

    print(f"Loaded scorer: {scorer.__class__.__name__}")
    print(f"Degraded flags: {degraded}")

    output = await scorer.score(text)
    print("\nModelOutput Result:")
    print(f"  available:     {output.available}")
    print(f"  score:         {output.score}")
    print(f"  top_words:     {output.top_words}")
    print(f"  calming_words: {output.calming_words}")
    print(f"  error:         {output.error}")


if __name__ == "__main__":
    asyncio.run(main())
