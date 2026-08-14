# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""Client-side LLM assist (P4, option A) — phrase RVND's DETERMINISTIC output.

The LLM never routes, decides, or invents governance. RVND has already made
every decision deterministically; the provider is handed the user's question
plus RVND's result and asked only to phrase it. With no connected provider the
chat stays pure-deterministic. BYOK key comes from `creds`; the provider is
called directly over httpx (no SDK), so nothing leaves the machine except the
call to the provider the user chose.
"""
from __future__ import annotations

import json
from typing import Optional

from . import creds

_SYSTEM = (
    "You are the presentation layer for RVND, a local-first governance engine. "
    "RVND has ALREADY made every governance decision deterministically. Your ONLY "
    "job is to phrase RVND's result for the user in clear, brief prose. You must "
    "NOT invent, add, or change any governance decision, verdict, permission, or "
    "fact, and you must not claim authority RVND did not grant. If RVND returned "
    "little or an error, say so plainly."
)

# Safe, current defaults; overridden by a cred's stored default_model.
DEFAULT_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
}


def available() -> Optional[str]:
    """The first connected cloud provider we can phrase with, or None."""
    for p in creds.list_connected():
        if p in ("anthropic", "openai"):
            return p
    return None


def _model_for(provider: str) -> str:
    stored = (creds._load().get(provider) or {}).get("default_model") or ""
    return stored or DEFAULT_MODELS.get(provider, "")


def _prompt(question: str, deterministic: dict) -> str:
    return (f"User asked RVND: {question!r}\n\n"
            f"RVND's deterministic result (authoritative — do not alter or extend):\n"
            f"{json.dumps(deterministic, ensure_ascii=False, indent=2)[:4000]}\n\n"
            f"Phrase this for the user in a few sentences. Add no governance content.")


def phrase(question: str, deterministic: dict, *, provider: str,
           timeout: float = 30.0) -> str:
    """Phrase RVND's result via the connected provider. Raises on transport/auth
    error so the caller can fall back to the deterministic rendering."""
    import httpx

    key = creds.get_key(provider)
    if not key:
        raise RuntimeError(f"no stored key for {provider}")
    model = _model_for(provider)
    user = _prompt(question, deterministic)

    if provider == "anthropic":
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": model, "max_tokens": 600, "system": _SYSTEM,
                  "messages": [{"role": "user", "content": user}]},
            timeout=timeout)
        r.raise_for_status()
        blocks = r.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks).strip()

    if provider == "openai":
        r = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "content-type": "application/json"},
            json={"model": model, "max_tokens": 600,
                  "messages": [{"role": "system", "content": _SYSTEM},
                               {"role": "user", "content": user}]},
            timeout=timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    raise RuntimeError(f"unsupported provider {provider!r}")
