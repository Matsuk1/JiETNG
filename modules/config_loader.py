"""
配置加载模块

负责加载和管理配置文件、歌曲数据、用户数据等全局配置
"""

import copy
import json
import os
import secrets
import csv

from cryptography.fernet import Fernet
from modules.json_encrypt import *

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

# 文件路径
DXDATA_LIST = "./data/dxdata/dxdata.json"
DXDATA_VERSION_FILE = "./data/dxdata/dxdata_version.json"
OVERRIDE_LIST = "./data/dxdata/intl_override.json"
USER_LIST = "./data/user.json.enc"
NOTICE_FILE = "./data/notice.json"
TIP_AD_FILE = "./data/tip_ad.json"
BACKUP_DIR = "./data/backup"
DEV_TOKENS_FILE = "./data/dev_tokens.json"
IMG_DIR = "./data/images"
FONT_PATH = "./assets/fonts/line_seed_jietng.ttf"
LOGO_PATH = "./assets/pics/logo.png"
QR_CODE = "./assets/pics/qrcode.png"
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

# key 配置字段
KEYS = _config["keys"]
USER_DATA_KEY = KEYS["user_data"].encode()
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

# 全局缓存数据
USERS = {}

# 用户数据脏标记（用于延迟写入）
_user_data_dirty = False

def read_dxdata(ver="jp"):
    """
    读取歌曲数据

    Args:
        ver: 版本 "jp" 或 "intl"

    Returns:
        tuple: (songs, versions)
    """
    dxdata_file = json.load(open(DXDATA_LIST, 'r', encoding='utf-8'))
    songs = list(dxdata_file['songs'])

    def is_int(s):
        return s.isdigit()

    if ver == "intl":
        csv_map = {}
        with open(OVERRIDE_LIST, 'r', encoding='utf-8') as f:
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
            cur = song
            for k in keys[:-1]:
                if is_int(k):
                    k = int(k)
                    while len(cur) <= k:
                        cur.append({})
                    cur = cur[k]
                else:
                    cur = cur.setdefault(k, {})
            last = keys[-1]
            if is_int(last):
                last = int(last)
                while len(cur) <= last:
                    cur.append(None)
                cur[last] = value
            else:
                cur[last] = value

    versions = list(dxdata_file['versions'])
    return songs, versions

def load_user():
    global USERS, _user_data_dirty
    if not USERS:  # 只在未加载时读取
        USERS.update(read_encrypted_json(USER_LIST, USER_DATA_KEY))
    _user_data_dirty = False

def write_user(force=False):
    """
    写入用户数据

    Args:
        force: 强制写入，忽略脏标记
    """
    global _user_data_dirty
    if force or _user_data_dirty:
        write_encrypted_json(USERS, USER_LIST, USER_DATA_KEY)
        _user_data_dirty = False

def mark_user_dirty():
    """标记用户数据已修改"""
    global _user_data_dirty
    _user_data_dirty = True
