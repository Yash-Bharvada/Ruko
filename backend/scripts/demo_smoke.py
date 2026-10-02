"""Demo smoke test script for hackathon live presentations."""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Reconfigure stdout to utf-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.routes_check import run_check
from app.core.config import Settings


def load_demo_cases() -> List[Dict[str, Any]]:
    """Load the 10 representative demo cases from data/demo_cases.json."""
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "demo_cases.json",
        Path.cwd() / "data" / "demo_cases.json",
        Path.cwd() / "backend" / "data" / "demo_cases.json",
    ]
    for c in candidates:
        if c.is_file():
            with open(c, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("data/demo_cases.json not found")


async def run_smoke_test() -> bool:
    """Run all demo cases through Ruko backend pipeline and display formatted demo results."""
    cases = load_demo_cases()
    settings = Settings()

    print("\n" + "=" * 80)
    print(" RUKO INVESTOR PROTECTION BACKEND — DEMO SMOKE TEST")
    print(f" Executing {len(cases)} Curated Scenarios Across Gujarati, Hindi & English")
    print("=" * 80 + "\n")

    all_passed = True

    for i, case in enumerate(cases, 1):
        start = time.perf_counter()
        result = await run_check(
            text=case["text"],
            language_hint=case.get("language"),
            amount=case.get("amount"),
            settings=settings,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        is_match = result.verdict == case["expected_verdict"]
        if not is_match:
            all_passed = False

        status_tag = "[PASS]" if is_match else "[FAIL]"

        print(f"CASE {i:02d}: {case['title']}")
        print(f"  Category : {case['category']} (Lang: {result.language})")
        preview = case['text'].replace('\n', ' ')
        if len(preview) > 75:
            preview = preview[:72] + "..."
        print(f"  Input    : \"{preview}\"")
        print(f"  Verdict  : {result.verdict.upper()} (Score: {result.score:.2f}) {status_tag} in {elapsed_ms:.1f}ms")

        if result.reasons:
            print("  Red Flags:")
            for r in result.reasons[:3]:
                print(f"    - [{r.severity.upper()}] {r.code}: \"{r.evidence}\"")

        print(f"  Summary  : {result.note}")
        print("-" * 80)

    print("\n" + "=" * 80)
    if all_passed:
        print(f" DEMO SMOKE TEST COMPLETED SUCCESSFULLY: {len(cases)}/{len(cases)} CASES PASSED")
    else:
        print(f" DEMO SMOKE TEST FAILED: Discrepancy detected in demo cases")
    print("=" * 80 + "\n")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_smoke_test())
    sys.exit(0 if success else 1)
