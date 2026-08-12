# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""ASCII board renderers — pure, against the real RVND shapes. No server."""
from __future__ import annotations

from loomground_console import board


def test_panel_frames_content():
    p = board.panel("title", ["a", "bb"])
    assert p.startswith("┌") and "title" in p
    assert "│ a" in p
    assert p.rstrip().endswith("┘")


def test_render_workspaces_marks_default_and_missing():
    ws = {"default": "/w/a", "workspaces": [
        {"path": "/w/a", "label": "alpha", "exists": True},
        {"path": "/w/b", "label": "beta", "exists": False},
    ]}
    out = board.render_workspaces(ws)
    assert "alpha" in out and "/w/a" in out
    assert "*" in out                       # default marked
    assert "missing" in out                 # b flagged not-present
    assert " 1 " in out and " 2 " in out    # numbered


def test_render_workspaces_empty():
    assert "no workspaces" in board.render_workspaces({"workspaces": []})


def test_render_security_counts_and_disclaimer():
    sd = {"summary": {"total": 3, "admitted": 2, "held": 1, "rejected": 0,
                      "released": 0, "holds_pending": 1, "sources": 2,
                      "top_rules": [{"rule": "pii"}]}}
    out = board.render_security(sd, folder="/w/alpha")
    assert "admitted 2" in out
    assert "held 1" in out
    assert "pii" in out
    assert "tripwire" in out                # honest disclaimer carried through
    assert "alpha" in out


def test_render_full_combines_both_panels():
    out = board.render({"default": "", "workspaces": []}, {"summary": {}}, folder="/w/x")
    assert "workspaces" in out and "security" in out
