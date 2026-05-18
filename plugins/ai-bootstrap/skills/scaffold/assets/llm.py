"""Single seam for every LLM call in the app.

All call sites use call_llm() / stream_llm(). New cross-cutting concerns
(caching, tracing, retries, rate limiting) get added here, not at the
call sites — that's the whole point of routing every call through one
module.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from openai import OpenAI, OpenAIError

from config import settings

log = logging.getLogger(__name__)

Message = dict[str, Any]


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    finish_reason: str


class LLMError(RuntimeError):
    """Unified error type wrapping provider-specific exceptions."""


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazily build a singleton OpenAI client. Reuses HTTP connections across calls."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.api_key_for(settings.llm_provider),
            base_url=settings.base_url_for(settings.llm_provider),
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    return _client


def call_llm(
    messages: list[Message],
    model: str | None = None,
    **opts: Any,
) -> LLMResponse:
    """Send a non-streaming chat completion request and return a typed response."""
    client = _get_client()
    chosen_model = model or settings.default_model_for(settings.llm_provider)
    started = time.monotonic()

    try:
        response = client.chat.completions.create(
            model=chosen_model,
            messages=messages,
            **opts,
        )
    except OpenAIError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        log.error(
            "LLM call failed",
            extra={"model": chosen_model, "latency_ms": latency_ms, "error": str(exc)},
        )
        raise LLMError(str(exc)) from exc

    latency_ms = int((time.monotonic() - started) * 1000)
    choice = response.choices[0]
    usage = response.usage

    result = LLMResponse(
        text=choice.message.content or "",
        model=response.model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        latency_ms=latency_ms,
        finish_reason=choice.finish_reason or "",
    )
    log.info(
        "LLM call ok",
        extra={
            "model": result.model,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "latency_ms": result.latency_ms,
        },
    )
    return result


def stream_llm(
    messages: list[Message],
    model: str | None = None,
    **opts: Any,
) -> Iterator[str]:
    """Stream chat completion deltas as text fragments.

    Useful for chat UIs where you want text to appear as the model generates it.
    """
    client = _get_client()
    chosen_model = model or settings.default_model_for(settings.llm_provider)

    try:
        stream = client.chat.completions.create(
            model=chosen_model,
            messages=messages,
            stream=True,
            **opts,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except OpenAIError as exc:
        log.error("LLM stream failed", extra={"model": chosen_model, "error": str(exc)})
        raise LLMError(str(exc)) from exc
