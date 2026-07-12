"""
LINE rich menu 状态切换工具。

运行时只负责把用户 link 到已创建的 rich menu；创建和上传图片由
scripts/setup_rich_menu.py 手动执行，避免应用启动时访问 LINE API。
"""

import logging
from typing import Optional

import requests

from modules.config_loader import (
    LINE_CHANNEL_ACCESS_TOKEN,
    RICH_MENU_BOUND_ID,
    RICH_MENU_DEFAULT_LANGUAGE,
    RICH_MENU_ENABLED,
    RICH_MENU_MENUS,
    RICH_MENU_UNBOUND_ID,
)

logger = logging.getLogger(__name__)

_LINE_API_BASE = "https://api.line.me/v2/bot"
_TIMEOUT = 8


def is_rich_menu_ready() -> bool:
    has_matrix = bool(RICH_MENU_MENUS and get_start_menu_id() and get_main_menu_id(RICH_MENU_DEFAULT_LANGUAGE))
    has_legacy = bool(RICH_MENU_UNBOUND_ID and RICH_MENU_BOUND_ID)
    return bool(RICH_MENU_ENABLED and LINE_CHANNEL_ACCESS_TOKEN and (has_matrix or has_legacy))


def normalize_rich_menu_language(language: Optional[str]) -> str:
    value = (language or RICH_MENU_DEFAULT_LANGUAGE or "zh").lower().replace("_", "-")
    if value in ("zh-tw", "zh-hk", "zh-mo", "tw"):
        return "zh-tw"
    if value.startswith("zh"):
        return "zh"
    if value.startswith("ja"):
        return "ja"
    if value.startswith("en"):
        return "en"
    return normalize_rich_menu_language(RICH_MENU_DEFAULT_LANGUAGE if value != RICH_MENU_DEFAULT_LANGUAGE else "zh")


def get_rich_menu_language(user_data: Optional[dict]) -> str:
    return normalize_rich_menu_language((user_data or {}).get("language"))


def _get_menu_id(page: str, language: Optional[str]) -> str:
    lang = normalize_rich_menu_language(language)
    menus = RICH_MENU_MENUS or {}
    return (
        menus.get(lang, {}).get(page)
        or menus.get(RICH_MENU_DEFAULT_LANGUAGE, {}).get(page)
        or menus.get("zh", {}).get(page)
        or ""
    )


def get_start_menu_id(language: Optional[str] = None) -> str:
    return (RICH_MENU_MENUS or {}).get("en", {}).get("start") or RICH_MENU_UNBOUND_ID


def get_main_menu_id(language: Optional[str] = None) -> str:
    return _get_menu_id("main", language) or RICH_MENU_BOUND_ID


def is_user_bound_for_rich_menu(user_data: Optional[dict]) -> bool:
    if not user_data:
        return False

    has_full_account = all(k in user_data for k in ("sega_id", "sega_pwd", "version"))
    has_import_account = bool(
        user_data.get("import_only")
        or user_data.get("auth_type") == "import_token"
        or user_data.get("import_tokens")
    )
    return has_full_account or has_import_account


def _headers() -> dict:
    return {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}


def link_rich_menu(user_id: str, rich_menu_id: str) -> bool:
    if not is_rich_menu_ready() or not user_id or not rich_menu_id:
        return False

    url = f"{_LINE_API_BASE}/user/{user_id}/richmenu/{rich_menu_id}"
    try:
        resp = requests.post(url, headers=_headers(), timeout=_TIMEOUT)
        if 200 <= resp.status_code < 300:
            logger.info("[RichMenu] Linked user_id=%s rich_menu_id=%s", user_id, rich_menu_id)
            return True
        logger.warning(
            "[RichMenu] Failed to link user_id=%s rich_menu_id=%s status=%s body=%s",
            user_id, rich_menu_id, resp.status_code, resp.text[:300],
        )
    except Exception as e:
        logger.warning("[RichMenu] Link error user_id=%s rich_menu_id=%s error=%s", user_id, rich_menu_id, e)
    return False


def link_rich_menu_for_state(user_id: str, user_data: Optional[dict]) -> bool:
    language = get_rich_menu_language(user_data)
    rich_menu_id = get_main_menu_id(language) if is_user_bound_for_rich_menu(user_data) else get_start_menu_id()
    return link_rich_menu(user_id, rich_menu_id)


def link_unbound_rich_menu(user_id: str, user_data: Optional[dict] = None) -> bool:
    return link_rich_menu(user_id, get_start_menu_id())


def link_bound_rich_menu(user_id: str, user_data: Optional[dict] = None) -> bool:
    return link_rich_menu(user_id, get_main_menu_id(get_rich_menu_language(user_data)))


def unlink_rich_menu(user_id: str) -> bool:
    if not is_rich_menu_ready() or not user_id:
        return False

    url = f"{_LINE_API_BASE}/user/{user_id}/richmenu"
    try:
        resp = requests.delete(url, headers=_headers(), timeout=_TIMEOUT)
        if resp.status_code in (200, 404):
            logger.info("[RichMenu] Unlinked user_id=%s", user_id)
            return True
        logger.warning("[RichMenu] Failed to unlink user_id=%s status=%s body=%s", user_id, resp.status_code, resp.text[:300])
    except Exception as e:
        logger.warning("[RichMenu] Unlink error user_id=%s error=%s", user_id, e)
    return False
