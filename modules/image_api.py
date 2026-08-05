import base64
import gc
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Callable

from flask import Blueprint, jsonify, request, send_file

from modules.api_auth import check_user_permission, require_dev_token
from modules.command_config import RANK_COMMANDS
from modules.config_loader import TEMP_VERSION, read_dxdata
from modules.event_tracker import track_event
from modules.image_manager import compose_images
from modules.rate_limiter import check_rate_limit
from modules.record_generator import (
    generate_cover,
    generate_level_rank_progress_image,
    generate_plate_image,
    generate_records_picture,
)
from modules.record_manager import read_record
from modules.song_generator import song_info_generate
from modules.song_matcher import normalize_text
from modules.user_manager import get_user_timezone


logger = logging.getLogger(__name__)
image_api = Blueprint("image_api", __name__)


@dataclass(frozen=True)
class ImageApiServices:
    background_filter: Callable
    generate_profile: Callable
    select_records: Callable


_services: ImageApiServices | None = None


def configure_image_api(*, background_filter, generate_profile, select_records):
    global _services
    _services = ImageApiServices(background_filter, generate_profile, select_records)


def _send_image_response(buf):
    """根据 format 参数返回图片（png 或 base64 JSON）"""
    fmt = request.args.get('format', 'png').strip().lower()
    if fmt == 'base64':
        img_data = base64.b64encode(buf.getvalue()).decode()
        buf.close()
        return jsonify({"success": True, "format": "base64", "image": img_data})
    return send_file(buf, mimetype="image/png")


