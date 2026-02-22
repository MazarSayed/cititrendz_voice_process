"""
Simple LLM client for structured extraction. Uses OpenAI with Pydantic output schema.
"""

from __future__ import annotations

import json
import os
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_client = None


def get_client():
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        from openai import OpenAI

        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        _client = OpenAI(api_key=key)
    return _client


def structured_extract(
    messages: list[dict[str, str]],
    schema: type[T],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
) -> T:
    """
    Call LLM with a full messages list and return parsed output matching the Pydantic schema.

    Args:
        messages: Full chat messages list (system + conversation history + extraction request).
        schema: Pydantic model class for structured output.
        model: OpenAI model name.
        temperature: Sampling temperature.

    Returns:
        Instance of schema with LLM output.
    """
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = (resp.choices[0].message.content or "{}").strip()
    data = json.loads(content)
    return schema.model_validate(data)
