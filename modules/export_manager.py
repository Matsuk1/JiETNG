"""
成绩导出管理 / Records Export Manager

把 best_records / recent_records 加工成阅读友好的结构（rank 写人话、
dx_score 拆成当前/上限、icon 翻成 FC+/AP+ 等），再以 JSON 或 XML
落盘到 EXPORT_DIR；返回 30 分钟内可访问的下载 URL + 元数据（条数、
体积）。

清理策略：单个全局周期线程（默认每 5 分钟扫一次）按 mtime 删过期文件，
重启可自愈，避免「每文件 1 sleep 30 分钟守护线程」的浪费与重启失忆问题。
"""

import json
import logging
import os
import re
import secrets
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from modules.config_loader import EXPORT_DIR, DOMAIN
from modules.record_manager import read_record
from modules.user_db import get_user_field

logger = logging.getLogger(__name__)

_EXPORT_TTL_SECONDS = 1800           # 30 min
_MAX_PAYLOAD_BYTES = 20 * 1024 * 1024  # 20 MB 保险阀

_periodic_cleanup_thread: Optional[threading.Thread] = None
_periodic_cleanup_lock = threading.Lock()


def _ensure_dir():
    """仅在写文件时确保目录存在，避免 import 时副作用。"""
    os.makedirs(EXPORT_DIR, exist_ok=True)


# ----------------------------------------------------------------------------
# 友好文件名 / Friendly download filename
# ----------------------------------------------------------------------------

_UNSAFE_FILENAME_CHARS_RE = re.compile(r'[\/\\?%*:|"<>\x00-\x1f\s]+')


def _slugify(name: str, max_len: int = 30) -> str:
    """把任意字符串规整成可放进文件名/URL 的 slug；保留 CJK。"""
    if not name:
        return "user"
    cleaned = _UNSAFE_FILENAME_CHARS_RE.sub("-", str(name)).strip("-")
    cleaned = cleaned[:max_len].rstrip("-")
    return cleaned or "user"


def _build_friendly_name(profile: dict, fmt: str) -> str:
    """生成 'JiETNG-{玩家名}-{YYYYMMDD-HHMMSS}.{ext}' 形式的下载文件名。"""
    p = profile or {}
    name = p.get("name") or p.get("line_nickname") or "user"
    slug = _slugify(name)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"JiETNG-{slug}-{ts}.{fmt}"


# ----------------------------------------------------------------------------
# 数据加工 / Data transform
# ----------------------------------------------------------------------------

# 谱面排名图标 → 人话
_RANK_MAP = {
    "sssp": "SSS+", "sss": "SSS",
    "ssp":  "SS+",  "ss":  "SS",
    "sp":   "S+",   "s":   "S",
    "aaa":  "AAA",  "aa":  "AA",  "a": "A",
    "bbb":  "BBB",  "bb":  "BB",  "b": "B",
    "c":    "C",    "d":   "D",
}

# Combo 图标；"back" = 该项无成就，导出时省略
_COMBO_MAP = {"app": "AP+", "ap": "AP", "fcp": "FC+", "fc": "FC", "back": None}

# Sync 图标；"back" = 该项无成就，导出时省略
_SYNC_MAP = {"fdxp": "FDX+", "fdx": "FDX", "fsp": "FS+", "fs": "FS",
             "sync": "Sync", "back": None}

_TYPE_MAP = {"dx": "DX", "std": "Standard", "utage": "Utage"}

_DIFF_MAP = {
    "basic":    "Basic",    "advanced": "Advanced",  "expert": "Expert",
    "master":   "Master",   "remaster": "Re:Master", "utage":  "Utage",
}

_DX_SCORE_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")


def _parse_dx_score_pair(s):
    """ '2950 / 3000' -> (2950, 3000)；解析失败 (None, None) """
    m = _DX_SCORE_RE.match(str(s or ""))
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def _parse_achievement(s):
    """ '100.5000%' -> 100.5000 """
    try:
        return float(str(s).rstrip("%").strip())
    except (ValueError, AttributeError, TypeError):
        return None


