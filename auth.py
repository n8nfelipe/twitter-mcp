"""Authentication loader for twitter-mcp.

Resolution order for credentials:
1. secret-vault-mcp (cofre criptografado) — preferred, se VAULT_MASTER_PASSWORD
   e TWITTER_VAULT_ENTRY (default: "twitter-cookies") estiverem definidos.
2. Environment variables / .env — fallback (TWITTER_AUTH_TOKEN, TWITTER_CT0, ...).

O cofre deve ter uma entry com 4 fields padrão:
  - name = TWITTER_VAULT_ENTRY (default "twitter-cookies")
  - username = <twitter_handle>
  - password = <auth_token>
  - notes  = JSON com {"ct0": "...", "user_id": "...", "csrf_token": "..."}
OU um entry usando fields url/notes custom — ver _extract_cookies_from_entry.

Se a entry não existir no cofre, automaticamente faz fallback para env vars
(útil em dev antes de popular o cofre).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


DEFAULT_VAULT_ENTRY = "twitter-cookies"


@dataclass
class TwitterAuth:
    auth_token: str = ""
    ct0: str = ""
    user_id: str = ""
    csrf_token: str = ""
    username: str = ""
    source: str = "env"

    @property
    def is_valid(self) -> bool:
        return bool(self.auth_token) and bool(self.ct0)

    @property
    def cookies(self) -> dict[str, str]:
        cookies = {
            "auth_token": self.auth_token,
            "ct0": self.ct0,
        }
        if self.user_id:
            cookies["user_id"] = self.user_id
        return cookies

    @property
    def headers(self) -> dict[str, str]:
        headers = {
            "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "X-Csrf-Token": self.ct0,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://twitter.com",
            "Referer": "https://twitter.com/",
        }
        return headers


def _extract_cookies_from_entry(entry) -> Optional[dict[str, str]]:
    """Extrai ct0/user_id/csrf_token de uma entry do cofre.

    Estratégia:
    1) Tenta parsear entry.notes como JSON com chaves ct0/user_id/csrf_token.
    2) Tenta parsear entry.url como JSON (algumas entries guardam tudo no url).
    Se não achar, retorna None e o caller faz fallback.
    """
    for blob in (entry.notes, entry.url):
        if not blob:
            continue
        try:
            data = json.loads(blob)
        except (ValueError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        ct0 = data.get("ct0", "")
        if ct0:
            return {
                "ct0": ct0,
                "user_id": str(data.get("user_id", "")),
                "csrf_token": str(data.get("csrf_token", "")),
            }
    return None


def _load_from_vault(entry_name: str) -> Optional[TwitterAuth]:
    try:
        from secret_vault_mcp import VaultClient
        from secret_vault_mcp.auth import VaultConfig
    except ImportError:
        return None

    try:
        config = VaultConfig.from_env()
    except ValueError:
        return None

    try:
        client = VaultClient(config)
        entry = client.get_secret(entry_name, reveal_password=True)
    except Exception:
        return None

    extras = _extract_cookies_from_entry(entry) or {}

    return TwitterAuth(
        auth_token=entry.password,
        ct0=extras.get("ct0", ""),
        user_id=extras.get("user_id", ""),
        csrf_token=extras.get("csrf_token", ""),
        username=entry.username,
        source="vault",
    )


def _load_from_env() -> TwitterAuth:
    return TwitterAuth(
        auth_token=os.getenv("TWITTER_AUTH_TOKEN", ""),
        ct0=os.getenv("TWITTER_CT0", ""),
        user_id=os.getenv("TWITTER_USER_ID", ""),
        csrf_token=os.getenv("TWITTER_CSRF_TOKEN", ""),
        username=os.getenv("TWITTER_USERNAME", ""),
        source="env",
    )


def load_auth() -> TwitterAuth:
    entry_name = os.getenv("TWITTER_VAULT_ENTRY", DEFAULT_VAULT_ENTRY)
    use_vault = os.getenv("TWITTER_USE_VAULT", "auto").lower()

    if use_vault in ("1", "true", "yes", "on"):
        from_vault = _load_from_vault(entry_name)
        if from_vault is None or not from_vault.is_valid:
            raise RuntimeError(
                f"Vault enabled but entry '{entry_name}' missing or invalid. "
                "Populate the cofre or set TWITTER_USE_VAULT=auto for env fallback."
            )
        return from_vault

    if use_vault == "auto":
        from_vault = _load_from_vault(entry_name)
        if from_vault is not None and from_vault.is_valid:
            return from_vault

    return _load_from_env()
