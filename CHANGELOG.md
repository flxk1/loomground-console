<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Changelog

Notable changes to loomground-console. Dates are ISO. Pre-1.0: the surface may change.

## [0.0.1] - 2026-08-12

First public cut — the terminal face of RVND, as its own repo (RVND stays a thin
orchestrator). A **client, not an engine**: it drives RVND's governance surface
over MCP; it holds no governance logic of its own.

### Added
- **home** — branded banner + command overview (dependency-free).
- **chat** — deterministic governance chat REPL: drives RVND's `governance_chat`
  over MCP, grounded in the workspace's versum. Slash-commands, inferred-intent
  echo, `/workspaces` + `/folder` picker. Verified live against a real RVND.
- **connect** — BYOK provider credentials in a local Fernet-encrypted store
  (`0600` key file); format + live validation. Ported from Brain's provider registry.
- **LLM phrasing (opt-in)** — with a connected provider, the LLM *phrases* RVND's
  deterministic result; it never routes or decides governance. `/llm` toggles;
  falls back to deterministic on any provider error.
- **board** / **workspaces** — ASCII dashboard (workspaces + security projection)
  and a workspace list, over RVND's own `workspace_workspace(list)` /
  `security_dashboard` ops (same ops the browser console uses).

### Notes
- Workspace selection lives in the app, not just the installer — driving RVND's
  own ops (one workflow, many surfaces).
- Roadmap: OAuth (API-key only today), the remaining workspace-lifecycle verbs
  (ingest/pin/govern/observe/seal/save), and a governance-topology `apply`.
