import json
import os
from json_encrypt import *

CONFIG_PATH = "./config/bot_config.json"

# 默认配置
default_config = {
    "admin_id": [],
    "notice": {
        "lines": [],
        "timestamp": 0
    },
    "maimai_version": "PRiSM PLUS",
    "file_path": {
        "arcade_list": "./data/arcade_list.json",
        "dxdata_list": "./data/dxdata_list.json",
        "user_list": "./data/user_list.json",
        "fonts_folder": "./assets/fonts",
        "notice_back": "./assets/bg/notice.png",
        "logo": "./assets/logo.png"
    },
    "record_database": {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "records"
    },
    "urls": {
        "dxdata": "",
        "ai_respond": ""
    },
    "line_channel": {
        "access_token": "",
        "secret": ""
    },
    "keys": {
        "user_data": "",
        "ai_respond": "",
        "bind_token": ""
    }
}

# 自动创建 config 目录
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

# 加载配置，若不存在则创建；若缺字段则补全
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)
    _config = default_config
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

    # 写回更新后的配置
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(_config, f, indent=4, ensure_ascii=False)

# 顶层字段
admin_id = _config["admin_id"]
NOTICE = _config["notice"]
MAIMAI_VERSION = _config["maimai_version"]

# 文件路径字段
file_path = _config["file_path"]
arcade_list = file_path["arcade_list"]
dxdata_list = file_path["dxdata_list"]
user_list = file_path["user_list"]
fonts_folder = file_path["fonts_folder"]
background_path = file_path["notice_back"]
LOGO_PATH = file_path["logo"]

# 数据库配置字段
record_database = _config["record_database"]
HOST = record_database["host"]
USER = record_database["user"]
PASSWORD = record_database["password"]
DATABASE = record_database["database"]

# URL 配置字段
urls = _config["urls"]
DXDATA_URL = urls["dxdata"]
AI_RESPOND_URL = urls["ai_respond"]

# LINE 配置字段
line_channel = _config["line_channel"]
LINE_CHANNEL_ACCESS_TOKEN = line_channel["access_token"]
LINE_CHANNEL_SECRET = line_channel["secret"]

# key 配置字段
keys = _config["keys"]
USER_DATA_KEY = keys["user_data"].encode()
AI_KEY = keys["ai_respond"]
BIND_TOKEN_KEY = keys["bind_token"].encode()

# 全局缓存数据
arcade = {}
songs = []
versions = {}
users = {}

def read_arcade():
    global arcade
    arcade.clear()
    arcade.update(json.load(open(arcade_list, 'r', encoding='utf-8')))

def write_arcade():
    with open(arcade_list, 'w', encoding='utf-8') as file:
        json.dump(arcade, file, ensure_ascii=False, indent=4)

def read_dxdata():
    global songs, versions
    dxdata_file = json.load(open(dxdata_list, 'r', encoding='utf-8'))
    songs.clear()
    songs.extend(dxdata_file['songs'])
    versions.clear()
    versions.update(dxdata_file['versions'])

def read_user():
    global users
    users.clear()
    users.update(read_encrypted_json(user_list, USER_DATA_KEY))

def write_user():
    write_encrypted_json(users, user_list, USER_DATA_KEY)
