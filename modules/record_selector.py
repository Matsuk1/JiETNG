"""Record list filtering and selection for B-series image commands."""

import math
import re

from modules.config_loader import MAIMAI_VERSION
from modules.maimai_manager import parse_level_value
from modules.record_manager import get_ideal_score, get_single_ra


def _achievement_value(record):
    return float(str(record.get("score", "0")).replace("%", ""))


def _sun50_target(score):
    if 100.4000 <= score <= 100.4999:
        return 100.5000
    if 99.9000 <= score <= 99.9999:
        return 100.0000
    return None


def _sun50_sort_key(record):
    score = _achievement_value(record)
    target = _sun50_target(score) or 0
    return (
        round(target - score, 4),
        -float(record.get("internalLevelValue", 0) or 0),
        str(record.get("name", "")),
        str(record.get("difficulty", "")),
        str(record.get("type", "")),
    )


def _record_level_value(record):
    try:
        return float(record.get("internalLevelValue", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _parse_level_filter_values(raw_level):
    values = parse_level_value(str(raw_level).strip())
    if not values:
        return []
    return [float(v) for v in values]


def _filter_records_by_level(song_record, parts):
    if not parts:
        return song_record, None

    if len(parts) == 1:
        level_values = _parse_level_filter_values(parts[0])
        if not level_values:
            return song_record, None
        value_set = {round(v, 1) for v in level_values}
        filtered = [
            x for x in song_record
            if round(_record_level_value(x), 1) in value_set
        ]
        return filtered, str(parts[0])

    start_values = _parse_level_filter_values(parts[0])
    stop_values = _parse_level_filter_values(parts[1])
    if not start_values or not stop_values:
        return song_record, None

    lv_start = min(start_values)
    lv_stop = max(stop_values)
    if lv_start > lv_stop:
        lv_start, lv_stop = lv_stop, lv_start

    filtered = [
        x for x in song_record
        if lv_start <= _record_level_value(x) <= lv_stop
    ]
    return filtered, f"{parts[0]} ~ {parts[1]}"


def select_records(song_record, type="best50", command="", ver="jp"):
    page = 1
    times = 1
    sort_rule = lambda x: (x["ra"], float(x["score"][:-1]))
    filter_rules = [
        (lambda x: x["new_song"] is False),
        (lambda x: x["new_song"] is True),
    ]
    details = {}
    if command != "":
        cmds = re.findall(r"-(\w+)(?:\s+([^-]+))?", command)
        for cmd, cmd_num in cmds:
            if cmd in ["diff", "difficulty"]:
                diff_map = {
                    "bas": "basic",
                    "adv": "advanced",
                    "exp": "expert",
                    "mas": "master",
                    "rem": "remaster",
                }
                raw_diffs = cmd_num.split()
                difficulties = []
                for d in raw_diffs:
                    d_lower = d.strip().lower()
                    if d_lower:
                        if d_lower in diff_map:
                            difficulties.append(diff_map[d_lower])
                        elif d_lower in ["basic", "advanced", "expert", "master", "remaster"]:
                            difficulties.append(d_lower)
                if difficulties:
                    song_record = list(filter(
                        lambda x: x.get("difficulty", "").lower() in difficulties,
                        song_record,
                    ))
                    details["Diff"] = " ".join(d for d in difficulties)
            elif cmd in ["lv", "level"]:
                parts = cmd_num.split()
                filtered_records, detail = _filter_records_by_level(song_record, parts)
                song_record = filtered_records
                if detail:
                    details["Lv"] = detail
            elif cmd in ["next", "nxt"]:
                filter_rules = [
                    (lambda x: x["version"] != MAIMAI_VERSION[ver][-1]),
                    (lambda x: x["version"] == MAIMAI_VERSION[ver][-1]),
                ]
                details["NextVer"] = "ON"
            elif cmd in ["ra", "rating"]:
                parts = cmd_num.split()
                if len(parts) == 1:
                    ra = int(parts[0])
                    song_record = list(filter(lambda x: x["ra"] == ra, song_record))
                    details["RA"] = f"{ra}"
                else:
                    ra_start, ra_stop = map(int, parts[:2])
                    song_record = list(filter(lambda x: ra_start <= x["ra"] <= ra_stop, song_record))
                    details["RA"] = f"{ra_start} ~ {ra_stop}"
            elif cmd in ["dx", "dxscore"]:
                parts = cmd_num.split()
                if not len(parts):
                    sort_rule = lambda x: (x["dx_percentage"], float(x["score"][:-1]))
                    details["Sort"] = "DX Score"
                elif len(parts) == 1:
                    dx_percentage = int(re.sub(r"\D", "", parts[0]))
                    song_record = list(filter(lambda x: x["dx_percentage"] * 100 >= dx_percentage, song_record))
                    details["DxScr"] = f"\u2267 {dx_percentage}%"
                else:
                    dx_start = int(re.sub(r"\D", "", parts[0]))
                    dx_stop = int(re.sub(r"\D", "", parts[1]))
                    song_record = list(filter(
                        lambda x: dx_start <= x["dx_percentage"] * 100 <= dx_stop,
                        song_record,
                    ))
                    details["DxScr"] = f"{dx_start}% ~ {dx_stop}%"
            elif cmd in ["dxstar", "star"]:
                parts = cmd_num.split()
                if len(parts) == 1:
                    dx_star = int(re.sub(r"\D", "", parts[0]))
                    song_record = list(filter(lambda x: x["dx_star"] == dx_star, song_record))
                    details["Star"] = f"{dx_star}"
                else:
                    dx_start = int(re.sub(r"\D", "", parts[0]))
                    dx_stop = int(re.sub(r"\D", "", parts[1]))
                    song_record = list(filter(lambda x: dx_start <= x["dx_star"] <= dx_stop, song_record))
                    details["Star"] = f"{dx_start} ~ {dx_stop}"
            elif cmd in ["score", "scr"]:
                parts = cmd_num.split()
                if len(parts) == 1:
                    score = float(re.sub(r"[^0-9.]", "", parts[0]))
                    song_record = list(filter(
                        lambda x: float(x["score"].replace("%", "")) >= score,
                        song_record,
                    ))
                    details["Scr"] = f"\u2267 {score:.4f}%"
                else:
                    scr_start = float(re.sub(r"[^0-9.]", "", parts[0]))
                    scr_stop = float(re.sub(r"[^0-9.]", "", parts[1]))
                    song_record = list(filter(
                        lambda x: scr_start <= float(x["score"].replace("%", "")) <= scr_stop,
                        song_record,
                    ))
                    details["Scr"] = f"{scr_start}% ~ {scr_stop}%"
            elif cmd in ["ver", "version"]:
                raw_versions = cmd_num.split()
                versions = []
                for v in raw_versions:
                    if v.strip():
                        processed = (
                            v.strip()
                            .replace("+", " PLUS")
                            .lower()
                            .replace("dx", "maimai\u3067\u3089\u3063\u304f\u3059")
                            .replace("deluxe", "maimai\u3067\u3089\u3063\u304f\u3059")
                        )
                        versions.append(processed)
                song_record = list(filter(
                    lambda x: (x.get("version") or "").lower() in versions,
                    song_record,
                ))
                details["Ver"] = ""
                for version in versions:
                    plus = "plus" in version
                    details["Ver"] += (
                        version.lower()
                        .replace("maimai\u3067\u3089\u3063\u304f\u3059", "dx")
                        .replace("plus", "")[:3]
                        .strip()
                    )
                    if plus:
                        details["Ver"] += "+"
                    details["Ver"] += " "
            elif cmd in ["type", "tp"]:
                raw_types = [t.strip().lower() for t in cmd_num.split() if t.strip()]
                valid_types = []
                for t in raw_types:
                    if t in ("dx", "std"):
                        valid_types.append(t)
                if valid_types:
                    song_record = list(filter(lambda x: x.get("type", "").lower() in valid_types, song_record))
                    details["Type"] = " / ".join(t.upper() for t in valid_types)
            elif cmd in ["page", "pg"]:
                try:
                    page = max(1, int(cmd_num.strip()))
                    if page > 1:
                        details["Page"] = str(page)
                except ValueError:
                    pass
            elif cmd in ["times", "tm"]:
                parts = cmd_num.split()
                times = min(float(parts[0]), 2.5)
                if times > 0:
                    details["Times"] = times
                else:
                    times = 1

    up_songs = down_songs = []

    up_songs_data = list(filter(filter_rules[0], song_record))
    down_songs_data = list(filter(filter_rules[1], song_record))

    num_50 = math.ceil(50 * times / 5) * 5
    num_35 = math.ceil(35 * times / 5) * 5
    num_25 = math.ceil(25 * times / 5) * 5
    num_15 = math.ceil(15 * times / 5) * 5

    if type == "best50":
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_35: page * num_35]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_15: page * num_15]

    elif type == "best40":
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_25: page * num_25]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_15: page * num_15]

    elif type == "best35":
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_35: page * num_35]

    elif type == "best15":
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_15: page * num_15]

    elif type == "allb35":
        up_songs = sorted(song_record, key=sort_rule, reverse=True)[(page - 1) * num_35: page * num_35]

    elif type == "allb50":
        up_songs = sorted(song_record, key=sort_rule, reverse=True)[(page - 1) * num_50: page * num_50]

    elif type == "apb50":
        up_songs_data = [x for x in up_songs_data if x.get("combo_icon") in ("ap", "app")]
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_35: page * num_35]

        down_songs_data = [x for x in down_songs_data if x.get("combo_icon") in ("ap", "app")]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_15: page * num_15]

    elif type == "fdxb50":
        up_songs_data = [x for x in up_songs_data if x.get("sync_icon") in ("fdx", "fdxp")]
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_35: page * num_35]

        down_songs_data = [x for x in down_songs_data if x.get("sync_icon") in ("fdx", "fdxp")]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_15: page * num_15]

    elif type == "unknown":
        up_songs = list(filter(lambda x: x["version"] == "UNKNOWN", song_record))

    elif type == "rct50":
        up_songs = song_record

    elif type == "idlb50":
        for rcd in up_songs_data:
            ideal_score, score_icon = get_ideal_score(float(rcd["score"][:-1]))
            rcd["score"] = f"{ideal_score:.4f}%"
            if score_icon:
                rcd["score_icon"] = score_icon
            if ideal_score == 101:
                rcd["combo_icon"] = "app"
            rcd["ra"] = get_single_ra(rcd["internalLevelValue"], ideal_score, ideal_score == 101)

        for rcd in down_songs_data:
            ideal_score, score_icon = get_ideal_score(float(rcd["score"][:-1]))
            rcd["score"] = f"{ideal_score:.4f}%"
            if score_icon:
                rcd["score_icon"] = score_icon
            if ideal_score == 101:
                rcd["combo_icon"] = "app"
            rcd["ra"] = get_single_ra(rcd["internalLevelValue"], ideal_score, ideal_score == 101)

        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_35: page * num_35]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page - 1) * num_15: page * num_15]

    elif type == "sun50":
        sun_songs_data = [
            x for x in song_record
            if _sun50_target(_achievement_value(x)) is not None
        ]
        sun_songs = sorted(sun_songs_data, key=_sun50_sort_key)[(page - 1) * num_50: page * num_50]
        up_songs = [x for x in sun_songs if _sun50_target(_achievement_value(x)) == 100.5000]
        down_songs = [x for x in sun_songs if _sun50_target(_achievement_value(x)) == 100.0000]

    else:
        return select_records(song_record, "best50", command, ver)

    return up_songs, down_songs, details
