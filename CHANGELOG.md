<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Changelog

Notable changes to loomground-console. Dates are ISO. Pre-1.0: the surface may change.

## [0.0.1] - 2026-08-12

First public cut — the terminal face of host, as its own repo (host stays a thin
orchestrator). A **client, not an engine**: it drives host's governance surface
over MCP; it holds no governance logic of its own.

### Added
- **home** — branded banner + command overview (dependency-free).
- **chat** — deterministic governance chat REPL: drives host's `governance_chat`
  over MCP, grounded in the workspace's versum. Slash-commands, inferred-intent
  echo, `/workspaces` + `/folder` picker. Verified live against a real host.
- **connect** — BYOK provider credentials in a local Fernet-encrypted store
  (`0600` key file); format + live validation.
- **LLM phrasing (opt-in)** — with a connected provider, the LLM *phrases* host's
  deterministic result; it never routes or decides governance. `/llm` toggles;
  falls back to deterministic on any provider error.
- **board** / **workspaces** — ASCII dashboard (workspaces + security projection)
  and a workspace list, over host's own `workspace_workspace(list)` /
  `security_dashboard` ops (same ops the browser console uses).

### Notes
- Workspace selection lives in the app, not just the installer — driving host's
  own ops (one workflow, many surfaces).
- Roadmap: OAuth (API-key only today), the remaining workspace-lifecycle verbs
  (ingest/pin/govern/observe/seal/save), and a governance-topology `apply`.
