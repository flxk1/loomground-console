# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""Pure REPL + client-helper logic — no live host needed. The MCP round-trip
itself is verified separately against a real host install."""
from __future__ import annotations

import asyncio

from loomground_console import repl
from loomground_console.rvnd_client import unwrap_tool_result, resolve_rvnd_command


# --- parse_command ---------------------------------------------------------

def test_parse_command_normal_vs_slash():
    assert repl.parse_command("draft a policy") == ("", "draft a policy")
    assert repl.parse_command("  /folder /tmp/ws ") == ("/folder", "/tmp/ws")
    assert repl.parse_command("/QUIT") == ("/quit", "")


# --- render_turn -----------------------------------------------------------

def test_render_turn_echoes_intent_why_and_audit():
    # shape taken from a live governance_chat response
    out = repl.render_turn({"intent": "ask", "echo": "inferred: ask",
                            "why": "question-shaped", "kind": "ask",
                            "result": {"answer": "42", "audit_id": "a1"}})
    assert "inferred: ask" in out
    assert "question-shaped" in out
    assert "42" in out
    assert "audit: a1" in out


def test_render_turn_map_shows_compact_counts_not_raw_dict():
    # host's map result: summary is a DICT — must render as a count line, not a dump
    out = repl.render_turn({"echo": "inferred: ask", "kind": "map",
                            "result": {"summary": {"total": 0, "empty": 0,
                                                   "instruments": []}}})
    assert "map: total 0, empty 0" in out
    assert "{" not in out                       # no raw dict


def test_render_turn_surfaces_error():
    out = repl.render_turn({"echo": "inferred: ingest",
                            "result": {"error": "no policy text"}})
    assert "no policy text" in out
    assert "⚠" in out


def test_render_turn_handles_empty():
    assert "no result" in repl.render_turn({"result": None})


# --- REPL loop with a fake chat (deterministic, no server) -----------------

def test_repl_runs_a_turn_then_quits():
    lines = iter(["draft a retention policy", "/quit"])
    printed: list[str] = []

    async def fake_chat(text, folder):
        return {"echo": f"inferred: ask", "result": {"answer": f"echo:{text}",
                                                     "audit_id": "z9"}}

    rc = asyncio.run(repl.run(
        fake_chat, folder="/tmp/ws",
        read_line=lambda prompt: next(lines),
        out=printed.append))
    assert rc == 0
    blob = "\n".join(printed)
    assert "echo:draft a retention policy" in blob
    assert "audit: z9" in blob
    assert "bye." in blob


def test_repl_workspaces_list_and_pick_by_number():
    lines = iter(["/workspaces", "/folder 2", "hello", "/quit"])
    printed: list[str] = []

    async def fake_chat(text, folder):
        printed.append(f"CHAT[{folder}]:{text}")
        return {"result": {"answer": "ok"}}

    async def fake_list():
        return {"default": "/w/a", "workspaces": [
            {"path": "/w/a", "label": "alpha"}, {"path": "/w/b", "label": "beta"}]}

    asyncio.run(repl.run(fake_chat, read_line=lambda p: next(lines),
                         out=printed.append, list_ws=fake_list))
    blob = "\n".join(printed)
    assert "/w/b" in blob                      # listed
    assert "CHAT[/w/b]:hello" in blob          # /folder 2 switched grounding to beta


def test_repl_chat_error_does_not_crash():
    lines = iter(["boom", "/quit"])
    printed: list[str] = []

    async def boom(text, folder):
        raise RuntimeError("server said no")

    rc = asyncio.run(repl.run(boom, read_line=lambda p: next(lines), out=printed.append))
    assert rc == 0
    assert any("server said no" in p for p in printed)


# --- client helpers --------------------------------------------------------

def test_unwrap_prefers_structured_content():
    class R:
        structuredContent = {"intent": "ask", "result": {"answer": "hi"}}
        content = []
    assert unwrap_tool_result(R()) == {"intent": "ask", "result": {"answer": "hi"}}


def test_unwrap_unwraps_single_result_key():
    class R:
        structuredContent = {"result": {"answer": "hi"}}
        content = []
    assert unwrap_tool_result(R()) == {"answer": "hi"}


def test_unwrap_falls_back_to_text_json():
    class Block:
        text = '{"answer": "hi"}'
    class R:
        structuredContent = None
        content = [Block()]
    assert unwrap_tool_result(R()) == {"answer": "hi"}


def test_resolve_command_prefers_explicit_dir(tmp_path):
    venv = tmp_path / ".venv" / "bin"
    venv.mkdir(parents=True)
    (venv / "python").write_text("")
    cmd = resolve_rvnd_command(str(tmp_path))
    assert cmd[0].endswith("/.venv/bin/python")
    assert cmd[1:] == ["-m", "workspaces.mcp_server"]
