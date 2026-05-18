---
description: Scaffolds a production-shaped Python AI project with multi-provider LLM support (OpenAI, OpenRouter, DeepInfra) using the OpenAI SDK pattern. Use this skill whenever the user invokes /ai-bootstrap:scaffold, or asks to bootstrap / scaffold / set up / start a new AI project / LLM project / Python AI app, or wants a starter for an OpenAI / OpenRouter / DeepInfra app with a clean swap-seam between providers. Generates pyproject.toml + .env + a typed config + an LLM client wrapper + a hello-world smoke test, all wired to uv. No Langfuse or other observability tooling — that lives in a separate skill so this stays focused.
---

# AI project scaffolder (Python)

This skill produces a small, opinionated starting point for a Python AI app: a `uv`-managed project with a Pydantic-validated config, a single `llm.py` seam that every LLM call flows through, and a `hello.py` smoke test. Three providers are pre-wired (OpenAI, OpenRouter, DeepInfra) and the user picks which one is active. The shape is production-ready, not toy — the user can grow the project on top of it without rewriting the foundation.

## Why this design

- **One seam, many providers.** Every LLM call goes through `call_llm()` / `stream_llm()` in `llm.py`. Every call goes through this seam, which is what makes future swaps cheap — caching, tracing, retries, or a provider change are one-file edits instead of grep-and-replace across call sites.
- **OpenAI SDK for everything.** OpenAI, OpenRouter, and DeepInfra all speak the OpenAI Chat Completions API. The scaffold uses the `openai` Python SDK and switches providers via `base_url` + a different API key. No multi-SDK juggling, no LiteLLM-style abstraction layer to learn. Anthropic models are reachable through OpenRouter (`model="anthropic/claude-opus-4"`) using the same code path.
- **Config is typed and validated at startup.** `config.py` uses `pydantic-settings` so missing/misnamed env vars fail loudly with a clear message rather than crashing deep inside a request. The user knows immediately if their `.env` is wrong.
- **Production-shaped, not over-engineered.** The wrapper returns a typed `LLMResponse` (text + tokens + latency + finish reason), uses module-level logging, supports streaming, and wraps provider errors in a single `LLMError`. But it stops short of adding caches/queues/agents — those are *application* concerns, not bootstrap concerns.
- **Assets are templated, not generated.** Substantive files live in `assets/` so updating the scaffold output means editing real Python you can lint and run, not Python-inside-an-f-string.
- **No Langfuse / tracing here.** The langfuse plugin owns that domain. Bundling it into this skill would couple two independent concerns; keeping them separate means each can evolve on its own and either can be used alone.

## Workflow

Execute these steps in order. Don't skip the interactive questions — they shape the output.

### Step 1 — Confirm target directory and project name

Use `AskUserQuestion` to gather:

