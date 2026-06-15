"""
User-scoped import token manager.

Import tokens are generated for one JiETNG user and can only upload processed
record payloads for that same user. Raw tokens are shown once; only SHA-256
hashes are stored in the user JSON document.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import datetime
from typing import Optional

from modules.user_db import get_user, save_user

_TOKEN_PREFIX = "jit_"
_TOKEN_BYTES = 32
_MAX_TOKENS_PER_USER = 5
_INDEX_FILE = "./data/import_tokens.json"
_index_lock = threading.Lock()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _load_index() -> dict:
    if not os.path.exists(_INDEX_FILE):
        return {}
    try:
        with open(_INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_index(index: dict) -> None:
    os.makedirs(os.path.dirname(_INDEX_FILE), exist_ok=True)
    with open(_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _active_tokens(user_data: dict) -> list[dict]:
    tokens = user_data.get("import_tokens", [])
    if not isinstance(tokens, list):
        return []
    return [item for item in tokens if isinstance(item, dict) and not item.get("revoked")]


def create_import_token(user_id: str, note: str = "") -> Optional[dict]:
    user_data = get_user(user_id)
    if not user_data:
        return None

    tokens = user_data.get("import_tokens", [])
    if not isinstance(tokens, list):
        tokens = []

    token_id = f"it_{secrets.token_hex(8)}"
    existing_ids = {item.get("token_id") for item in tokens if isinstance(item, dict)}
    while token_id in existing_ids:
        token_id = f"it_{secrets.token_hex(8)}"

    secret = secrets.token_urlsafe(_TOKEN_BYTES)
    token = f"{_TOKEN_PREFIX}{token_id}.{secret}"
    token_hash = _hash_token(token)

    revoked_token_ids = []
    active = _active_tokens({"import_tokens": tokens})
    if len(active) >= _MAX_TOKENS_PER_USER:
        oldest_active_id = active[0].get("token_id")
        for item in tokens:
            if item.get("token_id") == oldest_active_id:
                item["revoked"] = True
                item["revoked_at"] = _now()
                revoked_token_ids.append(oldest_active_id)
                break

    created_at = _now()
    tokens.append({
        "token_id": token_id,
        "token_hash": token_hash,
        "note": str(note or "")[:120],
        "created_at": created_at,
        "last_used": None,
        "revoked": False,
    })
    user_data["import_tokens"] = tokens
    save_user(user_id, user_data)

    with _index_lock:
        index = _load_index()
        for revoked_id in revoked_token_ids:
            if revoked_id in index:
                index[revoked_id]["revoked"] = True
                index[revoked_id]["revoked_at"] = created_at
        index[token_id] = {
            "user_id": user_id,
            "token_hash": token_hash,
            "created_at": created_at,
            "revoked": False,
        }
        _save_index(index)

    return {
        "token_id": token_id,
        "token": token,
        "note": str(note or "")[:120],
        "created_at": created_at,
    }


def list_import_tokens(user_id: str) -> Optional[list[dict]]:
    user_data = get_user(user_id)
    if not user_data:
        return None

    tokens = user_data.get("import_tokens", [])
    if not isinstance(tokens, list):
        return []

    result = []
    for item in tokens:
        if not isinstance(item, dict):
            continue
        result.append({
            "token_id": item.get("token_id"),
            "note": item.get("note", ""),
            "created_at": item.get("created_at"),
            "last_used": item.get("last_used"),
            "revoked": bool(item.get("revoked")),
        })
    return result


def revoke_import_token(user_id: str, token_id: str | None = None) -> int:
    user_data = get_user(user_id)
    if not user_data:
        return 0

    tokens = user_data.get("import_tokens", [])
    if not isinstance(tokens, list):
        return 0

    revoked = 0
    for item in tokens:
        if not isinstance(item, dict) or item.get("revoked"):
            continue
        if token_id and item.get("token_id") != token_id:
            continue
        item["revoked"] = True
        item["revoked_at"] = _now()
        revoked += 1

    if revoked:
        user_data["import_tokens"] = tokens
        save_user(user_id, user_data)
        with _index_lock:
            index = _load_index()
            for item in tokens:
                if not isinstance(item, dict):
                    continue
                tid = item.get("token_id")
                if tid in index and (not token_id or tid == token_id):
                    index[tid]["revoked"] = bool(item.get("revoked"))
                    index[tid]["revoked_at"] = item.get("revoked_at")
            _save_index(index)
    return revoked


def verify_import_token(token: str) -> Optional[dict]:
    if not token or not token.startswith(_TOKEN_PREFIX):
        return None

    try:
        token_body = token[len(_TOKEN_PREFIX):]
        token_id, _secret = token_body.split(".", 1)
    except Exception:
        return None

    token_hash = _hash_token(token)
    with _index_lock:
        index_item = _load_index().get(token_id)
    if not index_item or index_item.get("revoked"):
        return None
    if not hmac.compare_digest(str(index_item.get("token_hash", "")), token_hash):
        return None

    user_id = index_item.get("user_id")
    user_data = get_user(user_id) or {}
    tokens = user_data.get("import_tokens", [])
    if not isinstance(tokens, list):
        return None

    for item in tokens:
        if not isinstance(item, dict) or item.get("revoked"):
            continue
        if item.get("token_id") != token_id:
            continue
        if hmac.compare_digest(str(item.get("token_hash", "")), token_hash):
            item["last_used"] = _now()
            user_data["import_tokens"] = tokens
            save_user(user_id, user_data)
            return {
                "user_id": user_id,
                "token_id": item.get("token_id"),
                "note": item.get("note", ""),
            }

    return None