def _transform_record(r: dict) -> dict:
    """单条原始 DB 记录 → 阅读友好版本。None 字段会被剔除。"""
    out: dict = {
        "title":          r.get("name"),
        "type":           _TYPE_MAP.get(r.get("type"), r.get("type")),
        "difficulty":     _DIFF_MAP.get(r.get("difficulty"), r.get("difficulty")),
        "internal_level": r.get("internalLevelValue"),
        "version":        r.get("version"),
        "is_new_song":    bool(r.get("new_song", False)),
        "achievement":    _parse_achievement(r.get("score")),
        "rank":           _RANK_MAP.get(r.get("score_icon"), r.get("score_icon")),
        "song_rating":    r.get("ra"),
        "dx_star":        r.get("dx_star"),
    }

    # dx_score 拆成当前/上限两个 int
    cur, mx = _parse_dx_score_pair(r.get("dx_score"))
    if cur is not None:
        out["dx_score"] = cur
        out["dx_score_max"] = mx
        # dx_percentage 改成百分数（0~100），更直观
        if r.get("dx_percentage") is not None:
            out["dx_percentage"] = round(float(r["dx_percentage"]) * 100, 2)

    combo = _COMBO_MAP.get(r.get("combo_icon"), r.get("combo_icon"))
    if combo:
        out["combo"] = combo

    sync = _SYNC_MAP.get(r.get("sync_icon"), r.get("sync_icon"))
    if sync:
        out["sync"] = sync

    # 谱面封面 URL（导出后用户可外部渲染）
    if r.get("cover_url"):
        out["cover_url"] = r.get("cover_url")

    # 滤掉 None / 空键
    return {k: v for k, v in out.items() if v is not None}


def _transform_profile(p: dict, user_id: str) -> dict:
    """personal_info → 阅读友好版本（剔除空 / N/A / 内部路径）。"""
    p = p or {}
    out: dict = {
        "name":   p.get("name"),
        "trophy": p.get("trophy_content"),
    }

    # rating: str → int
    try:
        r = p.get("rating")
        if r not in (None, "", "ERROR", "N/A"):
            out["rating"] = int(r)
    except (ValueError, TypeError):
        pass

    # 选择性带 URL（用户外部渲染时有用）；顺手把官方拼写错误 cource→course 修掉
    url_map = {
        "nameplate_url":   "nameplate_url",
        "icon_url":        "icon_url",
        "class_rank_url":  "class_rank_url",
        "cource_rank_url": "course_rank_url",
    }
    for src, dst in url_map.items():
        v = p.get(src)
        if v and v != "N/A":
            out[dst] = v

    nickname = get_user_field(user_id, "nickname")
    if nickname:
        out["line_nickname"] = nickname
    last_update = get_user_field(user_id, "last_update")
    if last_update:
        out["last_update"] = last_update

    return {k: v for k, v in out.items() if v is not None}


def build_payload(user_id: str) -> dict:
    """读 DB → 加工 → 拼出待序列化的纯 dict 结构。"""
    ver = get_user_field(user_id, "version", "jp")
    best   = [_transform_record(r) for r in (read_record(user_id, recent=False) or [])]
    recent = [_transform_record(r) for r in (read_record(user_id, recent=True, recent_type=True) or [])]
    profile = _transform_profile(get_user_field(user_id, "personal_info", {}), user_id)
    return {
        "format":         "JiETNGExport",
        "schema_version": 2,
        "generated_at":   datetime.now().isoformat(timespec="seconds"),
        "user_id":        user_id,
        "maimai_version": ver,
        "profile":        profile,
        "records": {
            "best":   best,
            "recent": recent,
        },
    }


# ----------------------------------------------------------------------------
# 序列化 / Serializers
# ----------------------------------------------------------------------------

def to_json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _xml_text(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v) if v is not None else ""


def _dict_to_xml(parent: ET.Element, data: dict):
    for k, v in data.items():
        tag = "".join(ch if (ch.isalnum() or ch in "_-.") else "_" for ch in str(k)) or "field"
        if not (tag[0].isalpha() or tag[0] == "_"):
            tag = f"_{tag}"
        if isinstance(v, dict):
            _dict_to_xml(ET.SubElement(parent, tag), v)
        elif isinstance(v, list):
            wrap = ET.SubElement(parent, tag)
            for item in v:
                rec_el = ET.SubElement(wrap, "record")
                if isinstance(item, dict):
                    _dict_to_xml(rec_el, item)
                else:
                    rec_el.text = _xml_text(item)
        else:
            ET.SubElement(parent, tag).text = _xml_text(v)


def to_xml_bytes(payload: dict) -> bytes:
    attribs = {
        "schema_version": str(payload.get("schema_version", 1)),
        "generated_at":   str(payload.get("generated_at", "")),
        "user_id":        str(payload.get("user_id", "")),
        "maimai_version": str(payload.get("maimai_version", "")),
    }
    root = ET.Element(payload.get("format", "Export"), attrib=attribs)
    body = {k: v for k, v in payload.items()
            if k not in ("format", "schema_version", "generated_at", "user_id", "maimai_version")}
    _dict_to_xml(root, body)
    ET.indent(root, space="  ")
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")


# ----------------------------------------------------------------------------
# 文件生命周期 / File lifecycle
# ----------------------------------------------------------------------------

