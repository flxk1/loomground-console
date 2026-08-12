# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""loomground-console CLI — P1: branded home + command overview.

Deliberately dependency-free at this stage. The banner is shared with RVND's
`bootstrap.sh`. Later phases add `chat` (an MCP-client REPL over RVND's
deterministic governance_chat, grounded in the workspace versum), `board`
(ASCII dashboards), and `connect` (BYOK provider credentials).
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import IO

from . import __version__

_ART = (
    "   ██████╗ ██╗   ██╗███╗   ██╗██████╗ ",
    "   ██╔══██╗██║   ██║████╗  ██║██╔══██╗",
    "   ██████╔╝██║   ██║██╔██╗ ██║██║  ██║",
    "   ██╔══██╗╚██╗ ██╔╝██║╚██╗██║██║  ██║",
    "   ██║  ██║ ╚████╔╝ ██║ ╚████║██████╔╝",
    "   ╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═══╝╚═════╝ ",
)

# Command surface. Static for P1; a later phase reads `workspaces guide` from
# RVND over MCP so this never drifts from the server's real command set.
_COMMANDS = (
    ("chat",    "deterministic governance chat, grounded in your versum (no LLM)"),
    ("board",   "ASCII dashboard — oversight lanes, breaker state, audit tail"),
    ("connect", "connect an LLM provider (API key / OAuth) to enable LLM-assisted chat"),
    ("setup",   "run RVND's guided first-run wizard (workspaces init)"),
    ("console", "open the browser console (RVND app → http://127.0.0.1:8799)"),
    ("home",    "this screen"),
)


def _c(code: str, out: IO[str]) -> str:
    """ANSI escape, or '' when not a tty / NO_COLOR is set."""
    if not getattr(out, "isatty", lambda: False)() or os.environ.get("NO_COLOR"):
        return ""
    return f"\033[{code}m"


def banner(out: IO[str] = sys.stdout) -> None:
    accent, dim, reset = _c("38;5;39", out), _c("2", out), _c("0", out)
    out.write("\n" + accent + "\n".join(_ART) + reset + "\n")
    out.write(f"   {dim}RVND terminal · local-first governance for agentic AI{reset}\n\n")


def home(out: IO[str] = sys.stdout) -> None:
    banner(out)
    accent, dim, reset = _c("38;5;39", out), _c("2", out), _c("0", out)
    out.write(f"   {dim}commands{reset}\n")
    for name, desc in _COMMANDS:
        out.write(f"     {accent}{name:<8}{reset} {desc}\n")
    out.write(f"\n   {dim}loomground-console {__version__} — an MCP client of RVND; "
              f"no engine of its own{reset}\n\n")


def cmd_chat(args: argparse.Namespace) -> int:
    banner()
    print("   chat lands next (P2): a deterministic REPL that drives RVND's")
    print("   governance_chat over MCP, grounded in the workspace's versum —")
    print("   LLM only once you `connect` a provider. Brain's cmd_repl shell,")
    print("   RVND's real engine behind it.\n")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="loomground-console",
        description="Terminal frontend for RVND — an MCP client, not an engine.")
    p.add_argument("--version", action="version",
                   version=f"loomground-console {__version__}")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("home", help="branded home + command overview")
    sub.add_parser("chat", help="deterministic governance chat REPL (P2)"
                   ).set_defaults(func=cmd_chat)

    args = p.parse_args(argv)
    fn = getattr(args, "func", None)
    if fn is not None:
        return fn(args)
    home()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