1. **Target directory** for the project. Default: `./ai-app` (relative to the user's current working directory). If the directory already exists and contains files, ask whether to overwrite or pick a different path. Don't silently clobber — the user may have unrelated work there.

The **project name** is derived from the basename of the target directory (e.g. `./ai-app` → `ai-app`). Normalize to a valid Python package-style name (lowercase, hyphens or underscores only). If the derivation produces something awkward (e.g. `./My Project!` → `my-project`), tell the user what you used; only ask explicitly if the basename is unusable (empty, all special chars).

### Step 2 — Ask which provider is the default

Use a second `AskUserQuestion` round. The user picks **one** provider that becomes the active `LLM_PROVIDER` in `.env`. The other two are still pre-wired in `config.py` and present (commented as "fill if using") in `.env`, so switching later is one line.

Offer these three options:

| Provider | When it's the right default |
|---|---|
| `openrouter` | The user wants one API key that routes to many models (OpenAI, Anthropic, DeepSeek, Llama, etc.). Best for prototyping and A/B testing models. |
| `openai` | The user is committed to GPT-family models and wants the lowest-latency, first-party path. |
| `deepinfra` | The user wants cheap hosted open-source models (Llama, Mixtral, Qwen, DeepSeek-V3) and is fine with a single host. |

If the user has no strong preference, recommend `openrouter` — the flexibility makes the early prototyping phase much smoother.

### Step 3 — Pre-flight check for `uv`

Before writing any files, run `command -v uv` via Bash. If `uv` is not installed:

- Print the install hint: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Stop the workflow. Do not write files yet — leaving a half-scaffolded directory the user can't run is worse than telling them to install `uv` and re-invoke.
- Do not auto-install package managers without explicit consent. The user runs the install command themselves.

If `uv` is present, proceed to Step 4.

### Step 4 — Generate files

When this skill runs inside the installed plugin, asset paths are resolved relative to the skill's own directory. Use `${CLAUDE_PLUGIN_ROOT}/skills/scaffold/assets/` as the base for all templates, since the plugin is copied to a cache location at install time.

Read each file from `assets/`, substitute placeholders per the table below, and write into the target directory. Group all writes into one batch so the user sees "wrote N files" rather than a stream.

| Source asset | Destination | Substitutions | Notes |
|---|---|---|---|
| `pyproject.toml.template` | `<target>/pyproject.toml` | `{{PROJECT_NAME}}` | |
| `python-version` | `<target>/.python-version` | — | Pins Python version for `uv`. |
| `env.template` | `<target>/.env` | `{{DEFAULT_PROVIDER}}` | Secrets. Empty `*_API_KEY` lines; user fills before running. |
| `env.example.template` | `<target>/.env.example` | `{{DEFAULT_PROVIDER}}` | Safe to commit — no real keys. |
| `gitignore.template` | `<target>/.gitignore` | — | Critically includes `.env`. |
| `config.py` | `<target>/config.py` | — | |
| `llm.py` | `<target>/llm.py` | — | |
| `hello.py` | `<target>/hello.py` | — | |
| `prompts/system_default.md` | `<target>/prompts/system_default.md` | — | Establishes the "prompts are files" convention. |
| `README.md.template` | `<target>/README.md` | `{{PROJECT_NAME}}`, `{{DEFAULT_PROVIDER}}` | |

### Step 5 — Install dependencies

Run via Bash inside the target directory:

```
cd <target> && uv sync
```

This creates `.venv/`, resolves the dependency graph, and writes `uv.lock`. The user can `uv run hello.py` immediately after they've added their API key.

### Step 6 — Print next steps

A short, copy-pasteable summary:

- **Add your API key:** open `<target>/.env` and paste your `<PROVIDER>_API_KEY=...` value on the matching line.
- **Run the smoke test:** `cd <target> && uv run hello.py`
- **Switch providers later:** edit `LLM_PROVIDER` in `.env` (and fill the matching `*_API_KEY`).
- **Use other models on the same provider:** pass `model=...` to `call_llm()`, or set `LLM_DEFAULT_MODEL` in `.env`.
- **Need Anthropic / Claude?** Use OpenRouter with `model="anthropic/claude-opus-4"` — same code, no new SDK.
- **Add a fourth provider:** extend `ProviderConfig.PROVIDERS` in `config.py` and add the corresponding `*_API_KEY` to `.env` and `.env.example`.

Do not run `hello.py` automatically. The user hasn't pasted a key yet, and spending money on the user's API account without explicit go-ahead is exactly the kind of action this skill should avoid by default.

## env.template variables

| Placeholder | Source | Notes |
|---|---|---|
| `{{DEFAULT_PROVIDER}}` | Step 2 selection | One of `openai`, `openrouter`, `deepinfra`. Written as `LLM_PROVIDER=<value>`. |
| `{{PROJECT_NAME}}` | Step 1 derivation | Used in `pyproject.toml` and `README.md`. |

## When something goes sideways

- **`uv sync` fails on Python version:** the user's machine doesn't have the pinned Python version available. Suggest `uv python install` to fetch it.
- **The target directory exists and is non-empty:** ask whether to overwrite specific files or pick a new path. Never `rm -rf` an existing directory.
- **The target dir contains an existing `pyproject.toml`:** treat as the "exists and non-empty" case. Don't merge into someone else's `pyproject.toml`.
- **`uv sync` succeeds but `uv run hello.py` fails with a 401 / auth error:** the user's API key is missing or wrong. Point them at `.env` and the provider's dashboard for getting a fresh key.

## Files in this skill

- `SKILL.md` — this file.
- `assets/pyproject.toml.template` — `pyproject.toml` with `{{PROJECT_NAME}}` placeholder.
- `assets/python-version` — pinned Python version string.
- `assets/env.template` — `.env` with `{{DEFAULT_PROVIDER}}` placeholder; API key lines are empty.
- `assets/env.example.template` — committed-safe `.env.example` with `{{DEFAULT_PROVIDER}}` placeholder.
- `assets/gitignore.template` — static `.gitignore`.
- `assets/config.py` — typed settings module (Pydantic + provider metadata).
- `assets/llm.py` — single seam for all LLM calls (sync + streaming + typed response + error wrapping).
- `assets/hello.py` — smoke test exercising the seam end-to-end.
- `assets/prompts/system_default.md` — example file prompt to establish the convention.
- `assets/README.md.template` — generated project README with `{{PROJECT_NAME}}` and `{{DEFAULT_PROVIDER}}` placeholders.
