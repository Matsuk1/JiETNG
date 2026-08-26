"""Developer-token storage and verification."""

import json
import logging
import os
import secrets
import threading
from datetime import datetime

from modules.config_loader import DEV_TOKENS_FILE

logger = logging.getLogger(__name__)

_tokens = None
_dirty = False
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_lock = threading.RLock()


def _mark_dirty():
    global _dirty
    _dirty = True


def load_dev_tokens():
    global _tokens, _dirty
    with _lock:
        if _tokens is not None:
            return _tokens
        try:
            with open(DEV_TOKENS_FILE, encoding="utf-8") as file:
                data = json.load(file)
            _tokens = data if isinstance(data, dict) else {}
        except FileNotFoundError:
            _tokens = {}
        except (OSError, json.JSONDecodeError):
            logger.exception("[DevToken] Failed to load tokens")
            _tokens = {}
        _dirty = False
        return _tokens


def save_dev_tokens(tokens=None, force=False):
    global _tokens, _dirty
    with _lock:
        if tokens is not None:
            _tokens = tokens
            _mark_dirty()
        if _tokens is None or (not force and not _dirty):
            return True

        temporary_file = f"{DEV_TOKENS_FILE}.tmp"
        try:
            directory = os.path.dirname(DEV_TOKENS_FILE)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(temporary_file, "w", encoding="utf-8") as file:
                json.dump(_tokens, file, ensure_ascii=False, indent=2)
            os.replace(temporary_file, DEV_TOKENS_FILE)
        except OSError:
            logger.exception("[DevToken] Failed to save tokens")
            return False

        _dirty = False
        logger.info("[DevToken] Saved %s tokens", len(_tokens))
        return True


def flush_dev_tokens():
    return save_dev_tokens(force=True)


def create_dev_token(note, created_by):
    with _lock:
        tokens = load_dev_tokens()
        token_id = f"jt_{secrets.token_hex(8)}"
        while token_id in tokens:
            token_id = f"jt_{secrets.token_hex(8)}"

        token = secrets.token_urlsafe(32)
        created_at = datetime.now().strftime(TIMESTAMP_FORMAT)
        tokens[token_id] = {
            "token": token,
            "note": note,
            "created_at": created_at,
            "created_by": created_by,
            "last_used": None,
            "revoked": False,
            "allowed_users": [],
        }
        _mark_dirty()
        if not save_dev_tokens(force=True):
            return None
        return {
            "token_id": token_id,
            "token": token,
            "note": note,
            "created_at": created_at,
        }


def list_dev_tokens():
    return [
        {
            "token_id": token_id,
            "note": data.get("note", ""),
            "created_at": data.get("created_at", ""),
            "created_by": data.get("created_by", ""),
            "last_used": data.get("last_used", "Never"),
            "revoked": data.get("revoked", False),
            "token_preview": f'{data.get("token", "")[:8]}...' if data.get("token") else "",
        }
        for token_id, data in load_dev_tokens().items()
    ]


def revoke_dev_token(token_id):
    with _lock:
        token = load_dev_tokens().get(token_id)
        if token is None:
            return False
        token["revoked"] = True
        _mark_dirty()
        return save_dev_tokens(force=True)


def verify_dev_token(token):
    with _lock:
        for token_id, data in load_dev_tokens().items():
            if data.get("token") != token or data.get("revoked", False):
                continue
            data["last_used"] = datetime.now().strftime(TIMESTAMP_FORMAT)
            _mark_dirty()
            return {
                "token_id": token_id,
                "note": data.get("note", ""),
                "created_by": data.get("created_by", ""),
            }
    return None
