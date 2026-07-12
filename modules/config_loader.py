"""
配置加载模块

负责加载和管理配置文件、歌曲数据、用户数据等全局配置
"""

import copy
import json
import os
import secrets
import csv
import threading

from cryptography.fernet import Fernet

CONFIG_PATH = "./config.json"

# 默认配置
default_config = {
    "admin_password": "",
    "maimai_version": {
        "jp": [],
        "intl": []
    },
    "temp_version": {
        "abbr": "",
        "title": ""
    },
    "domain": "",
    "host": "0.0.0.0",
    "port": 5000,
    "record_database": {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "maimai_records"
    },
    "urls": {
        "line_adding": "",
        "support_page": "https://github.com/Matsuk1/JiETNG/blob/main/COMMANDS.md",
        "dxdata": [
            "https://dp4p6x0xfi5o9.cloudfront.net/maimai/data.json",
            "https://raw.githubusercontent.com/gekichumai/dxrating/refs/heads/main/packages/dxdata/dxdata.json"
        ]
    },
    "line_channel": {
        "account_id": "",
        "access_token": "",
        "secret": ""
    },
    "rich_menu": {
        "enabled": False,
        "unbound_id": "",
        "bound_id": "",
        "support_url": "",
        "default_language": "zh",
        "menus": {},
        "aliases": {}
    },
    "keys": {
        "user_data": "",
        "bind_token": ""
    },
    "cloudflare_r2": {
        "enabled": False,
        "account_id": "",
        "access_key_id": "",
        "secret_access_key": "",
        "bucket_name": "",
        "public_url": ""
    },
    "web_push": {
        "vapid_private_key": "",
        "vapid_public_key": "",
        "contact": "mailto:admin@example.com"
    }
}

config_dir = os.path.dirname(CONFIG_PATH)
if config_dir:
    os.makedirs(config_dir, exist_ok=True)

def _generate_vapid_keys():
    """生成 VAPID 密钥对（EC P-256），返回 (private_b64, public_b64)"""
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.backends import default_backend
    import base64
    key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    priv_bytes = key.private_numbers().private_value.to_bytes(32, 'big')
    pub = key.public_key().public_numbers()
    pub_bytes = b'\x04' + pub.x.to_bytes(32, 'big') + pub.y.to_bytes(32, 'big')
    return (
        base64.urlsafe_b64encode(priv_bytes).rstrip(b'=').decode(),
        base64.urlsafe_b64encode(pub_bytes).rstrip(b'=').decode()
    )

def _ensure_fernet_key(value: str) -> str:

    if not isinstance(value, str):
        value = ""

    try:
        Fernet(value.encode())
    except (ValueError, TypeError):
        value = Fernet.generate_key().decode()

    return value

def _ensure_bind_token(value: str) -> str:
    if not isinstance(value, str) or not value:
        value = secrets.token_urlsafe(16)

    return value

# 加载配置，若不存在则创建；若缺字段则补全
if not os.path.exists(CONFIG_PATH):
    _config = copy.deepcopy(default_config)
else:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
        _config = json.load(file)

    # 递归补字段
    def deep_update(default, current):
        for key, value in default.items():
            if key not in current:
                current[key] = value
            elif isinstance(value, dict):
                deep_update(value, current[key])

    deep_update(default_config, _config)

_config["keys"]["user_data"] = _ensure_fernet_key(_config["keys"].get("user_data", ""))
_config["keys"]["bind_token"] = _ensure_bind_token(_config["keys"].get("bind_token", ""))

# 自动生成 VAPID 密钥
if not _config["web_push"].get("vapid_private_key") or not _config["web_push"].get("vapid_public_key"):
    _config["web_push"]["vapid_private_key"], _config["web_push"]["vapid_public_key"] = _generate_vapid_keys()

# 写回更新后的配置
with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
    json.dump(_config, f, indent=4, ensure_ascii=False)

# 顶层字段
ADMIN_PASSWORD = _config["admin_password"]
MAIMAI_VERSION = _config["maimai_version"]
TEMP_VERSION = _config["temp_version"]

# 域名字段
DOMAIN = _config["domain"]

# 服务地址端口
HOST = _config["host"]
PORT = _config["port"]

# 数据文件路径（./data/）
LOG_FILE = "./jietng.log"
DXDATA_FILE = "./data/dxdata/dxdata.json"
DXDATA_VERSION_FILE = "./data/dxdata/dxdata_version.json"
OVERRIDE_FILE = "./data/dxdata/override.csv"
INTL_OVERRIDE_FILE = "./data/dxdata/intl_override.csv"
NOTICE_FILE = "./data/notice.json"
TIP_AD_FILE = "./data/tip_ad.json"
DEV_TOKENS_FILE = "./data/dev_tokens.json"

# 数据目录路径（./data/）
BACKUP_DIR = "./data/backup"
IMG_DIR = "./data/images"
EXPORT_DIR = "./data/exports"

# 资源文件路径（./assets/）
FONT_FILE = "./assets/fonts/line_seed_jietng.ttf"
LOGO_FILE = "./assets/pics/logo.png"
QR_CODE_FILE = "./assets/pics/qrcode.png"

# 资源目录路径（./assets/）
VERSIONS_DIR = "./assets/versions"
COVERS_DIR = "./assets/covers"
PLATES_DIR = "./assets/plates"
ICON_TYPE_DIR = "./assets/icon/type"
ICON_SCORE_DIR = "./assets/icon/score"
ICON_DX_STAR_DIR = "./assets/icon/dx_star"
ICON_COMBO_DIR = "./assets/icon/combo"
ICON_SYNC_DIR = "./assets/icon/sync"
ICON_COMBO_RCD_DIR = "./assets/icon/combo_rcd"
ICON_SYNC_RCD_DIR = "./assets/icon/sync_rcd"
ICON_BASE_DIR = "./assets/icon"
BG_DIR = "./assets/pics/bg"
RATING_DIR = "./assets/pics/rating"

