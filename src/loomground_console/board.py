# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""ASCII board — render host state in the terminal.

Pure renderers (no I/O, no color) so they unit-test without a live server; the
fetch is the MCP client's job. Inspired by Brain's framed panels. Shapes are the
real ones host returns:
  workspaces        {ok, default, workspaces:[{path,label,added_at,exists}]}
  security_dashboard {version, summary:{total,admitted,held,rejected,released,
                      holds_pending,sources,top_rules}, limits, ...}
"""
from __future__ import annotations

from typing import Any


def panel(title: str, lines: list[str], width: int = 64) -> str:
    """A framed box. Width grows to fit content; plain ASCII inside only."""
    body = lines or ["(empty)"]
    w = max(width, len(title) + 4, *(len(x) + 4 for x in body))
    head = f"┌─ {title} " + "─" * (w - len(title) - 4) + "┐"
    out = [head]
    for x in body:
        out.append("│ " + x.ljust(w - 3) + "│")
    out.append("└" + "─" * (w - 2) + "┘")
    return "\n".join(out)


def render_workspaces(ws: dict) -> str:
    default = ws.get("default", "")
    rows = ws.get("workspaces") or []
    lines: list[str] = []
    for i, r in enumerate(rows, 1):
        mark = "*" if r.get("path") == default else " "
        label = (r.get("label") or "")[:12]
        missing = "" if r.get("exists", True) else "  ⚠ missing"
        lines.append(f"{i:>2} {mark} {label:<12} {r.get('path', '')}{missing}")
    if not lines:
        lines = ["(no workspaces registered — `workspaces init` or add one)"]
    return panel(f"workspaces · {len(rows)} · * = default", lines)


def render_security(sd: dict, *, folder: str = "") -> str:
    s = sd.get("summary", {}) or {}

    def n(k: str) -> Any:
        return s.get(k, 0)

    lines = [
        f"total {n('total'):<4}  admitted {n('admitted'):<4}  "
        f"held {n('held'):<4}  rejected {n('rejected'):<4}",
        f"released {n('released'):<4}  holds_pending {n('holds_pending'):<4}  "
        f"sources {n('sources'):<4}",
    ]
    top = s.get("top_rules") or []
    if top:
        lines.append("top rules: " + ", ".join(
            (r.get("rule", str(r)) if isinstance(r, dict) else str(r)) for r in top[:5]))
    lines.append("")
    lines.append("tripwire, not containment — declares, never certifies.")
    tail = folder.rstrip("/").split("/")[-1] if folder else ""
    return panel(f"security{(' · ' + tail) if tail else ''}", lines)


def render(ws: dict, sd: dict, *, folder: str = "") -> str:
    """The full board: workspaces + the security panel for `folder`."""
    return render_workspaces(ws) + "\n\n" + render_security(sd, folder=folder)
