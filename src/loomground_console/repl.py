# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""The deterministic governance chat REPL.

Drives RVND's `governance_chat` over MCP, grounded in the workspace's versum.
**No LLM** — that arrives with `connect` (a later phase). Shell shaped after
Brain's `cmd_repl`: readline history, slash-commands, an inferred-intent echo
(so a wrong route is visible + correctable), and the result + audit id.

Turn/formatting logic is kept pure (`render_turn`, `parse_command`) so it is
unit-tested without a live RVND; only `run()` needs the server.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional

# governance_chat returns {"intent", "echo", "kind", "result"} where `result`
# is the dispatched op's own output (ingest / intake / ask …).

SLASH = {
    "/help":   "show commands",
    "/folder": "<path>  set the workspace this chat grounds in (its .versum)",
    "/llm":    "toggle LLM phrasing on/off (needs a connected provider)",
    "/clear":  "clear the screen",
    "/quit":   "exit  (also /q, or Ctrl-D)",
}


def parse_command(line: str) -> tuple[str, str]:
    """('' , text) for a normal turn; ('slash', rest) for a /command."""
    s = line.strip()
    if s.startswith("/"):
        head, _, rest = s.partition(" ")
        return head.lower(), rest.strip()
    return "", s


def render_turn(result: dict) -> str:
    """Format one governance_chat result for the terminal."""
    out: list[str] = []
    echo = result.get("echo")
    why = result.get("why")                        # the router's reasoning, if given
    if echo:
        out.append(f"  · {echo}" + (f"  ({why})" if why else ""))  # correctable route
    inner = result.get("result")
    if isinstance(inner, dict):
        if inner.get("error"):
            out.append(f"  ⚠ {inner['error']}")
        else:
            summary = (inner.get("answer") or inner.get("summary")
                       or inner.get("echo") or inner.get("message"))
            if summary:
                out.append(f"  {summary}")
            elif result.get("kind"):
                out.append(f"  ({result['kind']} ok)")
        audit = inner.get("audit_id") or inner.get("audit")
        if audit:
            out.append(f"  audit: {audit}")
    elif inner not in (None, ""):
        out.append(f"  {inner}")
    return "\n".join(out) or "  (no result)"


def _help_text() -> str:
    return "\n".join(f"  {k:<9} {v}" for k, v in SLASH.items())


async def run(chat: Callable[[str, str], "Any"], *,
              folder: str = "",
              read_line: Optional[Callable[[str], str]] = None,
              out=print,
              phrase: Optional[Callable[[str, dict], str]] = None,
              llm_on: bool = False) -> int:
    """Run the REPL. `chat(text, folder)` is an async callable returning the
    governance_chat dict (injected so tests pass a fake). `phrase(question,
    result)` optionally turns RVND's deterministic result into prose (P4, option
    A — never routes governance); `llm_on` is its initial state, toggled by /llm.
    `read_line(prompt)` defaults to input()."""
    reader = read_line or (lambda prompt: input(prompt))
    loop = asyncio.get_event_loop()
    mode = ("LLM-assisted" if (llm_on and phrase) else "deterministic")
    out(f"  RVND chat — {mode}, grounded in your versum. /help, /quit.")
    if phrase is None:
        out("  (no provider connected — `connect` one for optional LLM phrasing)")
    out(f"  workspace: {folder or '(none — set with /folder <path>)'}")
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(
                None, reader, f"rvnd[{_short(folder)}]> ")
        except (EOFError, KeyboardInterrupt):
            out("\n  bye.")
            return 0
        cmd, rest = parse_command(line)
        if cmd in ("/quit", "/q"):
            out("  bye.")
            return 0
        if cmd == "/help":
            out(_help_text()); continue
        if cmd == "/clear":
            out("\033[2J\033[H"); continue
        if cmd == "/folder":
            folder = rest or folder
            out(f"  workspace: {folder or '(none)'}"); continue
        if cmd == "/llm":
            if phrase is None:
                out("  no provider connected — run `loomground-console connect` first")
            else:
                llm_on = not llm_on
                out(f"  LLM phrasing: {'on' if llm_on else 'off'}")
            continue
        if cmd:                       # unknown slash
            out(f"  unknown command {cmd!r} — /help"); continue
        if not rest:
            continue
        try:
            result = await chat(rest, folder)
        except Exception as e:        # noqa: BLE001 - surface, don't crash the REPL
            out(f"  ⚠ {e}"); continue

        if llm_on and phrase is not None:
            # Phrase RVND's DETERMINISTIC result. On any provider error, fall
            # back to the deterministic rendering — the engine's word stands.
            try:
                prose = await loop.run_in_executor(None, phrase, rest, result)
                out("  " + prose.replace("\n", "\n  "))
                out(render_turn(result))           # keep the authoritative core visible
            except Exception as e:                 # noqa: BLE001
                out(render_turn(result))
                out(f"  (LLM phrasing unavailable: {e})")
        else:
            out(render_turn(result))


def _short(folder: str) -> str:
    if not folder:
        return "-"
    parts = folder.rstrip("/").split("/")
    return parts[-1] or "-"