@image_api.route("/api/v2/songs/<song_id>/image", methods=["GET"])
@require_dev_token
def api_v2_song_info(song_id):
    """
    生成歌曲信息图片 API

    需要 Bearer Token 认证

    参数:
    - ver: 服务器版本 jp/intl (默认 jp)

    返回: image/png
    """
    try:
        token_info = request.token_info
        if check_rate_limit(token_info['token_id'], "api_song_info_image"):
            return jsonify({"error": "Rate limited", "message": "Too many image requests. Please retry later."}), 429

        ver = request.args.get('ver', 'jp').strip().lower()
        if ver not in ('jp', 'intl'):
            return jsonify({"error": "Invalid ver, must be jp or intl"}), 400

        songs, _ = read_dxdata(ver)
        matching_song = None
        for song in songs:
            if song.get('id') == song_id:
                matching_song = song
                break

        if not matching_song:
            return jsonify({"error": "Song not found"}), 404

        song_img = song_info_generate(matching_song, ver=ver)

        buf = BytesIO()
        song_img.save(buf, "PNG")
        buf.seek(0)
        del song_img
        gc.collect(0)

        logger.info(f"[API] Song info generated: song_id={song_id}, ver={ver}, token_id={token_info['token_id']}")
        track_event('image_gen', user_id=None, metadata={'command': 'song-info', 'song_id': song_id, 'ver': ver})
        return _send_image_response(buf)

    except Exception as e:
        logger.error(f"[API] ✗ Song info error: song_id={song_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@image_api.route("/api/v2/users/<user_id>/songs/<song_id>/image", methods=["GET"])
@require_dev_token
def api_v2_song_record(user_id, song_id):
    """
    生成用户歌曲记录图片 API

    需要 Bearer Token 认证

    返回: image/png（包含用户在该歌曲各难度的游玩记录）
    """
    try:
        token_info = request.token_info
        if check_rate_limit(user_id, "api_song_record_image"):
            return jsonify({"error": "Rate limited", "message": "Too many image requests. Please retry later."}), 429

        has_permission, result = check_user_permission(user_id, token_info['token_id'])
        if not has_permission:
            return result

        _udata = result
        if "personal_info" not in _udata:
            return jsonify({"error": "User info not found, please sync first"}), 404

        ver = _udata.get("version", "jp")
        songs, _ = read_dxdata(ver)
        matching_song = None
        for song in songs:
            if song.get('id') == song_id:
                matching_song = song
                break

        if not matching_song:
            return jsonify({"error": "Song not found"}), 404

        song_record = read_record(user_id, ver=ver)
        if not song_record:
            return jsonify({"error": "No records found, please sync first"}), 404

        played_data = []
        for rcd in song_record:
            if rcd['cover_name'] == matching_song['cover_name'] and rcd['type'] == matching_song['type']:
                played_data.append(rcd)

        if not played_data:
            return jsonify({"error": "No record for this song"}), 404

        user_tz = get_user_timezone(user_id)
        song_img = song_info_generate(matching_song, played_data, timezone_offset=user_tz, ver=ver, bg_filter=_services.background_filter(user_id))

        buf = BytesIO()
        song_img.save(buf, "PNG")
        buf.seek(0)
        del song_img
        gc.collect(0)

        logger.info(f"[API] Song record generated: user_id={user_id}, song_id={song_id}, token_id={token_info['token_id']}")
        track_event('image_gen', user_id=user_id, metadata={'command': 'song-record'})
        return _send_image_response(buf)

    except Exception as e:
        logger.error(f"[API] ✗ Song record error: user_id={user_id}, song_id={song_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@image_api.route("/api/v2/users/<user_id>/image", methods=["GET"])
@require_dev_token
def api_v2_generate_record_image(user_id):
    """
    生成用户成绩图片 API (v2)

    需要 Bearer Token 认证

    参数:
    - command: 命令字符串，如 b50, rct50, apb50 等（默认 b50）

    返回: image/png
    """
    try:
        token_info = request.token_info
        if check_rate_limit(user_id, "api_record_image"):
            return jsonify({"error": "Rate limited", "message": "Too many image requests. Please retry later."}), 429

        has_permission, result = check_user_permission(user_id, token_info['token_id'])
        if not has_permission:
            return result

        _udata = result
        if "personal_info" not in _udata:
            return jsonify({"error": "User info not found, please sync first"}), 404

        command = request.args.get('command', 'b50').strip().lower()
        parts = re.split(r"[ \n]", command, 1)
        first_word = parts[0]
        rest_text = parts[1] if len(parts) > 1 else ""

        ver = _udata.get("version", "jp")

        record_type = None
        for aliases, mode in RANK_COMMANDS.items():
            if isinstance(aliases, tuple):
                if first_word in aliases:
                    record_type = mode
                    break
            else:
                if first_word == aliases:
                    record_type = mode
                    break

        if not record_type:
            return jsonify({"error": f"Unknown command: {command}",
                            "available": [a for aliases in RANK_COMMANDS for a in (aliases if isinstance(aliases, tuple) else (aliases,))]}), 400

        recent = (record_type == "rct50")
        recent_type = (record_type == "best40")
        song_record = read_record(user_id, recent, recent_type, ver=ver)
        if not song_record:
            return jsonify({"error": "No records found, please sync first"}), 404

        up_songs, down_songs, details = _services.select_records(song_record, record_type, rest_text, ver)
        if not up_songs and not down_songs:
            return jsonify({"error": "No matching records for this command"}), 404

        display_type = "未だ知らず" if record_type == "unknown" else record_type
        record_img = generate_records_picture(up_songs, down_songs, display_type.upper(), ver, details)
        user_info = _udata.get('personal_info')
        profile_img = _services.generate_profile(user_info, user_id=user_id)
        user_tz = get_user_timezone(user_id)
        img = compose_images([profile_img, record_img], timezone_offset=user_tz, bg_filter=_services.background_filter(user_id))
        del profile_img, record_img
        gc.collect(0)

        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        del img
        gc.collect(0)

        logger.info(f"[API] v2 Image generated: user_id={user_id}, command={command}, token_id={token_info['token_id']}")
        track_event('image_gen', user_id=user_id, metadata={'command': command, 'source': 'api'})
        return _send_image_response(buf)

    except Exception as e:
        logger.error(f"[API] ✗ v2 Generate image error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@image_api.route("/api/v2/users/<user_id>/plate", methods=["GET"])
@require_dev_token
def api_v2_generate_plate(user_id):
    """
    生成段位牌图片 API

    需要 Bearer Token 认证

    参数:
    - title: 牌子名称

    返回: image/png
    """
    try:
        token_info = request.token_info
        if check_rate_limit(user_id, "api_plate_image"):
            return jsonify({"error": "Rate limited", "message": "Too many image requests. Please retry later."}), 429

        has_permission, result = check_user_permission(user_id, token_info['token_id'])
        if not has_permission:
            return result

        _udata = result
        if "personal_info" not in _udata:
            return jsonify({"error": "User info not found, please sync first"}), 404

        title = request.args.get('title', '').strip()
        if not title:
            return jsonify({"error": "title parameter is required"}), 400
        if not (len(title) == 2 or len(title) == 3):
            return jsonify({"error": "Invalid title length, must be 2 or 3 characters"}), 400

        ver = _udata.get("version", "jp")
        song_record = read_record(user_id, ver=ver)
        if not song_record:
            return jsonify({"error": "No records found, please sync first"}), 404

        title = title.replace("晓", "暁").replace("极", "極")

        version_name = title[0]
        plate_type = title[1:]

        songs, versions = read_dxdata(ver)
        target_version = []
        if version_name in TEMP_VERSION["abbr"]:
            target_version.append(TEMP_VERSION["title"])
        for version in versions:
            if version_name in version['abbr']:
                target_version.append(version['version'])

        if not target_version:
            return jsonify({"error": "Version not found"}), 404

        if plate_type == "極":
            target_type, target_icon = "combo", ["fc", "fcp", "ap", "app"]
        elif plate_type == "将":
            target_type, target_icon = "score", ["sss", "sssp"]
        elif plate_type == "神":
            target_type, target_icon = "combo", ["ap", "app"]
        elif plate_type == "舞舞":
            target_type, target_icon = "sync", ["fdx", "fdxp"]
        else:
            return jsonify({"error": "Invalid plate type, must be 極/将/神/舞舞"}), 400

        version_rcd_data = list(filter(lambda x: x['version'] in target_version, song_record))
        if not version_rcd_data:
            return jsonify({"error": "No version records found"}), 404

        target_data = []
        target_num = {d: {'all': 0, 'clear': 0} for d in ['basic', 'advanced', 'expert', 'master']}

        rcd_map = {}
        for rcd in version_rcd_data:
            key1 = (rcd['name'], rcd['difficulty'], rcd['type'])
            rcd_map[key1] = rcd
            key2 = (normalize_text(rcd['name']), rcd['difficulty'], rcd['type'])
            rcd_map[key2] = rcd

        for song in songs:
            if song['version'] not in target_version or song['type'] == 'utage':
                continue
            for sheet in song['sheets']:
                if not sheet['regions'].get(ver, False) or sheet['difficulty'] not in target_num:
                    continue
                icon = "back"
                achieved = False
                achievement_rate = 0.0
                target_num[sheet['difficulty']]['all'] += 1
                song_title = song['title']
                difficulty = sheet['difficulty']
                song_type = song['type']

                rcd = rcd_map.get((song_title, difficulty, song_type)) or \
                      rcd_map.get((normalize_text(song_title), difficulty, song_type))
                if rcd:
                    icon = rcd[f'{target_type}_icon']
                    score_str = rcd.get('score', '0.0000%')
                    achievement_rate = float(score_str[:-1]) if score_str.endswith('%') else 0.0
                    if icon in target_icon:
                        target_num[difficulty]['clear'] += 1
                        achieved = True

                if difficulty == "master":
                    complete_info = {}
                    for diff in ["basic", "advanced", "expert", "master"]:
                        d_rcd = rcd_map.get((song_title, diff, song_type)) or \
                                rcd_map.get((normalize_text(song_title), diff, song_type))
                        complete_info[diff] = d_rcd is not None and d_rcd[f'{target_type}_icon'] in target_icon

                    target_data.append({
                        "img": generate_cover(song['cover_url'], song_type, icon, target_type,
                                              cover_name=song.get('cover_name'), complete_info=complete_info, achieved=achieved),
                        "level": sheet['level'],
                        "achieved": achieved,
                        "achievement_rate": achievement_rate
                    })

        plate_img = generate_plate_image(target_data, title, headers=target_num)
        for entry in target_data:
            entry.pop("img", None)
        del target_data

        user_info = _udata.get('personal_info')
        profile_img = _services.generate_profile(user_info, user_id=user_id)
        user_tz = get_user_timezone(user_id)
        img = compose_images([profile_img, plate_img], timezone_offset=user_tz, bg_filter=_services.background_filter(user_id))
        del profile_img, plate_img
        gc.collect(0)

        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        del img
        gc.collect(0)

        logger.info(f"[API] Plate generated: user_id={user_id}, title={title}, token_id={token_info['token_id']}")
        track_event('image_gen', user_id=user_id, metadata={'command': 'plate'})
        return _send_image_response(buf)

    except Exception as e:
        logger.error(f"[API] ✗ Generate plate error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@image_api.route("/api/v2/users/<user_id>/achievement", methods=["GET"])
@require_dev_token
def api_v2_generate_achievement(user_id):
    """
    生成达成状况图片 API

    需要 Bearer Token 认证

    参数:
    - level: 等级，如 11, 12+, 13, 14+, 15
    - rank: 可选，评级，如 sss, sss+, ap, ap+, fdx, fc 等

    返回: image/png
    """
    try:
        token_info = request.token_info
        if check_rate_limit(user_id, "api_achievement_image"):
            return jsonify({"error": "Rate limited", "message": "Too many image requests. Please retry later."}), 429

        has_permission, result = check_user_permission(user_id, token_info['token_id'])
        if not has_permission:
            return result

        _udata = result
        if "personal_info" not in _udata:
            return jsonify({"error": "User info not found, please sync first"}), 404

        level = request.args.get('level', '').strip()
        rank = request.args.get('rank', None)
        if rank:
            rank = rank.strip().lower()

        supported_levels = ["11", "11+", "12", "12+", "13", "13+", "14", "14+", "15"]
        if level not in supported_levels:
            return jsonify({"error": f"Invalid level, supported: {supported_levels}"}), 400

        rank_mapping = {
            "s":    ("score", ["s", "sp", "ss", "ssp", "sss", "sssp"]),
            "s+":   ("score", ["sp", "ss", "ssp", "sss", "sssp"]),
            "ss":   ("score", ["ss", "ssp", "sss", "sssp"]),
            "ss+":  ("score", ["ssp", "sss", "sssp"]),
            "sss":  ("score", ["sss", "sssp"]),
            "sss+": ("score", ["sssp"]),
            "fc":   ("combo", ["fc", "fcp", "ap", "app"]),
            "fc+":  ("combo", ["fcp", "ap", "app"]),
            "ap":   ("combo", ["ap", "app"]),
            "ap+":  ("combo", ["app"]),
            "fdx":  ("sync", ["fdx", "fdxp"]),
            "fdx+": ("sync", ["fdxp"])
        }

        if rank is not None and rank not in rank_mapping:
            return jsonify({"error": f"Invalid rank, supported: {list(rank_mapping.keys())}"}), 400

        ver = _udata.get("version", "jp")
        target_type, target_icons = rank_mapping[rank] if rank else (None, None)

        song_record = read_record(user_id, ver=ver)
        if not song_record:
            return jsonify({"error": "No records found, please sync first"}), 404

        rcd_map = {}
        for rcd in song_record:
            key1 = (rcd['name'], rcd['difficulty'], rcd['type'])
            rcd_map[key1] = rcd
            key2 = (normalize_text(rcd['name']), rcd['difficulty'], rcd['type'])
            rcd_map[key2] = rcd

        target_data = []
        total_charts = achieved_count = unachieved_count = unplayed_count = 0

        songs, _ = read_dxdata(ver)
        for song in songs:
            if song['type'] == 'utage':
                continue
            for sheet in song['sheets']:
                if not sheet['regions'].get(ver, False):
                    continue
                if level == "14+":
                    if sheet['level'] not in ["14+", "15"]:
                        continue
                else:
                    if sheet['level'] != level:
                        continue

                difficulty = sheet['difficulty']
                total_charts += 1
                song_title = song['title']
                song_type = song['type']
                icon = "back"
                achieved = False
                has_record = False
                achievement_rate = 0.0

                rcd = rcd_map.get((song_title, difficulty, song_type)) or \
                      rcd_map.get((normalize_text(song_title), difficulty, song_type))
                if rcd:
                    has_record = True
                    score_str = rcd.get('score', '0.0000%')
                    achievement_rate = float(score_str[:-1]) if score_str.endswith('%') else 0.0
                    if rank is not None:
                        user_icon = rcd.get(f'{target_type}_icon', "back")
                        icon = user_icon
                        if user_icon in target_icons:
                            achieved = True
                            achieved_count += 1
                        else:
                            unachieved_count += 1
                    else:
                        achieved = True
                        achieved_count += 1

                if not has_record:
                    unplayed_count += 1

                target_data.append({
                    "img": generate_cover(song['cover_url'], song_type, icon if rank else None,
                                          target_type if rank else None,
                                          cover_name=song.get('cover_name'), difficulty=difficulty,
                                          achieved=achieved if rank else None,
                                          song_title=song_title),
                    "level": sheet["level"],
                    "internal_level": sheet['internalLevelValue'],
                    "achieved": achieved,
                    "difficulty": difficulty,
                    "achievement_rate": achievement_rate
                })

        if not target_data:
            return jsonify({"error": "No matching data"}), 404

        level_display = level.replace("+", "⁺")
        rank_display = rank.upper().replace("+", "⁺") if rank else ""
        stats = {
            "achieved": achieved_count,
            "unachieved": unachieved_count,
            "unplayed": unplayed_count,
            "total": total_charts
        }

        record_img = generate_level_rank_progress_image(target_data, level_display, rank_display, stats)
        for entry in target_data:
            entry.pop("img", None)
        del target_data

        user_info = _udata.get('personal_info')
        profile_img = _services.generate_profile(user_info, scale=1.5, user_id=user_id)
        user_tz = get_user_timezone(user_id)
        img = compose_images([profile_img, record_img], timezone_offset=user_tz, bg_filter=_services.background_filter(user_id))
        del profile_img, record_img
        gc.collect(0)

        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        del img
        gc.collect(0)

        logger.info(f"[API] Achievement generated: user_id={user_id}, level={level}, rank={rank}, token_id={token_info['token_id']}")
        track_event('image_gen', user_id=user_id, metadata={'command': 'progress' if rank else 'level-list'})
        return _send_image_response(buf)

    except Exception as e:
        logger.error(f"[API] ✗ Generate achievement error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500



