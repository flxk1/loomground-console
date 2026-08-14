<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# loomground-console

The **terminal face of [RVND](https://github.com/flxk1/RVND)** — a branded
first-run flow, a deterministic governance **chat**, an ASCII **dashboard**, and
optional bring-your-own-key LLM assist.

It is a **client, not an engine.** All governance logic lives in RVND; this
console drives RVND's surface over **MCP** — the same seam other clients use.
Nothing here re-implements the engine.

## Install

```bash
pip install -e '.[mcp,connect]'
```

## Use

```bash
loomground-console home            # commands overview
loomground-console workspaces      # the workspaces RVND knows
loomground-console board           # ASCII dashboard (workspaces + security)
loomground-console connect         # connect an LLM provider (BYOK) — optional
loomground-console chat            # deterministic governance chat, grounded in a workspace
```

Point it at your RVND install with `--rvnd-dir <dir>` (or `$RVND_DIR`); it
defaults to `~/rvnd`.

## How it works

- **Deterministic by default** — chat routes through RVND's governance engine
  (an audited intent router + dispatch). **No LLM** unless you `connect` your own
  provider (BYOK). When connected, the model only *phrases* RVND's result — it
  never routes or decides governance, and it falls back to the deterministic
  answer on any error.
- **Grounded** — each chat turn grounds in the workspace's own knowledge.
- **Credentials stay local** — provider keys are encrypted at rest (see
  [SECURITY.md](SECURITY.md)).
- RVND's browser console is the other face.

## Status

Early — `0.0.1`, pre-1.0, the surface may change. Working today: `home`, `chat`,
`connect`, `board`, `workspaces`. See [CHANGELOG.md](CHANGELOG.md).

## License

AGPL-3.0-only.
