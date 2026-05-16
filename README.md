# aden-plugins

Personal Claude Code plugin marketplace by [@aden-ang-jj](https://github.com/aden-ang-jj).

## Plugins

| Plugin | Description |
|---|---|
| [`langfuse`](./plugins/langfuse) | Scaffolds a self-hosted [Langfuse v3](https://langfuse.com) docker-compose stack with strong secrets and optional admin/org provisioning. Skill: `/langfuse:self-host`. |

## Install

Inside Claude Code:

```
/plugin marketplace add aden-ang-jj/claude-plugins
/plugin install langfuse@aden-plugins
```

Then invoke any plugin's skills via their namespaced commands (e.g. `/langfuse:self-host`).

## Local development

To test changes before committing:

```
claude --plugin-dir ./plugins/langfuse
```

Then run `/langfuse:self-host` from within Claude Code. Iterate with `/reload-plugins`.

To validate the marketplace manifest:

```
claude plugin validate .
```

## License

MIT. See [LICENSE](./LICENSE).
