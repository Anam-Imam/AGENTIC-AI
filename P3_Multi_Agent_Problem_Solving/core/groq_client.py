from __future__ import annotations

import os
from typing import Any, Iterable

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# Keep prompts comfortably below provider/request limits.  The app clips large
# agent reports before they are sent to the next agent, but this also protects
# one-off calls made elsewhere in the project.
MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", "14000"))


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Create a .env file from .env.example and add your key."
        )
    return Groq(api_key=api_key)


def _clip(value: Any, limit: int = MAX_MESSAGE_CHARS) -> Any:
    if not isinstance(value, str) or len(value) <= limit:
        return value
    head = max(1000, int(limit * 0.72))
    tail = max(400, limit - head - 80)
    return f"{value[:head]}\n\n[…context clipped…]\n\n{value[-tail:]}"


def normalize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for message in messages:
        item = dict(message)
        if "content" in item:
            item["content"] = _clip(item.get("content", ""))
        # Tool call argument payloads can become unexpectedly large. Keep them
        # valid while preventing a single tool call from creating a 413 request.
        if isinstance(item.get("tool_calls"), list):
            calls = []
            for call in item["tool_calls"]:
                call_copy = dict(call)
                fn = dict(call_copy.get("function", {}))
                fn["arguments"] = _clip(fn.get("arguments", ""), 6000)
                call_copy["function"] = fn
                calls.append(call_copy)
            item["tool_calls"] = calls
        normalized.append(item)
    return normalized


def chat(
    messages: list[dict[str, Any]],
    model: str | None = None,
    *,
    temperature: float = 0.3,
    max_completion_tokens: int = 1200,
    tools: list[dict[str, Any]] | None = None,
) -> Any:
    client = get_client()
    model_name = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    kwargs: dict[str, Any] = {
        "messages": normalize_messages(messages),
        "model": model_name,
        "temperature": temperature,
        "max_completion_tokens": max_completion_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return client.chat.completions.create(**kwargs)


def stream_chat(
    messages: list[dict[str, Any]],
    model: str | None = None,
    *,
    temperature: float = 0.3,
    max_completion_tokens: int = 1200,
) -> Iterable[str]:
    client = get_client()
    model_name = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    stream = client.chat.completions.create(
        messages=normalize_messages(messages),
        model=model_name,
        temperature=temperature,
        max_completion_tokens=max_completion_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta
