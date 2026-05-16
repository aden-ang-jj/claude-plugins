# langfuse

A Claude Code plugin that scaffolds a self-hosted [Langfuse v3](https://langfuse.com) stack as a ready-to-run `compose.yaml` + `.env`.

## What it does

Invoke `/langfuse:self-host` (or ask Claude to "set up Langfuse self-hosted") and the skill will:

1. Ask you for a target directory, web port, and optional admin user / organization.
2. Generate strong random secrets for every component (Postgres, ClickHouse, Redis, MinIO, NextAuth, salt, encryption key).
3. Write `compose.yaml` + `.env` + `.gitignore` into the target directory.
4. Optionally run `docker compose up -d` for you.

The compose itself is taken verbatim from [Langfuse's upstream repo](https://github.com/langfuse/langfuse/blob/main/docker-compose.yml) so the plugin stays compatible as Langfuse evolves; the plugin's contribution is the interactive flow and the tailored `.env`.

## Install

```
/plugin marketplace add aden-ang-jj/claude-plugins
/plugin install langfuse@aden-plugins
```

Then run `/langfuse:self-host` from Claude Code.

## Skills

| Skill | Trigger | What it does |
|---|---|---|
| `self-host` | `/langfuse:self-host` | Generates `compose.yaml` + `.env` for a local Langfuse v3 stack and optionally starts it. |

## Design choices

- **API keys are NOT pre-generated.** You create your project's public/secret keys via the Langfuse UI after first login. This is the secure default. If you need API keys available to downstream tooling before the UI is up, this plugin isn't the right fit.
- **Init user/org are opt-in.** If you provide an admin email/name/password, the plugin also sets `AUTH_DISABLE_SIGNUP=true` so nobody else can sign up. If you skip, you'll sign up via the UI like a fresh install.
- **One Langfuse stack per directory.** The default target is `./langfuse/` to keep it self-contained and out of the way of any other compose in the same project.

## Requirements

- Docker + Docker Compose v2 (Docker Desktop, OrbStack, or Colima all work)
- `openssl` and `uuidgen` (preinstalled on macOS and most Linux distros)

## Production note

This plugin is for **local development and small self-hosted deployments**. It runs Postgres, ClickHouse, and MinIO as single-replica containers with local volumes — fine for a laptop or a single VPS, but not a production-grade setup. For production, you'd want:

- Reverse proxy with TLS (Caddy, nginx)
- Managed Postgres + ClickHouse (or properly clustered self-hosted)
- Real S3 (or R2, GCS) instead of MinIO
- SMTP for password reset / invites
- Secrets in a vault, not `.env` on disk

## License

MIT. See [LICENSE](../../LICENSE) at the repo root.
