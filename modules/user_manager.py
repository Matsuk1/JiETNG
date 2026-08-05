"""User lifecycle, preferences, nickname caching, and notice interactions."""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Optional

from modules.config_loader import BG_DIR
from modules.record_manager import delete_record
from modules.user_db import (
    create_user_if_missing,
    delete_user_from_db,
    get_all_user_ids,
    get_user,
    get_user_field,
    increment_user_field,
    remove_user_field,
    update_user_field,
)

logger = logging.getLogger(__name__)

SET_VALUE = 0
INCREMENT_VALUE = 1
DECREMENT_VALUE = 2
REMOVE_VALUE = 4
VALID_OPERATIONS = {SET_VALUE, INCREMENT_VALUE, DECREMENT_VALUE, REMOVE_VALUE}

NICKNAME_CACHE_TIMEOUT = 12 * 60 * 60
nickname_cache: dict[str, dict[str, Any]] = {}
nickname_cache_lock = threading.Lock()

NOTICE_VOTE_TYPES = {"support", "oppose"}
EMPTY_NOTICE_INTERACTION = {
    "read": False,
    "read_at": None,
    "vote": None,
    "voted_at": None,
}


def _now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_user(user_id: str) -> None:
    """Create a minimal user document without replacing an existing user."""
    create_user_if_missing(user_id, {"created_at": _now_string()})


def delete_user(user_id: str) -> None:
    """Delete a user, score records, cached nickname, and custom background."""
    delete_user_from_db(user_id)
    delete_record(user_id, recent=True)
    delete_record(user_id, recent=False)
    with nickname_cache_lock:
        nickname_cache.pop(user_id, None)

    background_path = os.path.join(BG_DIR, f"jietnguser_{user_id}.webp")
    try:
        os.remove(background_path)
    except FileNotFoundError:
        pass
    except OSError:
        logger.exception(
            "[UserManager] Failed to delete custom bg: user_id=%s", user_id
        )


def edit_user_value(
    user_id: str,
    key: str,
    word: Any,
    operation: int = SET_VALUE,
) -> None:
    """Set, increment, decrement, or remove one top-level user field."""
    if operation not in VALID_OPERATIONS:
        raise ValueError(f"Unsupported user edit operation: {operation}")
    add_user(user_id)

    if operation == SET_VALUE:
        update_user_field(user_id, key, word)
    elif operation == INCREMENT_VALUE:
        increment_user_field(user_id, key, word)
    elif operation == DECREMENT_VALUE:
        increment_user_field(user_id, key, -word)
    else:
        remove_user_field(user_id, key)


def get_user_timezone(user_id: str) -> int:
    """Return the user's UTC offset, defaulting to UTC+9."""
    return get_user_field(user_id, "timezone", 9)


def clear_user_value(key: str, word: Any, operation: int = SET_VALUE) -> None:
    """Apply one field operation to every user."""
    for user_id in get_all_user_ids():
        edit_user_value(user_id, key, word, operation)


def _get_cached_nickname(user_id: str) -> Optional[str]:
    with nickname_cache_lock:
        cached = nickname_cache.get(user_id)
        if cached is None:
            return None
        if time.monotonic() - cached["cached_at"] < NICKNAME_CACHE_TIMEOUT:
            return cached["nickname"]
        nickname_cache.pop(user_id, None)
    return None


def _cache_nickname(user_id: str, nickname: str) -> None:
    with nickname_cache_lock:
        nickname_cache[user_id] = {
            "nickname": nickname,
            "cached_at": time.monotonic(),
        }


def get_user_nickname(user_id: str, line_bot_api, use_cache: bool = True) -> str:
    """Fetch a LINE display name, with a twelve-hour in-process cache."""
    if use_cache:
        cached = _get_cached_nickname(user_id)
        if cached is not None:
            return cached

    try:
        nickname = line_bot_api.get_profile(user_id).display_name
    except Exception as exc:
        if "404" in str(exc):
            logger.warning("[User] User not found or blocked bot: user_id=%s", user_id)
            nickname = "Unknown (Blocked/Deleted)"
        else:
            logger.error(
                "[User] Failed to get nickname: user_id=%s error=%s", user_id, exc
            )
            nickname = "Unknown (API Error)"

    _cache_nickname(user_id, nickname)
    return nickname


def _notice_interactions(user_id: str) -> dict:
    interactions = get_user_field(user_id, "notice_interactions", {})
    return interactions if isinstance(interactions, dict) else {}


def _notice_interaction(interactions: dict, notice_id: str) -> dict:
    interaction = interactions.get(notice_id)
    if not isinstance(interaction, dict):
        interaction = dict(EMPTY_NOTICE_INTERACTION)
        interactions[notice_id] = interaction
    return interaction


def record_notice_read(user_id: str, notice_id: str) -> None:
    """Mark one notice as read without replacing unrelated user fields."""
    add_user(user_id)
    interactions = _notice_interactions(user_id)
    interaction = _notice_interaction(interactions, notice_id)
    interaction["read"] = True
    interaction["read_at"] = _now_string()
    update_user_field(user_id, "notice_interactions", interactions)


def record_notice_vote(user_id: str, notice_id: str, vote_type: str) -> bool:
    """Record a support/oppose vote and mark the notice as read."""
    if vote_type not in NOTICE_VOTE_TYPES or get_user(user_id) is None:
        return False

    now = _now_string()
    interactions = _notice_interactions(user_id)
    interaction = _notice_interaction(interactions, notice_id)
    interaction["vote"] = vote_type
    interaction["voted_at"] = now
    if not interaction.get("read"):
        interaction["read"] = True
        interaction["read_at"] = now
    update_user_field(user_id, "notice_interactions", interactions)
    return True


def get_notice_interaction(user_id: str, notice_id: str) -> Optional[dict]:
    """Return one user's interaction state for a notice."""
    interaction = _notice_interactions(user_id).get(notice_id)
    return interaction if isinstance(interaction, dict) else None


def has_user_read_notice(user_id: str, notice_id: str) -> bool:
    """Return true for missing users, otherwise the notice read state."""
    if get_user(user_id) is None:
        return True
    interaction = get_notice_interaction(user_id, notice_id)
    return bool(interaction and interaction.get("read"))


def clear_notice_read_status(notice_id: str) -> None:
    """Reset one notice's interaction state for every user."""
    for user_id in get_all_user_ids():
        interactions = _notice_interactions(user_id)
        interactions[notice_id] = dict(EMPTY_NOTICE_INTERACTION)
        update_user_field(user_id, "notice_interactions", interactions)


def clear_notice_record(notice_id: str) -> None:
    """Remove one notice's interaction state from every user."""
    for user_id in get_all_user_ids():
        interactions = _notice_interactions(user_id)
        if interactions.pop(notice_id, None) is not None:
            update_user_field(user_id, "notice_interactions", interactions)
