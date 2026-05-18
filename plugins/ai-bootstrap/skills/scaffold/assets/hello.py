"""Smoke test — proves the provider, API key, and llm.py seam all work end-to-end.

Run with: `uv run hello.py`
"""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from config import settings  # noqa: E402  (must come after load_dotenv)
from llm import call_llm  # noqa: E402

logging.basicConfig(
    level=settings.log_level,
    format="%(levelname)s %(name)s: %(message)s",
)


def load_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / f"{name}.md").read_text().strip()


def main() -> None:
    system_prompt = load_prompt("system_default")

    print(f"Provider: {settings.llm_provider}")
    print(f"Model:    {settings.default_model_for(settings.llm_provider)}")
    print("---")

    response = call_llm(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Say hi in one sentence."},
        ],
    )

    print(response.text)
    print("---")
    print(
        f"Tokens: {response.prompt_tokens} in / {response.completion_tokens} out"
        f"  |  Latency: {response.latency_ms}ms"
        f"  |  Finish: {response.finish_reason}"
    )


if __name__ == "__main__":
    main()
