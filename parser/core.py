"""
The one implementation. CLI and HTTP are both thin adapters over
`parse_brief`. Nothing else is allowed to call the LLM directly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import ValidationError

from .llm_client import call_llm, LLMError
from .schema import Criteria

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extract_v1.txt"
COST_LOG_PATH = Path(__file__).resolve().parent.parent / "out" / "token_usage.jsonl"


class ParseError(RuntimeError):
    pass


def _load_prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _strip_code_fences(text: str) -> str:
    """Gemini with responseMimeType=json shouldn't add fences, but strip
    them defensively in case the model wraps output anyway."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _log_token_usage(brief_id: str, total_tokens: int) -> None:
    COST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {"brief_id": brief_id, "total_tokens": total_tokens}
    with COST_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def parse_brief(text: str, *, brief_id: str = "adhoc") -> dict:
    """Parse a raw hiring-brief string into a validated criteria dict.

    Raises ParseError if the LLM call fails or the response cannot be
    coerced into the Criteria schema -- callers (CLI/HTTP) decide how to
    surface that.
    """
    if not text or not text.strip():
        raise ParseError("Empty brief text.")

    template = _load_prompt_template()
    prompt = template.replace("{brief_text}", text.strip())

    try:
        raw_response, usage = call_llm(prompt)
    except LLMError as e:
        raise ParseError(f"LLM call failed: {e}") from e

    _log_token_usage(brief_id, usage.total)

    cleaned = _strip_code_fences(raw_response)

    try:
        parsed_json = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ParseError(f"Model did not return valid JSON: {e}\nRaw: {cleaned[:500]}") from e

    try:
        criteria = Criteria.model_validate(parsed_json)
    except ValidationError as e:
        raise ParseError(f"Model output failed schema validation: {e}") from e

    return criteria.model_dump()


def average_token_cost() -> float | None:
    """Average total_tokens across every logged call, or None if no calls
    have been logged yet."""
    if not COST_LOG_PATH.exists():
        return None
    totals = []
    with COST_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            totals.append(json.loads(line)["total_tokens"])
    if not totals:
        return None
    return sum(totals) / len(totals)
