"""Manage localized tips and ads shown after selected bot responses."""

import json
import logging
import os
import random
import threading
from datetime import datetime

from modules.config_loader import TIP_AD_FILE


logger = logging.getLogger(__name__)
TIP_AD_DATA = []
_enabled_items = {"tip": [], "ad": []}
_data_lock = threading.RLock()
_loaded = False


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _rebuild_cache():
    global _enabled_items
    _enabled_items = {
        item_type: [
            item
            for item in TIP_AD_DATA
            if item.get("enabled", True) and item.get("type") == item_type
        ]
        for item_type in ("tip", "ad")
    }


def _save_locked():
    directory = os.path.dirname(TIP_AD_FILE)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temporary_file = f"{TIP_AD_FILE}.tmp"
    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(TIP_AD_DATA, file, ensure_ascii=False, indent=2)
    os.replace(temporary_file, TIP_AD_FILE)
    _rebuild_cache()


def load_tip_ad_data():
    global TIP_AD_DATA, _loaded
    with _data_lock:
        try:
            if os.path.exists(TIP_AD_FILE):
                with open(TIP_AD_FILE, encoding="utf-8") as file:
                    loaded = json.load(file)
                TIP_AD_DATA = (
                    [item for item in loaded if isinstance(item, dict)]
                    if isinstance(loaded, list)
                    else []
                )
            else:
                TIP_AD_DATA = []
                _save_locked()
            _loaded = True
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load tip/ad data: %s", exc, exc_info=True)
            TIP_AD_DATA = []
            _loaded = True
        _rebuild_cache()
        return TIP_AD_DATA


def _ensure_loaded():
    if not _loaded:
        load_tip_ad_data()


def save_tip_ad_data():
    with _data_lock:
        try:
            _save_locked()
            return True
        except OSError as exc:
            logger.error("Failed to save tip/ad data: %s", exc, exc_info=True)
            return False


def get_all_tip_ads():
    with _data_lock:
        _ensure_loaded()
        return TIP_AD_DATA.copy()


def _random_enabled(item_type):
    with _data_lock:
        _ensure_loaded()
        items = _enabled_items[item_type]
        return random.choice(items) if items and random.random() <= 0.75 else None


def get_random_tip():
    return _random_enabled("tip")


def get_random_ad():
    return _random_enabled("ad")


def _button(button_type, button_value, labels):
    if not button_type or not button_value:
        return None
    return {
        "type": button_type,
        "label": dict(labels or {}),
        "value": button_value,
    }


def _new_id():
    existing_ids = {item.get("id") for item in TIP_AD_DATA}
    base = str(int(datetime.now().timestamp()))
    item_id = base
    suffix = 1
    while item_id in existing_ids:
        item_id = f"{base}_{suffix}"
        suffix += 1
    return item_id


def create_tip_ad(
    tip_type,
    text,
    button_type=None,
    button_labels=None,
    button_value=None,
    enabled=True,
):
    with _data_lock:
        _ensure_loaded()
        timestamp = _now()
        item = {
            "id": _new_id(),
            "type": tip_type,
            "text": dict(text),
            "enabled": enabled,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        button = _button(button_type, button_value, button_labels)
        if button:
            item["button"] = button
        TIP_AD_DATA.append(item)
        return item if save_tip_ad_data() else None


def update_tip_ad(
    tip_ad_id,
    tip_type=None,
    text=None,
    button_type=None,
    button_labels=None,
    button_value=None,
    enabled=None,
    remove_button=False,
):
    with _data_lock:
        _ensure_loaded()
        item = next((item for item in TIP_AD_DATA if item.get("id") == tip_ad_id), None)
        if not item:
            return None

        if tip_type is not None:
            item["type"] = tip_type
        if text:
            item.setdefault("text", {}).update(text)
        if enabled is not None:
            item["enabled"] = enabled
        if remove_button:
            item.pop("button", None)
        else:
            button = _button(button_type, button_value, button_labels)
            if button:
                item["button"] = button
        item["updated_at"] = _now()
        return item if save_tip_ad_data() else None


def delete_tip_ad(tip_ad_id):
    global TIP_AD_DATA
    with _data_lock:
        _ensure_loaded()
        remaining = [item for item in TIP_AD_DATA if item.get("id") != tip_ad_id]
        if len(remaining) == len(TIP_AD_DATA):
            return False
        TIP_AD_DATA = remaining
        return save_tip_ad_data()


def get_tip_ad_by_id(tip_ad_id):
    with _data_lock:
        _ensure_loaded()
        item = next((item for item in TIP_AD_DATA if item.get("id") == tip_ad_id), None)
        return item.copy() if item else None
