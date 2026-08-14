# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""The deterministic governance chat REPL.

Drives host's `governance_chat` over MCP, grounded in the workspace's versum.
**No LLM** — that arrives with `connect` (a later phase). Shell shaped after
Brain's `cmd_repl`: readline history, slash-commands, an inferred-intent echo
(so a wrong route is visible + correctable), and the result + audit id.

Turn/formatting logic is kept pure (`render_turn`, `parse_command`) so it is
unit-tested without a live host; only `run()` needs the server.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional

# governance_chat returns {"intent", "echo", "kind", "result"} where `result`
# is the dispatched op's own output (ingest / intake / ask …).

SLASH = {
    "/help":       "show commands",
    "/workspaces": "list workspaces host knows (also /ws)",
    "/folder":     "<number|path>  set the workspace this chat grounds in (its .versum)",
    "/llm":        "toggle LLM phrasing on/off (needs a connected provider)",
    "/clear":      "clear the screen",
    "/quit":       "exit  (also /q, or Ctrl-D)",
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
        text = next((v for v in (inner.get("answer"), inner.get("message"),
                                 inner.get("echo")) if isinstance(v, str) and v), None)
        kind = result.get("kind", "result")
        if inner.get("error"):
            out.append(f"  ⚠ {inner['error']}")
        elif text:
            out.append(f"  {text}")
        else:
            # Structured result (e.g. a governance map): a compact count line,
            # never a raw dict dump.
            summ = inner.get("summary")
            if isinstance(summ, dict):
                pairs = ", ".join(f"{k} {v}" for k, v in summ.items()
                                  if isinstance(v, (int, float)))
                out.append(f"  {kind}: {pairs}" if pairs else f"  ({kind} ok)")
            elif isinstance(summ, str) and summ:
                out.append(f"  {summ}")
            else:
                out.append(f"  ({kind} ok)")
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
              llm_on: bool = False,
              list_ws: Optional[Callable[[], "Any"]] = None) -> int:
    """Run the REPL. `chat(text, folder)` is an async callable returning the
    governance_chat dict (injected so tests pass a fake). `phrase(question,
    result)` optionally turns host's deterministic result into prose (P4, option
    A — never routes governance); `llm_on` is its initial state, toggled by /llm.
    `read_line(prompt)` defaults to input()."""
    reader = read_line or (lambda prompt: input(prompt))
    loop = asyncio.get_event_loop()
    last_ws: list[str] = []                    # paths from the last /workspaces list
    mode = ("LLM-assisted" if (llm_on and phrase) else "deterministic")
    out(f"  host chat — {mode}, grounded in your versum. /help, /quit.")
    if phrase is None:
        out("  (no provider connected — `connect` one for optional LLM phrasing)")
    out(f"  workspace: {folder or '(none — set with /folder <path>)'}")
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(
                None, reader, f"host[{_short(folder)}]> ")
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
        if cmd in ("/workspaces", "/ws"):
            if list_ws is None:
                out("  (workspace list unavailable)"); continue
            try:
                data = await list_ws()
            except Exception as e:                # noqa: BLE001
                out(f"  ⚠ {e}"); continue
            rows = data.get("workspaces") or []
            last_ws[:] = [r.get("path", "") for r in rows]
            default = data.get("default", "")
            for i, r in enumerate(rows, 1):
                mark = "*" if r.get("path") == default else " "
                out(f"  {i:>2}{mark} {(r.get('label') or ''):<12} {r.get('path', '')}")
            out("  → /folder <number|path> to switch"); continue
        if cmd == "/folder":
            if rest.isdigit() and 1 <= int(rest) <= len(last_ws):
                folder = last_ws[int(rest) - 1]   # pick from the last /workspaces list
            elif rest:
                folder = rest
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
            # Phrase host's DETERMINISTIC result. On any provider error, fall
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
