# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""BYOK credential store — format validation is pure; the encrypted round-trip
uses a temp store (LOOMGROUND_CONSOLE_HOME) and skips if cryptography is absent.
No network: live validation is not exercised here."""
from __future__ import annotations

import pytest

from loomground_console import creds


# --- format validation (pure) ----------------------------------------------

def test_format_anthropic_prefix():
    ok, _ = creds.validate_key_format("anthropic", "sk-ant-" + "a" * 24)
    assert ok
    ok, msg = creds.validate_key_format("anthropic", "sk-oops")
    assert not ok and "sk-ant-" in msg


def test_format_openai_and_unknown():
    assert creds.validate_key_format("openai", "sk-" + "b" * 24)[0]
    assert not creds.validate_key_format("openai", "nope")[0]
    ok, msg = creds.validate_key_format("mystery", "x")
    assert not ok and "unknown provider" in msg


def test_format_ollama_needs_no_key():
    assert creds.validate_key_format("ollama", "")[0]


# --- encrypted store round-trip (needs cryptography) ------------------------

@pytest.fixture()
def store_home(tmp_path, monkeypatch):
    monkeypatch.setenv("LOOMGROUND_CONSOLE_HOME", str(tmp_path / "cfg"))
    return tmp_path


def test_connect_list_get_disconnect_roundtrip(store_home, monkeypatch):
    pytest.importorskip("cryptography")
    ok, _ = creds.connect("anthropic", "sk-ant-" + "c" * 24, validate="format")
    assert ok
    assert creds.list_connected() == ["anthropic"]
    assert creds.get_key("anthropic") == "sk-ant-" + "c" * 24
    # stored encrypted, not plaintext
    blob = (store_home / "cfg" / "credentials.enc").read_bytes()
    assert b"sk-ant-" not in blob
    assert creds.disconnect("anthropic") is True
    assert creds.list_connected() == []
    assert creds.get_key("anthropic") is None


def test_connect_rejects_bad_format(store_home):
    pytest.importorskip("cryptography")
    ok, msg = creds.connect("openai", "not-a-key", validate="format")
    assert not ok and "invalid format" in msg
    assert creds.list_connected() == []


def test_keyfile_is_0600(store_home):
    pytest.importorskip("cryptography")
    creds.connect("ollama", "", validate="none")
    import stat
    mode = (store_home / "cfg" / "store.key").stat().st_mode
    assert stat.S_IMODE(mode) == 0o600
