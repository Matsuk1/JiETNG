"""Create and verify user-scoped import tokens without storing raw secrets."""

import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import datetime

from modules.user_db import get_user, save_user


TOKEN_PREFIX = "jit_"
TOKEN_BYTES = 32
MAX_TOKENS_PER_USER = 5
INDEX_FILE = "./data/import_tokens.json"
_token_lock = threading.RLock()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _user_tokens(user_data):
    tokens = user_data.get("import_tokens", [])
    return (
        [item for item in tokens if isinstance(item, dict)]
        if isinstance(tokens, list)
        else []
    )


def _load_index():
    if not os.path.exists(INDEX_FILE):
        return {}
    try:
        with open(INDEX_FILE, encoding="utf-8") as file:
            index = json.load(file)
        return index if isinstance(index, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_index(index):
    directory = os.path.dirname(INDEX_FILE)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temporary_file = f"{INDEX_FILE}.tmp"
    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(index, file, ensure_ascii=False, indent=2)
    os.replace(temporary_file, INDEX_FILE)


def _new_token_id(tokens):
    existing_ids = {item.get("token_id") for item in tokens}
    while True:
        token_id = f"it_{secrets.token_hex(8)}"
        if token_id not in existing_ids:
            return token_id


def create_import_token(user_id, note=""):
    with _token_lock:
        user_data = get_user(user_id)
        if not user_data:
            return None

        tokens = _user_tokens(user_data)
        token_id = _new_token_id(tokens)
        token = f"{TOKEN_PREFIX}{token_id}.{secrets.token_urlsafe(TOKEN_BYTES)}"
        token_hash = _hash_token(token)
        created_at = _now()
        note = str(note or "")[:120]

        active_tokens = [item for item in tokens if not item.get("revoked")]
        revoked_id = None
        if len(active_tokens) >= MAX_TOKENS_PER_USER:
            oldest = active_tokens[0]
            oldest.update(revoked=True, revoked_at=created_at)
            revoked_id = oldest.get("token_id")

        tokens.append(
            {
                "token_id": token_id,
                "token_hash": token_hash,
                "note": note,
                "created_at": created_at,
                "last_used": None,
                "revoked": False,
            }
        )
        user_data["import_tokens"] = tokens
        if not save_user(user_id, user_data):
            return None

        index = _load_index()
        if revoked_id in index:
            index[revoked_id].update(revoked=True, revoked_at=created_at)
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
            "note": note,
            "created_at": created_at,
        }


def list_import_tokens(user_id):
    with _token_lock:
        user_data = get_user(user_id)
        if not user_data:
            return None
        return [
            {
                "token_id": item.get("token_id"),
                "note": item.get("note", ""),
                "created_at": item.get("created_at"),
                "last_used": item.get("last_used"),
                "revoked": bool(item.get("revoked")),
            }
            for item in _user_tokens(user_data)
        ]


def revoke_import_token(user_id, token_id=None):
    with _token_lock:
        user_data = get_user(user_id)
        if not user_data:
            return 0

        tokens = _user_tokens(user_data)
        revoked_at = _now()
        changed = [
            item
            for item in tokens
            if not item.get("revoked")
            and (token_id is None or item.get("token_id") == token_id)
        ]
        if not changed:
            return 0
        for item in changed:
            item.update(revoked=True, revoked_at=revoked_at)

        user_data["import_tokens"] = tokens
        if not save_user(user_id, user_data):
            return 0
        index = _load_index()
        for item in changed:
            if item.get("token_id") in index:
                index[item["token_id"]].update(revoked=True, revoked_at=revoked_at)
        _save_index(index)
        return len(changed)


def delete_revoked_import_token(user_id, token_id):
    with _token_lock:
        user_data = get_user(user_id)
        if not user_data:
            return False
        tokens = _user_tokens(user_data)
        target = next(
            (
                item
                for item in tokens
                if item.get("token_id") == token_id and item.get("revoked")
            ),
            None,
        )
        if not target:
            return False

        user_data["import_tokens"] = [item for item in tokens if item is not target]
        if not save_user(user_id, user_data):
            return False
        index = _load_index()
        index.pop(token_id, None)
        _save_index(index)
        return True


def verify_import_token(token):
    if not token or not token.startswith(TOKEN_PREFIX):
        return None
    token_id, separator, secret = token[len(TOKEN_PREFIX) :].partition(".")
    if not separator or not token_id or not secret:
        return None

    token_hash = _hash_token(token)
    with _token_lock:
        index_item = _load_index().get(token_id)
        if not index_item or index_item.get("revoked"):
            return None
        if not hmac.compare_digest(str(index_item.get("token_hash", "")), token_hash):
            return None

        user_id = index_item.get("user_id")
        user_data = get_user(user_id) or {}
        item = next(
            (
                item
                for item in _user_tokens(user_data)
                if item.get("token_id") == token_id and not item.get("revoked")
            ),
            None,
        )
        if not item or not hmac.compare_digest(
            str(item.get("token_hash", "")), token_hash
        ):
            return None

        item["last_used"] = _now()
        save_user(user_id, user_data)
        return {"user_id": user_id, "token_id": token_id, "note": item.get("note", "")}
