"""Helpers for interpreting LINE message mentions."""

import logging
import re

from modules.user_db import user_exists

logger = logging.getLogger(__name__)


def _mentionees(event):
    mention = getattr(event.message, "mention", None)
    return getattr(mention, "mentionees", None) or ()


def clean_message_text(event):
    """Remove mention spans and return single-line and multiline text forms."""
    text = event.message.text
    for item in reversed(_mentionees(event)):
        start = getattr(item, "index", None)
        length = getattr(item, "length", None)
        if start is not None and length is not None:
            text = text[:start] + text[start + length:]

    text = text.replace("\ufffd", "")
    multiline = re.sub(r"[ \t]+", " ", text)
    multiline = re.sub(r" *\r?\n *", "\n", multiline).strip()
    return re.sub(r"\s+", " ", multiline).strip(), multiline


def should_ignore_mentions(event):
    """Ignore @ALL and messages targeting two or more non-bot users."""
    mentionees = _mentionees(event)
    user_id = event.source.user_id
    if any(getattr(item, "type", None) == "all" for item in mentionees):
        logger.info("[Mention] @ALL ignored: user_id=%s, text=%r", user_id, event.message.text)
        return True

    user_count = sum(not getattr(item, "is_self", False) for item in mentionees)
    if user_count >= 2:
        logger.info(
            "[Mention] Multiple users ignored: count=%s, user_id=%s, text=%r",
            user_count,
            user_id,
            event.message.text,
        )
        return True
    return False


def registered_mentioned_user_id(event, sender_id):
    """Return the first mentioned non-bot user registered in the service."""
    for item in _mentionees(event):
        if getattr(item, "is_self", False):
            continue
        user_id = getattr(item, "user_id", None)
        if user_id and user_exists(user_id):
            logger.info("[Mention] User mentioned: user_id=%s, mentioned_user_id=%s", sender_id, user_id)
            return user_id
        if user_id:
            logger.debug("[Mention] User not registered: mentioned_user_id=%s", user_id)
    return None


def has_non_bot_mention(event):
    return any(not getattr(item, "is_self", False) for item in _mentionees(event))
