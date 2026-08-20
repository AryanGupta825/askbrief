"""
eval.py -- proves the parser works, doesn't just assert it ran.

Design:
Each brief has a small set of hand-derived, source-grounded checks: things
that are either explicitly stated in the text (so getting them wrong is an
extraction bug) or explicitly ABSENT from the text (so inventing them is a
hallucination bug). This is not exhaustive field coverage -- it is a
targeted set chosen because each one maps to a specific behavior the task
brief calls out as being under test (correction handling, calibrated nulls,
must/preferred distinction, exclusions, code-mixed language).

Run:
    python eval.py

Exit code 0 = all checks passed. Non-zero = at least one failure, printed
with brief id, field, expected, actual.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

OUT_DIR = Path(__file__).resolve().parent / "out"


def _get(d: dict, path: str) -> Any:
    """Dotted-path getter, e.g. 'location.work_mode'."""
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _contains_ci(items: list[str] | None, needle: str) -> bool:
    if not items:
        return False
    needle = needle.lower()
    return any(needle in item.lower() for item in items)


Check = tuple[str, Callable[[dict], bool], str]  # (name, predicate, human description)


CHECKS: dict[str, list[Check]] = {
    "F01": [
        (
            "must_have_java_or_kotlin",
            lambda d: _contains_ci(d.get("must_have_skills"), "java")
            or _contains_ci(d.get("must_have_skills"), "kotlin"),
            "Java or Kotlin must appear in must_have_skills (explicit requirement)",
        ),
        (
            "must_have_kafka",
            lambda d: _contains_ci(d.get("must_have_skills"), "kafka"),
            "Kafka must appear in must_have_skills (explicit requirement)",
        ),
        (
            "work_mode_hybrid",
            lambda d: _get(d, "location.work_mode") == "hybrid",
            "work_mode must be 'hybrid' -- explicitly stated ('hybrid role, 3 days a week in office')",
        ),
        (
            "kubernetes_not_must_have",
            lambda d: not _contains_ci(d.get("must_have_skills"), "kubernetes"),
            "Kubernetes is listed under 'Nice to have' and must NOT be in must_have_skills",
        ),
    ],
    "F02": [
        (
            "exclusions_service_company",
            lambda d: bool(d.get("exclusions")),
            "exclusions must be non-empty -- brief explicitly rules out service company profiles",
        ),
        (
            "headcount_three",
            lambda d: d.get("headcount") == 3,
            "headcount must be 3 ('need 3 senior backend folks')",
        ),
        (
            "compensation_range_present",
            lambda d: _get(d, "compensation.min_lpa") is not None
            and _get(d, "compensation.max_lpa") is not None,
            "compensation min/max must be populated (explicit: '45-55 LPA')",
        ),
    ],
    "F03": [
        (
            "no_hallucinated_compensation",
            lambda d: _get(d, "compensation.min_lpa") is None
            and _get(d, "compensation.max_lpa") is None,
            "compensation must stay null -- nothing in the brief supports a number",
        ),
        (
            "no_hallucinated_location",
            lambda d: not _get(d, "location.cities"),
            "location.cities must stay empty -- no location mentioned",
        ),
        (
            "no_hallucinated_must_haves",
            lambda d: not d.get("must_have_skills"),
            "must_have_skills must stay empty -- brief names no specific skill",
        ),
        (
            "no_hallucinated_headcount",
            lambda d: d.get("headcount") is None,
            "headcount must stay null -- brief gives no number",
        ),
    ],
    "F04": [
        (
            "experience_uses_latest_correction",
            lambda d: _get(d, "experience.min_years") == 7,
            "min_years must be 7, not 5 -- brief self-corrects ('actually make that seven')",
        ),
        (
            "work_mode_not_hard_onsite",
            lambda d: _get(d, "location.work_mode") != "onsite",
            "work_mode must not be locked to onsite -- speaker says location flexibility is fine",
        ),
        (
            "go_present",
            lambda d: _contains_ci(d.get("must_have_skills"), "go")
            or _contains_ci(d.get("preferred_skills"), "go"),
            "Go must appear somewhere (must or preferred) -- explicitly mentioned as ideal",
        ),
    ],
    "F05": [
        (
            "python_is_must_have",
            lambda d: _contains_ci(d.get("must_have_skills"), "python"),
            "Python must be in must_have_skills ('Python must hai')",
        ),
        (
            "django_is_preferred_not_must",
            lambda d: _contains_ci(d.get("preferred_skills"), "django")
            and not _contains_ci(d.get("must_have_skills"), "django"),
            "Django must be preferred, not required ('Django hota toh accha rahega' = nice to have)",
        ),
        (
            "work_mode_onsite",
            lambda d: _get(d, "location.work_mode") == "onsite",
            "work_mode must be onsite -- explicitly rules out remote ('remote bilkul nahi')",
        ),
        (
            "city_pune",
            lambda d: _contains_ci(_get(d, "location.cities"), "pune"),
            "location.cities must include Pune",
        ),
    ],
}


def run() -> int:
    total = 0
    passed = 0
    failures: list[str] = []

    for brief_id, checks in CHECKS.items():
        out_path = OUT_DIR / f"{brief_id}.json"
        print(f"\n=== {brief_id} ===")

        if not out_path.exists():
            print(f"  MISSING: {out_path} not found -- run the parser on this brief first.")
            failures.append(f"{brief_id}: output file missing")
            total += len(checks)
            continue

        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  MISSING/INVALID JSON: {e}")
            failures.append(f"{brief_id}: invalid JSON output")
            total += len(checks)
            continue

        for name, predicate, description in checks:
            total += 1
            try:
                ok = predicate(data)
            except Exception as e:  # defensive: a bad shape shouldn't crash the whole run
                ok = False
                description = f"{description} [predicate raised {e!r}]"
            status = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            else:
                failures.append(f"{brief_id}.{name}: {description}")
            print(f"  [{status}] {name}: {description}")

    print(f"\n{passed}/{total} checks passed.")
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
