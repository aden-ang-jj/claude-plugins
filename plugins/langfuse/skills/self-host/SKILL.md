---
description: Scaffolds a self-hosted Langfuse v3 stack (web, worker, Postgres, ClickHouse, Redis, MinIO) as a ready-to-run docker compose project. Use this skill whenever the user invokes /langfuse:self-host, or asks to set up / self-host / deploy / spin up / install Langfuse locally, or wants a docker-compose for LLM observability/tracing. Walks the user through optional auto-provisioning of the initial admin user, organization, and project, generates secure random secrets, and writes compose.yaml + .env to a chosen directory.
---

# Langfuse self-hosting scaffolder

This skill produces a working `compose.yaml` + `.env` for a self-hosted **Langfuse v3** instance and (optionally) starts it. The compose is taken verbatim from Langfuse's upstream repo so it stays in sync with their supported configuration; the skill's job is to generate strong secrets and a tailored `.env`, and to walk the user through a small set of decisions.

## Why this design

- **Compose is upstream-shaped.** The reference compose at `assets/compose.yaml` matches `langfuse/langfuse@main/docker-compose.yml`. Every value is read from env via `${VAR:-default}`. The skill never needs to template the YAML itself — it just writes a `.env` next to it. When Langfuse ships breaking changes, only `assets/compose.yaml` needs updating.
- **Projects are created in the UI, not headlessly.** Langfuse's headless project init requires you to pre-supply public+secret API keys, and this skill deliberately doesn't pre-generate keys (they should be created via the UI after first login, where Langfuse generates them properly). So the skill doesn't even ask about project init — the user creates their first project (and its API keys) in the UI.
- **Init user/org are opt-in.** `LANGFUSE_INIT_*` env vars let Langfuse auto-create an admin user and an organization on first boot. The skill asks; if the user skips, they just sign up via the UI like a fresh install.
- **Signup auto-locks when an init user is set.** If the user provisions an admin via init env vars, the skill also sets `AUTH_DISABLE_SIGNUP=true` so the only account that can exist on this instance is the one that was provisioned. This was the user's explicit preference.

## Workflow

Execute these steps in order. Do not skip the interactive questions — they are the entire reason this skill exists.

### Step 1 — Confirm target directory and port

Use `AskUserQuestion` to gather:

