# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""The one seam to RVND — an MCP stdio client.

loomground-console holds no governance logic. It spawns RVND's installed MCP
server (`python -m workspaces.mcp_server`) and calls the `workspace_workflow`
facade, exactly as Claude Code / the browser console do. `governance_chat` is
reached as `workspace_workflow(op="governance_chat", params={text, folder_context})`.

The `mcp` package is an optional dependency (`pip install loomground-console[mcp]`);
it is imported lazily so P1 (home/banner) stays dependency-free.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Optional


def resolve_rvnd_command(rvnd_dir: Optional[str] = None) -> list[str]:
    """The command that launches RVND's MCP server. Resolution order:
    explicit dir → $RVND_DIR → `workspaces-mcp` on PATH → ~/rvnd venv →
    current interpreter (only works if `workspaces` is importable here)."""
    cand = rvnd_dir or os.environ.get("RVND_DIR")
    if cand:
        py = Path(cand).expanduser() / ".venv" / "bin" / "python"
        if py.exists():
            return [str(py), "-m", "workspaces.mcp_server"]
    exe = shutil.which("workspaces-mcp")
    if exe:
        return [exe]
    home_py = Path.home() / "rvnd" / ".venv" / "bin" / "python"
    if home_py.exists():
        return [str(home_py), "-m", "workspaces.mcp_server"]
    return [sys.executable, "-m", "workspaces.mcp_server"]


def unwrap_tool_result(res: Any) -> dict:
    """Pull the JSON dict out of an MCP CallToolResult. FastMCP returns a
    structured object plus a JSON text block; prefer the structured content,
    fall back to parsing the first text block."""
    sc = getattr(res, "structuredContent", None)
    if isinstance(sc, dict):
        # FastMCP wraps a non-dict return under {"result": ...}; unwrap when present
        return sc.get("result", sc) if set(sc.keys()) == {"result"} else sc
    for block in getattr(res, "content", None) or []:
        txt = getattr(block, "text", None)
        if txt:
            try:
                return json.loads(txt)
            except (ValueError, TypeError):
                return {"text": txt}
    return {}


class RvndClient:
    """Async context manager over an MCP stdio session to RVND.

        async with RvndClient(resolve_rvnd_command()) as rvnd:
            out = await rvnd.governance_chat("draft a data-retention policy", folder)
    """

    def __init__(self, command: list[str], *, env: Optional[dict] = None):
        self.command = command
        self.env = env
        self._session: Any = None
        self._stack: Optional[AsyncExitStack] = None

    async def __aenter__(self) -> "RvndClient":
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as e:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "the RVND client needs the 'mcp' package: "
                "pip install 'loomground-console[mcp]'") from e
        self._stack = AsyncExitStack()
        params = StdioServerParameters(
            command=self.command[0], args=self.command[1:], env=self.env)
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._stack is not None:
            await self._stack.aclose()

    async def op(self, tool: str, op: str, params: Optional[dict] = None) -> dict:
        """Call any RVND facade tool: tool(op=…, params=…)."""
        res = await self._session.call_tool(
            tool, {"op": op, "params": params or {}})
        return unwrap_tool_result(res)

    async def governance_chat(self, text: str, folder_context: str = "") -> dict:
        """One deterministic governed turn: intent router → dispatch → result."""
        return await self.op(
            "workspace_workflow", "governance_chat",
            {"text": text, "folder_context": folder_context})

    async def security_dashboard(self, folder_context: str,
                                 group_by: str = "verdict") -> dict:
        """Read-only projection of the folder's signed chain (admitted/held/…)."""
        return await self.op(
            "workspace_workflow", "security_dashboard",
            {"folder_context": folder_context, "group_by": group_by})

    async def list_workspaces(self) -> dict:
        """{ok, default, workspaces:[{path,label,added_at,exists}, ...]}."""
        return await self.op("workspace_workspace", "list", {})
