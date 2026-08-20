"""
Minimal wrapper around a cloud LLM call.

Uses Google's Gemini API (REST) because it has a free tier and needs only
an API key, no SDK-specific account setup. Swap-friendly: everything the
rest of the codebase needs is `call_llm(prompt: str) -> tuple[str, TokenUsage]`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv()  # picks up .env in the working directory if present

GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


class LLMError(RuntimeError):
    pass


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def call_llm(prompt: str, *, temperature: float = 0.0) -> tuple[str, TokenUsage]:
    """Send `prompt` to Gemini, return (raw_text_response, token_usage).

    Raises LLMError on missing key / non-200 response / malformed response
    shape, so callers can decide how to surface the failure instead of this
    module silently returning garbage.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise LLMError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }

    resp = requests.post(
        GEMINI_URL,
        params={"key": api_key},
        json=body,
        timeout=60,
    )
    if resp.status_code != 200:
        raise LLMError(f"Gemini API error {resp.status_code}: {resp.text[:500]}")

    data = resp.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Gemini response shape: {json.dumps(data)[:500]}") from e

    usage = data.get("usageMetadata", {})
    token_usage = TokenUsage(
        prompt_tokens=usage.get("promptTokenCount", 0),
        completion_tokens=usage.get("candidatesTokenCount", 0),
    )
    return text, token_usage