1. **Target directory** for the compose stack. Default: `./langfuse` (relative to the user's current working directory). If the directory already exists and contains files, ask whether to overwrite or pick a different path. Don't silently clobber.
2. **Web port** for the Langfuse UI. Default: `3000`. This becomes `NEXTAUTH_URL=http://localhost:<port>` and the host-side port mapping.

Keep this question batch small (these two are infrastructure-level — separate from identity).

### Step 2 — Ask about initial provisioning

Use a second `AskUserQuestion` round for the identity bits. The user can skip any of these.

1. **Initialize an admin user?** If yes, ask for: email, display name, password. Validate: email contains `@`; password is at least 8 chars. If skipped, the user signs up via UI.
2. **Initialize an organization?** If yes, ask for org name. The skill generates a random UUID for `LANGFUSE_INIT_ORG_ID`. If skipped, the user creates one in the UI.

Do **not** ask about initializing a project — Langfuse's headless project init requires pre-supplied API keys, which this skill doesn't generate. The user creates their first project (and its keys) via the UI after login.

Practical hint: don't ask about org if the user already opted out of admin user — Langfuse's init has no one to attach the org to.

### Step 3 — Generate secrets

Run via Bash:

```
openssl rand -hex 32   # one each for: NEXTAUTH_SECRET, SALT, ENCRYPTION_KEY
openssl rand -base64 24 | tr -d '=+/'   # one each for: POSTGRES_PASSWORD, CLICKHOUSE_PASSWORD, REDIS_AUTH, MINIO_ROOT_PASSWORD
```

Generate them in a single Bash call (7 values) to keep it fast. Capture the output and use it to populate the `.env` template.

UUIDs for org/project (if needed):

```
uuidgen | tr '[:upper:]' '[:lower:]'
```

### Step 4 — Write the files

When this skill runs inside the installed plugin, asset paths are resolved relative to the skill's own directory. Use `${CLAUDE_PLUGIN_ROOT}/skills/self-host/assets/compose.yaml` and `…/env.template` to find the templates, since the plugin is copied to a cache location at install time.

1. Read `assets/compose.yaml` from the skill directory and write it verbatim to `<target>/compose.yaml`. No substitution. The compose is self-contained and reads everything from env.
2. Read `assets/env.template` from the skill directory. Substitute every `{{PLACEHOLDER}}` with the generated value or user input (see "env.template variables" below). Write to `<target>/.env`.
3. Write `<target>/.gitignore` with the single line `.env` so the secrets file is never committed by accident.

### env.template variables

These are the placeholders that need filling. If a value is empty/unset, leave the placeholder line as `KEY=` (Langfuse falls back to compose defaults, which are safe for empty optional inits but NOT for passwords — passwords must always be filled).

| Placeholder | Source | Required |
|---|---|---|
| `{{NEXTAUTH_URL}}` | `http://localhost:<port>` from step 1 | yes |
| `{{NEXTAUTH_SECRET}}` | openssl hex 32 | yes |
| `{{SALT}}` | openssl hex 32 | yes |
| `{{ENCRYPTION_KEY}}` | openssl hex 32 | yes |
| `{{POSTGRES_PASSWORD}}` | openssl base64 | yes |
| `{{DATABASE_URL}}` | `postgresql://postgres:<postgres_password>@postgres:5432/postgres` (must reflect above) | yes |
| `{{CLICKHOUSE_PASSWORD}}` | openssl base64 | yes |
| `{{REDIS_AUTH}}` | openssl base64 | yes |
| `{{MINIO_ROOT_PASSWORD}}` | openssl base64 (reused as S3 secret access key — see below) | yes |
| `{{LANGFUSE_INIT_USER_EMAIL}}` | user input or empty | optional |
| `{{LANGFUSE_INIT_USER_NAME}}` | user input or empty | optional |
| `{{LANGFUSE_INIT_USER_PASSWORD}}` | user input or empty | optional |
| `{{LANGFUSE_INIT_ORG_ID}}` | uuidgen or empty | optional |
| `{{LANGFUSE_INIT_ORG_NAME}}` | user input or empty | optional |
| `{{AUTH_DISABLE_SIGNUP}}` | `true` if init user was provided, else `false` | yes |

The MinIO password is reused for all three `LANGFUSE_S3_*_SECRET_ACCESS_KEY` env vars (event/media/batch-export) because all three buckets live in the same MinIO instance. The compose's defaults for `*_ACCESS_KEY_ID` (`minio`) are fine and don't need to be overridden.

### Step 5 — Offer to start the stack

Use `AskUserQuestion` with three options: start now, skip and print instructions, or cancel. If user picks "start", run:

```
cd <target> && docker compose up -d
```

Then tail `docker compose logs -f langfuse-web` in the background for a moment to confirm it boots (the langfuse-web container takes 2-3 minutes to apply migrations and log "Ready"). If the user picks "skip", print the one-liner they need to run.

### Step 6 — Print next steps

A short, copy-pasteable summary:

- URL: `http://localhost:<port>`
- Login: if init user was set, show the email; otherwise say "sign up via the UI on first visit"
- Where to get API keys: "In the UI → your project → Settings → API Keys → Create new keys"
- MinIO console (if user is curious): `http://localhost:9091` with the minio creds
- Stopping: `cd <target> && docker compose down` (preserves data) or `docker compose down -v` (wipes volumes)

## When something goes sideways

- **`docker compose up` fails with port conflict on 3000:** rerun with a different web port (Step 1).
- **`docker compose up` fails with port conflict on 9090/9091/5432/6379/8123/9000:** these are MinIO, MinIO console, Postgres, Redis, ClickHouse HTTP, ClickHouse native. The upstream compose binds the latter five to `127.0.0.1` only, so conflicts there mean another local service is using them. The skill should NOT silently remap; tell the user and let them stop the conflicting service.
- **langfuse-web container is unhealthy after 5+ minutes:** look at `docker compose logs langfuse-web` for migration errors. Most common cause is a stale volume from a previous half-broken install — `docker compose down -v` and retry.

## Files in this skill

- `SKILL.md` — this file.
- `assets/compose.yaml` — verbatim upstream Langfuse compose. Update when upstream changes.
- `assets/env.template` — `.env` file with placeholders to substitute in Step 4.
