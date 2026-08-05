"""Parsing helpers for level and category progress commands."""

import re

PROGRESS_RANK_PATTERN = r"(sss\+|ss\+|s\+|ap\+|fc\+|fdx\+|sss|ss|ap|fc|fdx|s)"

PROGRESS_CATEGORY_ALIASES = {
    "vocaloid": "niconico＆ボーカロイド",
    "popani": "POPS＆アニメ",
    "touhou": "東方Project",
    "gekichu": "オンゲキ＆CHUNITHM",
    "game": "ゲーム＆バラエティ",
    "maimai": "maimai",
}


def resolve_progress_category(target):
    return PROGRESS_CATEGORY_ALIASES.get(str(target or "").strip().lower())


def parse_level_rank_progress(text):
    body = re.sub(r"\s+", " ", text.strip().lower())
    body = re.sub(r"\s*-(uc|up|c)\s*$", "", body).strip()
    body = re.sub(r"\s*(progress|進捗|进度)\s*$", "", body).strip()
    match = re.search(fr"{PROGRESS_RANK_PATTERN}\s*$", body)
    if not match:
        return None, None
    return body[:match.start()].strip(), match.group(1)
