# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""BYOK provider credentials — a LOCAL, single-user, encrypted store.

Ported from Brain's `user_credentials.py` (the PROVIDERS registry + format/live
validation), simplified to one machine / one user. Keys are encrypted at rest
with Fernet under a 0600 key file in ~/.config/loomground-console/. Nothing is
sent anywhere except the provider's own validation endpoint, and only when you
ask for a live check.

Honest limitation: the encryption key sits next to the ciphertext (both 0600).
This protects against casual reading and accidental commits, NOT against an
attacker who already has your filesystem. For that, use an OS keychain (future).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

# Trimmed from Brain's registry — the ones a local RVND user is likely to BYO.
PROVIDERS: dict[str, dict] = {
    "anthropic": {
        "name": "Anthropic", "key_prefix": "sk-ant-",
        "key_pattern": r"^sk-ant-[a-zA-Z0-9_-]{20,}$",
        "test_url": "https://api.anthropic.com/v1/models",
        "auth_header": "x-api-key", "auth_format": "{key}",
        "extra_headers": {"anthropic-version": "2023-06-01"},
    },
    "openai": {
        "name": "OpenAI", "key_prefix": "sk-",
        "key_pattern": r"^sk-[a-zA-Z0-9_-]{20,}$",
        "test_url": "https://api.openai.com/v1/models",
        "auth_header": "Authorization", "auth_format": "Bearer {key}",
    },
    "ollama": {
        "name": "Ollama (local)", "key_pattern": r".*", "no_auth": True, "local": True,
        "test_url": "http://localhost:11434/api/tags",
        "default_endpoint": "http://localhost:11434",
    },
}


def _config_dir() -> Path:
    return Path(os.environ.get("LOOMGROUND_CONSOLE_HOME")
                or (Path.home() / ".config" / "loomground-console"))


# --- validation (pure / network) -------------------------------------------

def validate_key_format(provider: str, api_key: str) -> tuple[bool, str]:
    cfg = PROVIDERS.get(provider)
    if not cfg:
        return False, f"unknown provider: {provider}"
    if cfg.get("no_auth"):
        return True, ""
    if not api_key:
        return False, "an API key is required"
    pat = cfg.get("key_pattern", "")
    if pat and not re.match(pat, api_key):
        pref = cfg.get("key_prefix", "")
        return False, (f"invalid format — {cfg['name']} keys start with '{pref}'"
                       if pref else f"invalid format for {cfg['name']}")
    return True, ""


def validate_key_live(provider: str, api_key: str, *, timeout: float = 10.0) -> tuple[bool, str]:
    ok, err = validate_key_format(provider, api_key)
    if not ok:
        return False, err
    try:
        import httpx
    except ImportError:
        return True, "format ok (live check skipped — httpx not installed)"
    cfg = PROVIDERS[provider]
    url = cfg.get("test_url")
    if not url:
        return True, "format ok"
    headers: dict[str, str] = {}
    if not cfg.get("no_auth"):
        headers[cfg["auth_header"]] = cfg["auth_format"].format(key=api_key)
        headers.update(cfg.get("extra_headers", {}))
    try:
        r = httpx.get(url, headers=headers, timeout=timeout)
    except Exception as e:  # noqa: BLE001 - report unreachable, don't crash
        return False, f"live: cannot reach {cfg['name']} ({e})"
    if r.status_code == 200:
        return True, "live: ok"
    if r.status_code in (401, 403):
        return False, "live: key rejected by provider"
    return False, f"live: HTTP {r.status_code}"


# --- encrypted store -------------------------------------------------------

def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as e:  # pragma: no cover - dependency guard
        raise RuntimeError("credential storage needs 'cryptography': "
                           "pip install 'loomground-console[connect]'") from e
    d = _config_dir()
    d.mkdir(parents=True, exist_ok=True)
    keyfile = d / "store.key"
    if not keyfile.exists():
        keyfile.write_bytes(Fernet.generate_key())
        keyfile.chmod(0o600)
    return Fernet(keyfile.read_bytes())


def _load() -> dict:
    store = _config_dir() / "credentials.enc"
    if not store.exists():
        return {}
    try:
        return json.loads(_fernet().decrypt(store.read_bytes()).decode())
    except Exception:  # noqa: BLE001 - corrupt/rotated key → treat as empty
        return {}


def _save(data: dict) -> None:
    store = _config_dir() / "credentials.enc"
    store.write_bytes(_fernet().encrypt(json.dumps(data).encode()))
    store.chmod(0o600)


def connect(provider: str, api_key: str, *, endpoint: str = "",
            default_model: str = "", validate: str = "live") -> tuple[bool, str]:
    """Store a provider credential. validate: 'live' | 'format' | 'none'."""
    provider = provider.strip().lower()
    if provider not in PROVIDERS:
        return False, f"unknown provider {provider!r} (known: {', '.join(PROVIDERS)})"
    if validate == "live":
        ok, msg = validate_key_live(provider, api_key)
    elif validate == "format":
        ok, msg = validate_key_format(provider, api_key)
    else:
        ok, msg = True, "stored (unvalidated)"
    if not ok:
        return False, msg
    data = _load()
    data[provider] = {"key": api_key, "endpoint": endpoint, "default_model": default_model}
    _save(data)
    return True, msg or "stored"


def list_connected() -> list[str]:
    return sorted(_load().keys())


def get_key(provider: str) -> Optional[str]:
    """The stored key for a provider (for the LLM wiring in P4)."""
    return (_load().get(provider.strip().lower()) or {}).get("key")


def disconnect(provider: str) -> bool:
    data = _load()
    provider = provider.strip().lower()
    if provider in data:
        del data[provider]
        _save(data)
        return True
    return False
