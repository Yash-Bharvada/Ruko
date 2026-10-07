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


async def run_explain_demo_docs() -> bool:
    """Run synthetic demo documents through the Explain a Document pipeline."""
    from app.modules.docexplain import explain_document

    docs_dir = Path(__file__).resolve().parent.parent / "data" / "demo_docs"
    demo_files = [
        ("English Loan Agreement", docs_dir / "loan_agreement.txt", "en"),
        ("Hindi Health Insurance Policy", docs_dir / "insurance_clause.txt", "hi"),
        ("Gujarati Rental Agreement", docs_dir / "rental_agreement.txt", "gu"),
    ]

    print("\n" + "=" * 80)
    print(" RUKO EXPLAIN A DOCUMENT — DEMO WALKTHROUGH")
    print(f" Explaining {len(demo_files)} Synthetic Legal/Financial Documents")
    print("=" * 80 + "\n")

    all_ok = True
    for title, path, lang in demo_files:
        if not path.is_file():
            continue
        with open(path, "r", encoding="utf-8") as f:
            doc_text = f.read()

        start = time.perf_counter()
        exp = await explain_document(
            plain_text=doc_text,
            language=lang,
            include_storyboard=True,
            crosscheck=True,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        print(f"DOCUMENT: {title} (Lang: {exp.language}, Type: {exp.doc_type_guess}) in {elapsed_ms:.1f}ms")
        print(f"  Summary    : {exp.summary[:100]}...")
        print(f"  Key Points : {len(exp.key_points)} takeaways grounded")
        print(f"  Steps      : {len(exp.steps)} action steps")
        print(f"  Storyboard : {len(exp.storyboard)} browser scenes generated & signed")
        if exp.storyboard:
            print(f"  Sample Scene 1 Narration : \"{exp.storyboard[0].narration[:80]}...\"")
        print("-" * 80)

    return all_ok


async def run_smoke_test() -> bool:
    """Run all demo cases and demo docs through Ruko backend pipeline."""
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

    # Run doc explain demo
    await run_explain_demo_docs()

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
