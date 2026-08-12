# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""P4 client-side LLM assist. `available` uses a temp cred store; `phrase` is
tested with httpx mocked — no network, no real provider call."""
from __future__ import annotations

import asyncio

import pytest

from loomground_console import creds, llm, repl


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("LOOMGROUND_CONSOLE_HOME", str(tmp_path / "cfg"))
    return tmp_path


def test_available_none_then_provider(home):
    assert llm.available() is None
    pytest.importorskip("cryptography")
    creds.connect("anthropic", "sk-ant-" + "a" * 24, validate="format")
    assert llm.available() == "anthropic"


def test_phrase_anthropic_mocked(home, monkeypatch):
    pytest.importorskip("cryptography")
    httpx = pytest.importorskip("httpx")
    creds.connect("anthropic", "sk-ant-" + "k" * 24, validate="format")
    seen = {}

    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"content": [{"type": "text", "text": "phrased!"}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen.update(url=url, headers=headers, json=json)
        return Resp()

    monkeypatch.setattr(httpx, "post", fake_post)
    out = llm.phrase("q", {"answer": "x"}, provider="anthropic")
    assert out == "phrased!"
    assert seen["url"].endswith("/v1/messages")
    assert seen["headers"]["x-api-key"] == "sk-ant-" + "k" * 24
    assert seen["json"]["model"]                    # a model was chosen
    assert "authoritative" in seen["json"]["messages"][0]["content"]


def test_phrase_openai_mocked(home, monkeypatch):
    pytest.importorskip("cryptography")
    httpx = pytest.importorskip("httpx")
    creds.connect("openai", "sk-" + "k" * 24, validate="format")

    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": "hi"}}]}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Resp())
    assert llm.phrase("q", {"a": 1}, provider="openai") == "hi"


# --- REPL integration (fake phrase; no provider needed) --------------------

def test_repl_phrases_over_deterministic_core():
    lines = iter(["draft a policy", "/quit"])
    printed: list[str] = []

    async def fake_chat(t, f):
        return {"echo": "inferred: ask", "result": {"answer": "CORE", "audit_id": "a1"}}

    rc = asyncio.run(repl.run(fake_chat, read_line=lambda p: next(lines),
                              out=printed.append,
                              phrase=lambda q, r: "friendly phrasing", llm_on=True))
    assert rc == 0
    blob = "\n".join(printed)
    assert "friendly phrasing" in blob        # LLM prose shown
    assert "CORE" in blob                      # deterministic core still shown
    assert "audit: a1" in blob


def test_repl_falls_back_when_phrase_errors():
    lines = iter(["x", "/quit"])
    printed: list[str] = []

    async def fake_chat(t, f):
        return {"result": {"answer": "CORE"}}

    def boom(q, r):
        raise RuntimeError("api down")

    asyncio.run(repl.run(fake_chat, read_line=lambda p: next(lines),
                         out=printed.append, phrase=boom, llm_on=True))
    blob = "\n".join(printed)
    assert "CORE" in blob
    assert "api down" in blob


def test_repl_llm_toggle_off():
    lines = iter(["/llm", "next turn", "/quit"])
    printed: list[str] = []

    async def fake_chat(t, f):
        return {"result": {"answer": "CORE"}}

    asyncio.run(repl.run(fake_chat, read_line=lambda p: next(lines),
                         out=printed.append,
                         phrase=lambda q, r: "PHRASED", llm_on=True))
    blob = "\n".join(printed)
    assert "LLM phrasing: off" in blob
    assert "PHRASED" not in blob               # toggled off before the turn ran
