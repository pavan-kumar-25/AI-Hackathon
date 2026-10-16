"""NeoStats Azure OpenAI client (same pattern as sample_open_ai_wrapper.py)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from openai import OpenAI

from config import (
    AZURE_OPENAI_BASE_URL,
    AZURE_OPENAI_DEPLOYMENT,
    require_api_key,
)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(
        base_url=AZURE_OPENAI_BASE_URL,
        api_key=require_api_key(),
    )


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict | None = "auto",
    temperature: float = 0.2,
) -> Any:
    kwargs: dict[str, Any] = {
        "model": AZURE_OPENAI_DEPLOYMENT,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
    return get_client().chat.completions.create(**kwargs)