# 数据库配置字段
RECORD_DATABASE = _config["record_database"]
DB_HOST = RECORD_DATABASE["host"]
DB_USER = RECORD_DATABASE["user"]
DB_PASSWORD = RECORD_DATABASE["password"]
DB_NAME = RECORD_DATABASE["database"]

# URL 配置字段
URLS = _config["urls"]
LINE_ADDING_URL = URLS["line_adding"]
SUPPORT_PAGE = URLS["support_page"]
DXDATA_URL = URLS["dxdata"]

# LINE 配置字段
LINE_CHANNEL = _config["line_channel"]
LINE_ACCOUNT_ID = LINE_CHANNEL["account_id"]
LINE_CHANNEL_ACCESS_TOKEN = LINE_CHANNEL["access_token"]
LINE_CHANNEL_SECRET = LINE_CHANNEL["secret"]

# Rich menu 配置字段
RICH_MENU = _config.get("rich_menu", {})
RICH_MENU_ENABLED = bool(RICH_MENU.get("enabled", False))
RICH_MENU_UNBOUND_ID = RICH_MENU.get("unbound_id", "")
RICH_MENU_BOUND_ID = RICH_MENU.get("bound_id", "")
RICH_MENU_DEFAULT_LANGUAGE = RICH_MENU.get("default_language", "zh")
RICH_MENU_MENUS = RICH_MENU.get("menus", {})

# key 配置字段
KEYS = _config["keys"]
BIND_TOKEN_KEY = KEYS["bind_token"].encode()

# Cloudflare R2 配置字段
R2_CONFIG = _config.get("cloudflare_r2", {})
R2_ENABLED = R2_CONFIG.get("enabled", False)
R2_ACCOUNT_ID = R2_CONFIG.get("account_id", "")
R2_ACCESS_KEY_ID = R2_CONFIG.get("access_key_id", "")
R2_SECRET_ACCESS_KEY = R2_CONFIG.get("secret_access_key", "")
R2_BUCKET_NAME = R2_CONFIG.get("bucket_name", "")
R2_PUBLIC_URL = R2_CONFIG.get("public_url", "")

# Web Push 配置字段
WEB_PUSH_CONFIG = _config.get("web_push", {})
VAPID_PRIVATE_KEY = WEB_PUSH_CONFIG.get("vapid_private_key", "")
VAPID_PUBLIC_KEY = WEB_PUSH_CONFIG.get("vapid_public_key", "")
VAPID_CONTACT = WEB_PUSH_CONFIG.get("contact", "mailto:admin@example.com")


def apply_override(songs, override_file):
    """应用 CSV override 文件到歌曲数据"""
    if not os.path.exists(override_file):
        return
    csv_map = {}
    with open(override_file, 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if row:
                csv_map[row[0]] = row[1:]

    for song in songs:
        if song['title'] not in csv_map:
            continue
        if song['type'] != csv_map[song['title']][0]:
            continue
        row = csv_map[song['title']][1:]
        *keys, value = row
        # 自动转换数字类型
        try:
            value = int(value) if value.isdigit() else float(value)
        except (ValueError, AttributeError):
            pass
        cur = song
        for k in keys[:-1]:
            if k.isdigit():
                k = int(k)
                while len(cur) <= k:
                    cur.append({})
                cur = cur[k]
            else:
                cur = cur.setdefault(k, {})
        last = keys[-1]
        if last.isdigit():
            last = int(last)
            while len(cur) <= last:
                cur.append(None)
            cur[last] = value
        else:
            cur[last] = value

        for sheet in song.get("sheets", []):
            sheet["internalLevelValue"] = float(sheet["internalLevelValue"])


# dxdata 内存缓存：按 ver 缓存 (mtimes, songs, versions)
# mtimes 任一变化（dxdata.json / override.csv / intl_override.csv）即失效重建
# 注意：返回的 songs/versions 是共享引用，调用方禁止原地修改
_dxdata_cache: dict = {}
_dxdata_cache_lock = threading.Lock()


def _file_mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def read_dxdata(ver="jp"):
    """
    读取歌曲数据（带 mtime 失效缓存）

    Args:
        ver: 版本 "jp" 或 "intl"

    Returns:
        tuple: (songs, versions) — 共享引用，请勿原地修改
    """
    files = [DXDATA_FILE, OVERRIDE_FILE]
    if ver == "intl":
        files.append(INTL_OVERRIDE_FILE)
    mtimes = tuple(_file_mtime(f) for f in files)

    with _dxdata_cache_lock:
        cached = _dxdata_cache.get(ver)
        if cached and cached[0] == mtimes:
            return cached[1], cached[2]

    # 缓存未命中或失效；不持锁重建，避免长时间阻塞并发读
    with open(DXDATA_FILE, 'r', encoding='utf-8') as f:
        dxdata_file = json.load(f)
    songs = list(dxdata_file['songs'])

    # 通用 override（所有版本生效）
    apply_override(songs, OVERRIDE_FILE)

    # intl 专用 override
    if ver == "intl":
        apply_override(songs, INTL_OVERRIDE_FILE)

    versions = list(dxdata_file['versions'])

    with _dxdata_cache_lock:
        _dxdata_cache[ver] = (mtimes, songs, versions)
    return songs, versions

def load_user():
    """初始化用户表"""
    from modules.user_db import init_users_table
    init_users_table()
