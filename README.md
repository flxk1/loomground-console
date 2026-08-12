<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# loomground-console

The **terminal face of RVND** — a branded install/wizard flow, a deterministic
governance **chat REPL** grounded in the user's versum, and **ASCII dashboards**.

It is a **client, not an engine.** All governance logic stays in
[RVND](https://github.com/flxk1/RVND) (the thin orchestrator); this console
drives RVND's existing surface over **MCP** — the same seam Claude Code, Codex,
and the browser console already use. Nothing here re-implements the engine.

- **Deterministic by default** — chat routes through RVND's `governance_chat`
  (intent router + audited dispatch). **No LLM** unless you `connect` your own
  provider (BYOK API key / OAuth); then the same chat becomes LLM-assisted.
- **Grounded in your versum** — each chat turn grounds in the workspace's
  `.versum` knowledge via RVND's `ask_workspace`.
- **The browser console** (RVND `app/serve.py`) remains the other face.

## Status
- **P1 — home + command overview** ✅ (this scaffold): `loomground-console home`.
- **P2 — chat REPL** (next): deterministic, versum-grounded, MCP client of RVND.
- **P3 — `connect`** (BYOK provider credentials, ported from Brain `user_credentials.py`).
- **P4 — LLM opt-in**; **P5 — versum-locate wizard step**; **P6 — ASCII `board`**.

See the program plan in the Loomground `work/` tree.

## Run
```bash
python -m loomground_console home
```

## License
AGPL-3.0-only (matching RVND, the application it fronts).
