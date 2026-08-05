"""Compatibility exports backed by language plugin catalogs."""

from modules.i18n import localized_catalog


welcome_msg_text = "『JiETNG・カヰテー』で有りんす。\nお願ひ申し候。"
group_welcome_msg_text = "『JiETNG・カヰテー』で有りんす。\nお出迎え有りんす。"


_messages = localized_catalog("messages")
globals().update(_messages)

__all__ = (
    "welcome_msg_text",
    "group_welcome_msg_text",
    *_messages,
)
