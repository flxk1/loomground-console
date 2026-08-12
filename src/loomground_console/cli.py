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
    ("board",   "ASCII dashboard — workspaces + the security board"),
    ("workspaces", "list the workspaces RVND knows (pick one in chat with /workspaces)"),
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
    import asyncio
    from . import repl as _repl
    from .rvnd_client import RvndClient, resolve_rvnd_command

    from . import llm as _llm

    banner()
    command = resolve_rvnd_command(getattr(args, "rvnd_dir", None))
    folder = getattr(args, "folder", "") or ""
    # LLM phrasing (P4, option A) — only if a provider is connected. It never
    # routes governance; it phrases RVND's deterministic result. Available for
    # the /llm toggle whenever connected; --no-llm just starts it off.
    provider = _llm.available()
    phrase = (lambda q, r: _llm.phrase(q, r, provider=provider)) if provider else None
    llm_on = bool(provider) and not getattr(args, "no_llm", False)

    async def _main() -> int:
        try:
            async with RvndClient(command) as rvnd:
                return await _repl.run(rvnd.governance_chat, folder=folder,
                                       phrase=phrase, llm_on=llm_on,
                                       list_ws=rvnd.list_workspaces)
        except RuntimeError as e:            # missing 'mcp' dep
            print(f"  {e}")
            return 1
        except Exception as e:               # noqa: BLE001 - server unreachable
            print(f"  could not reach RVND ({e}).")
            print(f"  tried: {' '.join(command)}")
            print("  → point at your install with  --rvnd-dir <dir>  or  RVND_DIR=<dir>,")
            print("    and install the client deps:  pip install 'loomground-console[mcp]'")
            return 1

    return asyncio.run(_main())


def cmd_connect(args: argparse.Namespace) -> int:
    import getpass
    from . import creds

    if args.list:
        conn = creds.list_connected()
        print("  connected providers: " + (", ".join(conn) if conn else "(none)"))
        return 0
    if args.remove:
        ok = creds.disconnect(args.remove)
        print(f"  {'removed' if ok else 'not connected'}: {args.remove}")
        return 0 if ok else 1

    banner()
    known = ", ".join(creds.PROVIDERS)
    provider = (args.provider
                or input(f"  provider [{known}] (default anthropic): ").strip()
                or "anthropic").lower()
    if provider not in creds.PROVIDERS:
        print(f"  unknown provider {provider!r} — known: {known}")
        return 2
    cfg = creds.PROVIDERS[provider]
    api_key = ""
    if not cfg.get("no_auth"):
        try:                       # the USER types the key; it is never echoed
            api_key = getpass.getpass(f"  {cfg['name']} API key (hidden): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  cancelled.")
            return 1
    mode = "format" if args.no_validate else "live"
    try:
        ok, msg = creds.connect(provider, api_key, validate=mode)
    except RuntimeError as e:       # cryptography missing
        print(f"  {e}")
        return 1
    print(f"  {'✓ connected' if ok else '✗'} {provider}: {msg}")
    if ok:
        print("  deterministic chat is unchanged; LLM-assist uses this once P4 lands.")
    return 0 if ok else 1


def _run_with_rvnd(rvnd_dir, go) -> int:
    """Shared boilerplate: open an MCP session to RVND and run `go(rvnd)`."""
    import asyncio
    from .rvnd_client import RvndClient, resolve_rvnd_command
    command = resolve_rvnd_command(rvnd_dir)

    async def _m() -> int:
        try:
            async with RvndClient(command) as rvnd:
                return await go(rvnd)
        except RuntimeError as e:               # missing 'mcp'
            print(f"  {e}")
            return 1
        except Exception as e:                  # noqa: BLE001 - server unreachable
            print(f"  could not reach RVND ({e}).")
            print(f"  tried: {' '.join(command)}  →  --rvnd-dir <dir> or RVND_DIR=<dir>")
            return 1

    return asyncio.run(_m())


def cmd_workspaces(args: argparse.Namespace) -> int:
    from . import board as _board

    async def go(rvnd) -> int:
        print(_board.render_workspaces(await rvnd.list_workspaces()))
        return 0

    return _run_with_rvnd(getattr(args, "rvnd_dir", None), go)


def cmd_board(args: argparse.Namespace) -> int:
    from . import board as _board
    folder_arg = getattr(args, "folder", "") or ""

    async def go(rvnd) -> int:
        ws = await rvnd.list_workspaces()
        folder = folder_arg or ws.get("default", "")
        if not folder:
            print(_board.render_workspaces(ws))
            print("  no default workspace — pick one with --folder <path>")
            return 1
        sd = await rvnd.security_dashboard(folder)
        print(_board.render(ws, sd, folder=folder))
        return 0

    return _run_with_rvnd(getattr(args, "rvnd_dir", None), go)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="loomground-console",
        description="Terminal frontend for RVND — an MCP client, not an engine.")
    p.add_argument("--version", action="version",
                   version=f"loomground-console {__version__}")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("home", help="branded home + command overview")
    chat = sub.add_parser("chat", help="deterministic governance chat REPL")
    chat.add_argument("--folder", default="", help="workspace to ground in (its .versum)")
    chat.add_argument("--rvnd-dir", default=None,
                      help="RVND install dir (else $RVND_DIR, workspaces-mcp, ~/rvnd)")
    chat.add_argument("--no-llm", action="store_true",
                      help="start with LLM phrasing off (toggle in-session with /llm)")
    chat.set_defaults(func=cmd_chat)
    conn = sub.add_parser("connect", help="connect an LLM provider (BYOK API key)")
    conn.add_argument("--provider", help="anthropic | openai | ollama")
    conn.add_argument("--list", action="store_true", help="list connected providers")
    conn.add_argument("--remove", metavar="PROVIDER", help="disconnect a provider")
    conn.add_argument("--no-validate", action="store_true",
                      help="store without a live provider check")
    conn.set_defaults(func=cmd_connect)
    wsp = sub.add_parser("workspaces", help="list workspaces RVND knows")
    wsp.add_argument("--rvnd-dir", default=None, help="RVND install dir")
    wsp.set_defaults(func=cmd_workspaces)
    brd = sub.add_parser("board", help="ASCII dashboard — workspaces + security")
    brd.add_argument("--folder", default="", help="workspace to show (else the default)")
    brd.add_argument("--rvnd-dir", default=None, help="RVND install dir")
    brd.set_defaults(func=cmd_board)

    args = p.parse_args(argv)
    fn = getattr(args, "func", None)
    if fn is not None:
        return fn(args)
    home()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
