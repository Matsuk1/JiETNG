"""Validation and normalization for web session score-image payloads."""


def normalize_session_profile(profile: dict, ver: str) -> dict:
    from modules.maimai_manager import get_rating_image_path

    base = "https://maimaidx-eng.com/maimai-mobile" if ver == "intl" else "https://maimaidx.jp/maimai-mobile"
    rating = str(profile.get("rating", "0")).strip() or "0"
    try:
        rating_int = int(rating)
    except (TypeError, ValueError):
        rating_int = 0

    return {
        "name": str(profile.get("name", "NAME_ERROR")).strip()[:64] or "NAME_ERROR",
        "rating": rating,
        "rating_block_path": get_rating_image_path(rating_int),
        "cource_rank_url": profile.get("cource_rank_url") or profile.get("course_rank_url") or "N/A",
        "class_rank_url": profile.get("class_rank_url") or "N/A",
        "icon_url": profile.get("icon_url") or "N/A",
        "nameplate_url": profile.get("nameplate_url") or "N/A",
        "trophy_url": profile.get("trophy_url") or f"{base}/img/trophy_rainbow.png",
        "trophy_content": str(profile.get("trophy_content", "N/A")).strip()[:80] or "N/A",
    }


def normalize_session_records(records: list) -> list:
    valid_difficulties = {"basic", "advanced", "expert", "master", "remaster"}
    valid_types = {"std", "dx", "utage"}
    normalized = []

    for record in records[:3000]:
        if not isinstance(record, dict):
            continue
        name = str(record.get("name", "")).strip()
        score = str(record.get("score", "")).strip()
        difficulty = str(record.get("difficulty", "")).strip().lower()
        music_type = str(record.get("type", "")).strip().lower()
        if not name or not score or difficulty not in valid_difficulties or music_type not in valid_types:
            continue

        normalized.append({
            "name": name[:160],
            "difficulty": difficulty,
            "type": music_type,
            "score": score if score.endswith("%") else f"{score}%",
            "dx_score": str(record.get("dx_score", "N/A")).replace(",", "").strip(),
            "score_icon": str(record.get("score_icon", "")).strip().lower(),
            "combo_icon": str(record.get("combo_icon", "")).strip().lower(),
            "sync_icon": str(record.get("sync_icon", "")).strip().lower(),
        })

    return normalized