def cleanup_expired_exports(ttl_seconds: int = _EXPORT_TTL_SECONDS):
    """扫描 EXPORT_DIR，删除 mtime 超过 ttl 的 .json/.xml。"""
    if not os.path.exists(EXPORT_DIR):
        return
    now = time.time()
    deleted = 0
    try:
        for filename in os.listdir(EXPORT_DIR):
            if not (filename.endswith(".json") or filename.endswith(".xml")):
                continue
            path = os.path.join(EXPORT_DIR, filename)
            try:
                age = now - os.path.getmtime(path)
                if age > ttl_seconds:
                    os.remove(path)
                    deleted += 1
                    logger.info(f"[Export] ✓ Deleted expired: file={filename}, age={int(age)}s")
            except Exception as e:
                logger.error(f"[Export] ✗ Cleanup file failed: file={filename}, error={e}")
        if deleted:
            logger.info(f"[Export] ✓ Periodic cleanup done: deleted={deleted}")
    except Exception as e:
        logger.error(f"[Export] ✗ Periodic cleanup failed: error={e}")


def start_periodic_cleanup(interval_seconds: int = 300):
    """启动周期性清理线程（默认每 5 分钟扫一次）；重复调用幂等。"""
    global _periodic_cleanup_thread
    with _periodic_cleanup_lock:
        if _periodic_cleanup_thread is not None and _periodic_cleanup_thread.is_alive():
            return

        def _loop():
            while True:
                try:
                    time.sleep(interval_seconds)
                    cleanup_expired_exports()
                except Exception as e:
                    logger.error(f"[Export] ✗ Periodic loop error: error={e}", exc_info=True)

        _periodic_cleanup_thread = threading.Thread(
            target=_loop, daemon=True, name="PeriodicExportCleanup"
        )
        _periodic_cleanup_thread.start()
        logger.info("[Export] ✓ Periodic cleanup thread started")


def _save_export(content: bytes, ext: str, friendly_name: str) -> Optional[str]:
    """落盘并返回外部访问 URL；失败返回 None。

    磁盘文件名仍为 `{token}.{ext}`（安全/唯一），URL 第二段携带
    `friendly_name`（CJK 自动百分号编码），便于用户辨识。
    文件清理由 start_periodic_cleanup 启动的全局线程按 mtime 统一处理。
    """
    if not content or len(content) > _MAX_PAYLOAD_BYTES:
        logger.error(f"[Export] ✗ Payload size out of range: bytes={len(content) if content else 0}")
        return None
    try:
        _ensure_dir()
        file_id = secrets.token_urlsafe(16)
        path = os.path.join(EXPORT_DIR, f"{file_id}.{ext}")
        with open(path, "wb") as f:
            f.write(content)
        url = f"https://{DOMAIN}/linebot/export/{file_id}/{quote(friendly_name, safe='')}"
        logger.info(f"[Export] ✓ Saved: id={file_id}.{ext} bytes={len(content)} name={friendly_name}")
        return url
    except Exception as e:
        logger.error(f"[Export] ✗ Save failed: error={e}")
        return None


# ----------------------------------------------------------------------------
# Public entry / 对外入口
# ----------------------------------------------------------------------------

def export_records(user_id: str, fmt: str) -> dict:
    """读取用户成绩 → 序列化 → 落盘 → 返回元数据。

    Returns:
        {"status": "ok",    "url": str, "size": int, "fmt": str,
         "best_count": int, "recent_count": int, "ttl_minutes": int}
        {"status": "empty"}                         # 没有任何成绩
        {"status": "error", "message": str}         # 失败
    """
    fmt = (fmt or "").lower()
    if fmt not in ("json", "xml"):
        return {"status": "error", "message": f"unsupported format: {fmt}"}

    try:
        payload = build_payload(user_id)
    except Exception as e:
        logger.error(f"[Export] ✗ Build payload failed: user_id={user_id}, error={e}", exc_info=True)
        return {"status": "error", "message": str(e)}

    recs = payload.get("records", {})
    best_count = len(recs.get("best") or [])
    recent_count = len(recs.get("recent") or [])
    if not best_count and not recent_count:
        return {"status": "empty"}

    content = to_json_bytes(payload) if fmt == "json" else to_xml_bytes(payload)
    friendly_name = _build_friendly_name(payload.get("profile"), fmt)
    url = _save_export(content, fmt, friendly_name)
    if not url:
        return {"status": "error", "message": "save failed"}

    return {
        "status":        "ok",
        "url":           url,
        "friendly_name": friendly_name,
        "size":          len(content),
        "fmt":           fmt,
        "best_count":    best_count,
        "recent_count":  recent_count,
        "ttl_minutes":   _EXPORT_TTL_SECONDS // 60,
    }
