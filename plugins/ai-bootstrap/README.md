# ai-bootstrap

Scaffolds a small, production-shaped Python AI project with multi-provider LLM support — OpenAI, OpenRouter, and DeepInfra — using the OpenAI SDK pattern.

## Skill

- `/ai-bootstrap:scaffold` — interactive scaffolder. Asks for a target directory and a default provider, then generates a `uv`-managed project with a typed config, an `LLMClient` seam, a smoke test, and a prompts folder.

## What you get

```
ai-app/
├── pyproject.toml          # uv-managed deps
├── .python-version
├── .env                    # secrets (gitignored)
├── .env.example            # committed contract
├── .gitignore
├── config.py               # Pydantic settings + provider metadata
├── llm.py                  # single seam: call_llm() + stream_llm()
├── hello.py                # smoke test
├── prompts/
│   └── system_default.md
└── README.md
```

After scaffolding:

```sh
cd ai-app
# paste your API key into .env
uv run hello.py
```

## Why these three providers

- **OpenAI** — GPT-family direct.
- **OpenRouter** — one key, ~300 models (Anthropic, DeepSeek, Llama, Mistral, …). Easy A/B testing.
- **DeepInfra** — cheap hosted open-source models.

All three speak the OpenAI Chat Completions API, so the scaffold uses one SDK and switches providers by `base_url`. Adding a fourth OpenAI-compatible provider is ~5 lines in `config.py`.

## What this plugin intentionally doesn't include

- Observability / tracing → use the `langfuse` plugin.
- Web framework, RAG, agents → application concerns, not bootstrap concerns.
