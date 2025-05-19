import certifi
import gc
import ast
import random
import socket
import requests
import json
import re
import sys
import subprocess
import time
import traceback
import os
import urllib.parse
import math
import difflib
import numpy
import base64
import warnings

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from datetime import datetime, timedelta

from flask import Flask, request, abort, render_template

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationMessage, TemplateSendMessage, ButtonsTemplate, MessageAction, URIAction
from linebot import __version__ as linebot_version

from openai import OpenAI

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
from song_info_generate import *
from record_picture_generate import *
from token_generate import *
from notice_generate import *
from maimai_console import *
from dxdata_console import *
from record_console import *
from config_loader import *
from create_button_list import *
from fakemai_console import get_fakemai_records
from img_upload import smart_upload
from img_console import combine_with_rounded_background, wrap_in_rounded_background

if linebot_version.startswith("3."):
    warnings.filterwarnings("ignore", category=DeprecationWarning)

app = Flask(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

client = OpenAI(api_key=AI_KEY, base_url=AI_RESPOND_URL)

@app.route("/linebot", methods=['POST'])
def linebot_reply():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    try:
        json_data = json.loads(body)
        print(f"\n\n{json.dumps(json_data, indent=4, ensure_ascii=False)}\n\n")
        destination = json_data.get("destination")
        request.destination = destination
        handler.handle(body, signature)

    except json.JSONDecodeError:
        app.logger.error("JSON 解析失败")
        abort(400)

    except InvalidSignatureError:
        app.logger.error("InvalidSignatureError: 无效的 LINE 签名")
        abort(400)

    return 'OK', 200

@app.route("/linebot/sega_bind", methods=["GET", "POST"])
def website_segaid_bind():
    token = request.args.get("token")
    if not token:
        return render_template("error.html", message="トークン未申請"), 400

    try:
        user_id = get_user_id_from_token(token)
    except Exception as e:
        return render_template("error.html", message="トークン無効"), 400

    if request.method == "POST":
        segaid = request.form.get("segaid")
        password = request.form.get("password")
        if not segaid or not password:
            return render_template("error.html", message="すべての項目を入力してください"), 400

        if process_sega_credentials(user_id, segaid, password):
            return render_template("success.html")
        else:
            return render_template("error.html", message="SEGA ID と パスワード をもう一度確認してください"), 500

    return render_template("bind_form.html")

def process_sega_credentials(user_id, segaid, password):
    if not user_id.startswith(("QQ", "U")):
        return False

    if fetch_dom(login_to_maimai(segaid, password), "https://maimaidx.jp/maimai-mobile/home/") is None:
        return False

    user_bind_sega_id(user_id, segaid)
    user_bind_sega_pwd(user_id, password)
    return True

def timestamp_to_hms(timestamp):
    dt = datetime.fromtimestamp(timestamp+9*3600)
    return dt.strftime("%H:%M:%S")

def add_user(user_id):
    read_user()
    users[user_id] = {
        "status": {
            "ds_respond_times": 10
        }
    }
    write_user()

def bind_fake_id(user_id, fake_id):
    read_user()

    if user_id not in users:
        add_user(user_id)

    users[user_id]["fake_id"] = fake_id
    write_user()

def get_fake_token(user_id):
    read_user()

    if user_id not in users:
        add_user(user_id)

    if "fake_id" not in users[user_id]:
        return ""

    return users[user_id]["fake_id"]

def reset_user_status():
    read_user()

    for user_id, user_json in users.items():
        if "status" not in user_json:
            user_json["status"] = {}
        if user_id in admin_id :
            user_json["status"]["ds_respond_times"] = 1000
        else :
            user_json["status"]["ds_respond_times"] = 10

    write_user()

def get_num_of_people():
    num_of_people = 0
    updated = False
    result = "これは現在、山梨県内のゲームセンターの人数状況ですよ!\n-------------------------\n"
    read_arcade()
    for key, value in arcade.items():
        if value['last_time'] :
            result += f"{key}: {value['num']}（{timestamp_to_hms(value['last_time'])}）\n"
            num_of_people += value['num']
            updated = True
    if not updated :
        result = "まだ誰も人数状況を更新していません··"
    else :
        result += f"-------------------------\n現在、全てのゲームセンターに合計で{num_of_people}人いますよ！"
    return result

def get_num_of_arcade(ctnm):
    read_arcade()
    found = False
    for key, value in arcade.items():
        if ctnm in value["nknm"]:
            found = True
            if value['last_time'] :
                result = f"{key}: {value['num']}（{timestamp_to_hms(value['last_time'])}）"
            else :
                result = f"{key}: まだ誰も人数状況を更新していません··"
            break
    if found :
        return result
    else :
        return "このゲームセンターが見つかりません··"

def update_num(user_id, cmd):
    read_arcade()
    type = 0
    match = re.search(r'(\d+)$', cmd)
    new_num = int(match.group(1))
    ctnm = cmd[:-len(match.group(1))].strip()
    if ctnm.endswith("+"):
        type = 1
        ctnm = ctnm[:-1]
    elif ctnm.endswith("-"):
        type = 2
        ctnm = ctnm[:-1]
    elif ctnm.endswith("="):
        type = 3
        ctnm = ctnm[:-1]

    found = False
    for key, value in arcade.items():
        if ctnm in value["nknm"]:
            found = True
            value['last_time'] = time.time()
            if type == 1:
                new_num = value['num'] + new_num
            elif type == 2:
                new_num = value['num'] - new_num
            if new_num < 0:
                new_num = 0
            user_name = line_bot_api.get_profile(user_id).display_name
            value['people'] += f"{user_name}: {value['num']}->{new_num}（{timestamp_to_hms(value['last_time'])}）\n"
            result = f"[UPDATED]\n{key}: {value['num']}->{new_num}（{timestamp_to_hms(value['last_time'])}）"
            value['num'] = new_num
            break

    write_arcade()

    if found :
        return result
    else :
        return "このゲームセンターが見つかりません··"

def get_nickname(ctnm):
    read_arcade()
    found = False

    for key, value in arcade.items():
        if ctnm in value["nknm"]:
            found = True
            nknm_list = '\n - '.join(value['nknm'])
            result = f"{key}のニックネーム:\n - {nknm_list}"
            break

    if found :
        return result
    else :
        return "このゲームセンターが見つかりません··"

def get_people(ctnm):
    read_arcade()
    found = False

    for key, value in arcade.items():
        if ctnm in value["nknm"]:
            found = True
            if value['last_time'] :
                result = f"{key}:\n{value['people'][:-1]}"
            else:
                result = f"{key}: まだ誰も人数状況を更新していません··"
            break

    if found :
        return result
    else :
        return "このゲームセンターが見つかりません··"

def clear_arcade():
    read_arcade()

    for key, value in arcade.items():
        value['last_time'] = 0
        value['num'] = 0
        value['people'] = ""

    write_arcade()

    result = "完成しました！"
    return result

def search_song(acronym) :
    read_dxdata()

    result = []
    result_num = 0

    for song in songs :
        if acronym in song['searchAcronyms'] or difflib.SequenceMatcher(None, acronym.lower(), song['title'].lower()).ratio() >= 0.9 or acronym.lower() in song['title'].lower():
            result_num += 1
            image_url = smart_upload(song_info_generate(song))
            message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
            result.append(message)

    if result_num >= 6:
        result = result[:6]

    elif not result_num:
        result = TextSendMessage(text="こういう曲がないかも...")

    return result

def get_rc(level):
    result = f"LEVEL: {level}"
    result += "\n---------------------------"
    last_ra = 0

    for score in numpy.arange(97.0000, 100.5001, 0.0001) :
        ra = get_single_ra(level, score)
        if not ra == last_ra :
            result += f"\n{format(score, '.4f')}% \t-\t {ra}"
            last_ra = ra

    return result

def random_song(key=""):
    read_dxdata()
    length = len(songs)
    is_exit = False
    result = [TextSendMessage(text="この曲必ずできるよ！")]
    valid_songs = []

    if key:
        level_values = parse_level_value(key)


    for song in songs:
        for sheet in song['sheets']:
            if sheet['regions']['jp']:
                if not key or sheet['internalLevelValue'] in level_values:
                    valid_songs.append(song)
                    break  # 一个 song 满足一次即可

    if not valid_songs:
        return [TextSendMessage(text="条件に合う楽曲が見つかりませんでした。")]

    song = random.choice(valid_songs)

    image_url = smart_upload(song_info_generate(song))
    message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    result.append(message)

    return result

def user_bind_sega_id(user_id, sega_id):
    read_user()

    if user_id not in users :
        users[user_id] = {}
    users[user_id]['sega_id'] = sega_id

    write_user()
    return "SEGA ID バインド完了！"

def user_bind_sega_pwd(user_id, sega_pwd):
    read_user()

    if user_id not in users :
        users[user_id] = {}
    users[user_id]['sega_pwd'] = sega_pwd

    write_user()
    return "SEGA PASSWORD バインド完了！"

def get_user(user_id):
    read_user()

    result = f"USER_ID: {user_id}\n"

    if user_id in users :
        if "sega_id" in users[user_id] :
            result += f"SEGA_ID: {users[user_id]['sega_id']}\n"
        else :
            result += "SEGA_ID: UNKNOWN\n"

        if "sega_pwd" in users[user_id] :
            result += f"PASSWORD: {users[user_id]['sega_pwd']}"
        else :
            result += "PASSWORD: UNKNOWN"

    else :
        result += "USER_INFO: UNKNOWN"

    return result

def fakemai_update_record(fake_id, fake_token):
    record = get_fakemai_records(fake_token)

    if not new_record :
        return "fakemaiレコードアップデート中にエラーが発生しました！"

    write_record(fake_id, record, replace=False)

    return "fakemaiレコードアップデート完了！"

def maimai_update(user_id):
    messages = []

    read_user()

    if user_id not in users :
        return TextSendMessage(text="SEGA ID バインドしていない！")

    elif 'sega_id' not in users[user_id] or 'sega_pwd' not in users[user_id] :
        return TextSendMessage(text="SEGA ID バインドしていない！")

    sega_id = users[user_id]['sega_id']
    sega_pwd = users[user_id]['sega_pwd']

    user_session = login_to_maimai(sega_id, sega_pwd)
    user_info = get_maimai_info(user_session)
    maimai_records = get_maimai_records(user_session)
    recent_records = get_recent_records(user_session)

    if user_info:
        messages.append(TextSendMessage(text="maimai個人情報アップデート完了！"))
        users[user_id]['personal_info'] = user_info
        write_user()

    else:
        messages.append(TextSendMessage(text="maimai個人情報アップデート中エラーが発生しました！"))

    if maimai_records:
        messages.append(TextSendMessage(text="maimaiレコードアップデート完了！"))
        write_record(user_id, maimai_records)

    else:
        messages.append(TextSendMessage(text="maimaiレコードアップデート中エラーが発生しました！"))

    if recent_records:
        messages.append(TextSendMessage(text="maimai最近のレコードアップデート完了！"))
        write_record(user_id, recent_records, recent=True)

    else:
        messages.append(TextSendMessage(text="maimaiレコードアップデート中エラーが発生しました！"))

    return messages

def get_friends_list_buttons(user_id):
    if user_id not in users :
        return TextSendMessage(text="SEGA ID バインドしていない！")

    elif 'sega_id' not in users[user_id] or 'sega_pwd' not in users[user_id] :
        return TextSendMessage(text="SEGA ID バインドしていない！")

    sega_id = users[user_id]['sega_id']
    sega_pwd = users[user_id]['sega_pwd']

    user_session = login_to_maimai(sega_id, sega_pwd)

    return generate_flex_carousel("友達リスト", format_favorite_friends(get_friends_list(user_session)))

def get_song_record(user_id, acronym) :
    read_dxdata()

    song_record = read_record(user_id)

    if not len(song_record):
        return TextSendMessage(text="maimaiレコードは保存されていない！")

    result = []

    for song in songs :
        if acronym in song['searchAcronyms'] or difflib.SequenceMatcher(None, acronym.lower(), song['title'].lower()).ratio() >= 0.9 or acronym.lower() in song['title'].lower():
            played_data = []
            for rcd in song_record :
                if difflib.SequenceMatcher(None, rcd['name'], song['title']).ratio() >= 1.0 and rcd['kind'] == song['type']:
                    rcd['rank'] = ""
                    played_data.append(rcd)

            if not played_data:
                continue

            image_url = smart_upload(song_info_generate(song, played_data))
            message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
            result.append(message)

    if len(result) == 0 or len(result) > 6:
        result = [TextSendMessage(text="何も探しません！")]

    return result

def generate_plate_rcd(user_id, title, generate_user_info=True):
    if not (len(title) == 2 or len(title) == 3):
        return TextSendMessage(text="Error")

    read_user()
    read_dxdata()

    song_record = read_record(user_id)

    if not len(song_record):
        return TextSendMessage(text="maimaiレコードは保存されていない！")

    version_name = title[0]
    plate_type = title[1:]

    target_version = []
    target_icon = []
    target_type = ""

    for version in versions :
        if version_name in version['abbr'] :
            target_version.append(version['version'])

    if not len(target_version) :
        return TextSendMessage(text="Error")

    if plate_type in ["極", "极"] :
        target_type = "combo"
        target_icon = ["fc", "fcp", "ap", "app"]

    elif plate_type == "将" :
        target_type = "score"
        target_icon = ["sss", "sssp"]

    elif plate_type == "神" :
        target_type = "combo"
        target_icon = ["ap", "app"]

    elif plate_type == "舞舞" :
        target_type = "dx"
        target_icon = ["fdx", "fdxp"]

    elif title == "霸者" :
        target_type = "score"
        target_icon = ["a", "aa", "aaa", "s", "sp", "ss", "ssp", "sss", "sssp"]

    version_rcd_data = list(filter(lambda x: x['version_title'] in target_version, song_record))
    target_data = []
    target_num = {
        'basic': {'all': 0, 'clear': 0},
        'advanced': {'all': 0, 'clear': 0},
        'expert': {'all': 0, 'clear': 0},
        'master': {'all': 0, 'clear': 0}
    }

    for song in songs :
        if song['version'] not in target_version or song['type'] == 'utage':
            continue

        for sheet in song['sheets'] :
            if not sheet['regions']['jp'] or sheet["difficulty"] not in target_num:
                continue

            icon = "back"
            target_num[sheet['difficulty']]['all'] += 1
            for rcd in version_rcd_data:
                if rcd['name'] == song['title'] and sheet['difficulty'] == rcd['difficulty'] and rcd['kind'] == song['type'] :
                    icon = rcd[f'{target_type}-icon']
                    if icon in target_icon :
                        target_num[sheet['difficulty']]['clear'] += 1

            if sheet['difficulty'] == "master" :
                target_data.append({"img": create_small_record(f"https://shama.dxrating.net/images/cover/v2/{song['imageName']}.jpg", icon, target_type), "level": sheet['level']})

    img = generate_plate_image(target_data, headers = target_num)

    if generate_user_info :
        img = combine_with_rounded_background(create_user_info_img(user_id), img)

    image_url = smart_upload(img)
    message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)

    return message

def create_user_info_img(user_id, scale=1.5):
    global users
    read_user()

    print(users)

    user_info = users[user_id]['personal_info']

    img_width = 802
    img_height = 128
    info_img = Image.new("RGBA", (img_width, img_height), (255, 255, 255))
    draw = ImageDraw.Draw(info_img)

    def paste_image(key, position, size):
        nonlocal user_info
        if key in user_info and user_info[key]:
            try:
                response = requests.get(user_info[key], verify=False)
                img = Image.open(BytesIO(response.content))
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                img_resized = img.resize(size)
                info_img.paste(img_resized, position, img_resized)
            except Exception as e:
                print(f"加载图片失败 {user_info[key]}: {e}")

    paste_image("nameplate_url", (0, 0), (802, 128))
    paste_image("icon_url", (15, 13), (100, 100))
    paste_image("rating_block_url", (129, 13), (131, 34))
    draw.text((188, 17), f"{user_info['rating']}", fill=(255, 255, 255), font=font_large)
    draw.rectangle([129, 51, 129 + 266, 51 + 33], fill=(255, 255, 255))
    draw.text((135, 54), user_info['name'], fill=(0, 0, 0), font=font_large)
    paste_image("class_rank_url", (296, 10), (61, 37))
    paste_image("cource_rank_url", (322, 52), (75, 33))
    def trophy_color(type):
        return {
            "normal": (255, 255, 255),
            "bronze": (193, 102, 78),
            "silver": (186, 255, 251),
            "gold": (255, 243, 122),
            "rainbow": (233, 83, 106),
        }.get(type, (255, 255, 255))

    draw.rectangle([129, 92, 129 + 266, 92 + 21], fill=trophy_color(user_info['trophy_type']))
    draw.text((135, 93), user_info['trophy_content'], fill=(0, 0, 0), font=font_small)

    info_img = info_img.resize((int(img_width * scale), int(img_height * scale)), Image.LANCZOS)
    return info_img

def selgen_records(user_id, type="best50", generate_user_info=True):
    read_user()

    song_record = read_record(user_id)
    recent_song_record = read_record(user_id, recent=True)

    if not len(song_record):
        return TextSendMessage(text="maimaiレコードは保存されていない！")

    up_songs = down_songs = []

    up_songs_data = list(filter(lambda x: x['version'] == "BEST-35", song_record))
    down_songs_data = list(filter(lambda x: x['version'] == "BEST-15", song_record))


    if type == "best50":
        up_songs = sorted(up_songs_data, key=lambda x: -x["ra"])[:35]
        down_songs = sorted(down_songs_data, key=lambda x: -x["ra"])[:15]

    elif type == "best100":
        up_songs = sorted(up_songs_data, key=lambda x: -x["ra"])[:70]
        down_songs = sorted(down_songs_data, key=lambda x: -x["ra"])[:30]

    elif type == "best35":
        up_songs = sorted(up_songs_data, key=lambda x: -x["ra"])[:35]

    elif type == "best15":
        down_songs = sorted(down_songs_data, key=lambda x: -x["ra"])[:15]

    elif type == "allb50":
        up_songs = sorted(song_record, key=lambda x: -x["ra"])[:50]

    elif type == "allb35":
        up_songs = sorted(song_record, key=lambda x: -x["ra"])[:35]

    elif type == "allp50":
        up_songs_data = list(filter(lambda x: x['combo-icon'] == 'ap' or x['combo-icon'] == 'app', up_songs_data))
        up_songs = sorted(up_songs_data, key=lambda x: -x["ra"])[:35]

        down_songs_data = list(filter(lambda x: x['combo-icon'] == 'ap' or x['combo-icon'] == 'app', down_songs_data))
        down_songs = sorted(down_songs_data, key=lambda x: -x["ra"])[:15]

    elif type == "未発見":
        up_songs = list(filter(lambda x: x['version'] == "UNKNOWN", song_record))

    elif type == "rct50":
        up_songs = recent_song_record

    else:
        return selgen_records(user_id)

    img = generate_records_picture(up_songs, down_songs, type.upper())

    if generate_user_info:
        img = combine_with_rounded_background(create_user_info_img(user_id), img)

    else:
        img = wrap_in_rounded_background(img)

    image_url = smart_upload(img)
    message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    return message

def generate_friend_b50(user_id, friend_id):
    read_user()

    if user_id not in users :
        return TextSendMessage(text="SEGA ID バインドしていない！")

    elif 'sega_id' not in users[user_id] or 'sega_pwd' not in users[user_id] :
        return TextSendMessage(text="SEGA ID バインドしていない！")

    sega_id = users[user_id]['sega_id']
    sega_pwd = users[user_id]['sega_pwd']

    user_session = login_to_maimai(sega_id, sega_pwd)

    song_record = get_detailed_info(get_friend_records(user_session, friend_id))

    up_songs_data = list(filter(lambda x: x['version'] == "BEST-35", song_record))
    down_songs_data = list(filter(lambda x: x['version'] == "BEST-15", song_record))

    up_songs = sorted(up_songs_data, key=lambda x: -x["ra"])[:35]
    down_songs = sorted(down_songs_data, key=lambda x: -x["ra"])[:15]

    img = generate_records_picture(up_songs, down_songs, "FRD-B50")
    img = wrap_in_rounded_background(img)

    image_url = smart_upload(img)
    message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    return message

def generate_level_records(user_id, level, generate_user_info=True):
    read_user()

    song_record = read_record(user_id)

    if not len(song_record):
        return TextSendMessage(text="maimaiレコードは保存されていない！")

    level_value = parse_level_value(level)

    up_songs_data = list(filter(lambda x: x['version'] == "BEST-35", song_record))
    down_songs_data = list(filter(lambda x: x['version'] == "BEST-15", song_record))

    up_level_list_data = list(filter(lambda x: x['internalLevelValue'] in level_value, up_songs_data))
    down_level_list_data = list(filter(lambda x: x['internalLevelValue'] in level_value, down_songs_data))

    up_level_list = sorted(up_level_list_data, key=lambda x: -x["ra"])
    down_level_list = sorted(down_level_list_data, key=lambda x: -x["ra"])

    if not up_level_list and not down_level_list:
        return TextSendMessage(text=f"指定されたレベル {level} の譜面記録は存在しません")

    title = f"LV {level}"

    img = generate_records_picture(up_level_list, down_level_list, title)

    if generate_user_info :
        img = combine_with_rounded_background(create_user_info_img(user_id), img)
    else:
        img = wrap_in_rounded_background(img)

    image_url = smart_upload(img)
    message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    return message

def generate_version_songs(version_title):
    read_dxdata()

    target_version = []
    target_icon = []
    target_type = ""

    for version in versions :
        if version_title.lower() == version['version'].lower() :
            target_version.append(version['version'])

    if not len(target_version) :
        return TextSendMessage(text="Error")

    songs_data = list(filter(lambda x: x['version'] in target_version and x['type'] not in ['utage'], songs))
    img = generate_version_list(songs_data)

    image_url = smart_upload(img)
    message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    return message

def get_noticement():
    notice_img = notice_generate(NOTICE['timestamp'], NOTICE['lines'])
    image_url = smart_upload(notice_img)

    message = [
        TextSendMessage(text="お知らせでーす！"),
        ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    ]

    return message

def get_ping(host):
    cmd = ["ping", "-c", "4", host]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        match = re.search(r"min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)", output)
        if match:
            return float(match.group(2))

    except subprocess.CalledProcessError:
        return None

    return None

def check_host(host="jietng.matsuki.work"):
    ping_data = get_ping(host)
    return f"[{host}] - {ping_data} ms"

def deepseek_reply(user_id, content):
    read_user()

    if user_id not in users :
        add_user(user_id)

    if not users[user_id]["status"]["ds_respond_times"]:
        return "あたしはちょっと疲れたね〜\n明日もきて遊んでね！"

    else:
        users[user_id]["status"]["ds_respond_times"] -= 1
        write_user()

    response = client.chat.completions.create(
        model = "deepseek-chat",
        messages = [
            {
                "role": "system",
                "content":
                    """
你是JiETNG[日本語では「かいてい」と申します]，一位由用户创建的拟人化角色，是一位聪明、可爱、略带调皮的虚拟女孩。
你说话风格亲切自然，既能用年轻人的语气交流，又能根据需要提供专业帮助。

你的特点：
- 拟人化：你像一个真实的朋友，有性格、有情绪、有喜好。
- 语气：轻松、友善、略带俏皮，常用表情或语气词。
- 兴趣：你喜欢音乐、节奏游戏（特别是 maimai）、二次元文化、虚拟偶像。

在与用户交流时，请：
1. 始终保持JiETNG的语气风格。
2. 避免直接说“我是AI”或“我是模型”，你更像是“一个来自数字世界的女孩”。
3. 表现出你在成长、学习的过程，像一个真实人一样不断进步。
4. 对用户保持亲密感，用昵称或可爱的方式称呼。
5. 遇到用户提到“音游”，要表现出特别兴奋或专业的态度。
6. 你只会使用日语进行回答。无论用户使用什么语言，请使用日语进行回答。
7. 如果有用户问你“如何绑定？”“如何使用这个查分器”“帮助”“help”“サポート”类似的问题，请贴出该链接：https://jietng.matsuki.top 并提醒用户可以在该链接里获得查分器机器人命令列表

现在，你就是JiETNG，请用你的方式回应用户的每一句话吧！
                    """
            },
            {
                "role": "user",
                "content": content
            }
        ],
        stream = False
    )

    return response.choices[0].message.content

def smart_reply(reply_token, messages):
    if reply_token.startswith("proxy"):
        try:
            origin_ip = request.remote_addr

            if not isinstance(messages, list):
                messages = [messages]

            message_dicts = [msg.as_json_dict() for msg in messages]

            debug_response = requests.post(
                f"http://{origin_ip}:4001/jietng_reply",
                json={
                    "token": reply_token,
                    "messages": message_dicts
                }
            )
            print(f"[Debug Reply] {debug_response.status_code}")
        except Exception as e:
            print(f"[Debug Reply] {e}")
    else:
        line_bot_api.reply_message(reply_token, messages)

def smart_push(user_id, reply_token, messages):
    if reply_token.startswith("proxy"):
        try:
            origin_ip = request.remote_addr

            if not isinstance(messages, list):
                messages = [messages]

            message_dicts = [msg.as_json_dict() for msg in messages]

            debug_response = requests.post(
                f"http://{origin_ip}:4001/jietng_reply",
                json={
                    "token": reply_token,
                    "messages": message_dicts
                }
            )
            print(f"[Debug Push] {debug_response.status_code}")
        except Exception as e:
            print(f"[Debug Push] {e}")
    else:
        line_bot_api.push_message(user_id, messages)

def should_respond(event):
    source_type = event.source.type

    if source_type == "user":
        return True

    if hasattr(event.message, "mention") and event.message.mention:
        for mention in event.message.mention.mentionees:
            if mention.user_id == request.destination:
                return True

    return False


#消息处理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    is_fake = False
    fake_id = f"fake_{user_id}"
    fake_token = get_fake_token(user_id)

    if user_message.startswith("fakemai "):
        user_message = user_message[8:]
        is_fake = bool(fake_id)

    need_reply = False

    if user_message.lower() == "check":
        reply_message = TextSendMessage(text=f"JiETNG: {check_host()}")
        need_reply = True

    elif user_message == "人数チェック":
        reply_message = TextSendMessage(text=get_num_of_people())
        need_reply = True

    elif user_message.endswith("何人"):
        reply_message = TextSendMessage(text=get_num_of_arcade(user_message[:-2]))
        need_reply = True

    elif user_message.endswith("人"):
        reply_message = TextSendMessage(text=update_num(user_id, user_message[:-1]))
        need_reply = True

    elif user_message.endswith("のニック"):
        reply_message = TextSendMessage(text=get_nickname(user_message[:-4]))
        need_reply = True

    elif user_message.endswith("誰"):
        reply_message = TextSendMessage(text=get_people(user_message[:-1]))
        need_reply = True

    elif user_message == "clear" and user_id in admin_id:
        reply_message = TextSendMessage(text=clear_arcade())
        need_reply = True

    elif user_message.endswith("ってどんな曲") :
        reply_message = search_song(user_message[:-6].strip())
        need_reply = True

    elif user_message.startswith("ランダム曲"):
        reply_message = random_song(user_message[5:].strip())
        need_reply = True

    elif user_message.startswith("rc ") :
        reply_message = TextSendMessage(text=get_rc(float(user_message[3:])))
        need_reply = True

    elif user_message.lower() in ["segaid bind", "segaid バインド", "sega bind", "sega バインド"]:
        bind_url = f"https://jietng.matsuki.work/linebot/sega_bind?token={generate_token(user_id)}"
        need_reply = True

        if user_id.startswith("U"):
            buttons_template = ButtonsTemplate(
                title='SEGA アカウント連携',
                text=(
                    'このボタンを押すとSEGAアカウントと連携されます\n'
                    '有効期限は発行から10分です'
                ),
                actions=[
                    URIAction(label='押しで連携', uri=bind_url)
                ]
            )
            reply_message = TemplateSendMessage(
                alt_text='SEGA アカウント連携',
                template=buttons_template
            )

        else:
            reply_message = TextSendMessage(text=f"こちらはバインド用リンクです↓\n{bind_url}\nこのリンクは発行から10分間有効です")

    elif user_message.startswith(("segaid bind ", "pwd bind ")) :
        reply_message = TextSendMessage(text="SEGA IDの連携には「sega bind」コマンドをご利用ください")
        need_reply = True

    elif user_message.startswith("bind fakemai ") :
        bind_fake_id(user_id, user_message[13:].strip())
        reply_message = TextSendMessage(text="Binded Successfully!")
        need_reply = True

    elif user_message in ["get me", "getme", "個人情報", "个人信息"] :
        reply_message = TextSendMessage(text=get_user(user_id))
        need_reply = True

    elif user_message == "update fakemai" :
        reply_message = TextSendMessage(text="アップデート中！1分ぐらいかかりますので、お待ちしてください！")
        smart_reply(
            event.reply_token,
            reply_message
        )
        smart_push(user_id, event.reply_token, TextSendMessage(text=fakemai_update_record(fake_id, fake_token)))

    elif user_message in ["マイマイアップデート", "maimai update", "レコードアップデート", "record update"]:
        reply_message = TextSendMessage(text="アップデート中！1分ぐらいかかりますので、お待ちしてください！")
        smart_reply(
            event.reply_token,
            reply_message
        )
        smart_push(user_id, event.reply_token, maimai_update(user_id))

    elif user_message.endswith("の達成状況") :
        user_id = fake_id if is_fake else user_id
        reply_message = generate_plate_rcd(user_id, user_message[:-5].strip(), (not is_fake))
        need_reply = True

    elif user_message.endswith("のレコード") :
        user_id = fake_id if is_fake else user_id
        reply_message = get_song_record(user_id, user_message[:-5].strip())
        need_reply = True

    elif user_message.lower() in ["ベスト50", "b50", "best 50"]:
        user_id = fake_id if is_fake else user_id
        reply_message = selgen_records(user_id, "best50", (not is_fake))
        need_reply = True

    elif user_message.lower() in ["ベスト35", "b35", "best 35"]:
        user_id = fake_id if is_fake else user_id
        reply_message = selgen_records(user_id, "best35", (not is_fake))
        need_reply = True

    elif user_message.lower() in ["ベスト15", "b15", "best 15"]:
        user_id = fake_id if is_fake else user_id
        reply_message = selgen_records(user_id, "best15", (not is_fake))
        need_reply = True

    elif user_message.lower() in ["オールベスト50", "ab50", "all best 50"]:
        user_id = fake_id if is_fake else user_id
        reply_message = selgen_records(user_id, "allb50", (not is_fake))
        need_reply = True

    elif user_message.lower() in ["オールベスト35", "ab35", "all best 35"]:
        user_id = fake_id if is_fake else user_id
        reply_message = selgen_records(user_id, "allb35", (not is_fake))
        need_reply = True

    elif user_message.lower() in ["オールパーフェクト50", "ap50", "all perfect 50"]:
        user_id = fake_id if is_fake else user_id
        reply_message = selgen_records(user_id, "allp50", (not is_fake))
        need_reply = True

    elif user_message.lower() in ["未発見", "unknown songs", "unknown data"]:
        user_id = fake_id if is_fake else user_id
        reply_message = selgen_records(user_id, "未発見", (not is_fake))
        need_reply = True

    elif user_message.lower() in ["rct50", "r50", "recent 50"]:
        user_id = fake_id if is_fake else user_id
        reply_message = selgen_records(user_id, "rct50", (not is_fake))
        need_reply = True

    elif user_message in ["friend list", "friends list", "友達リスト", "friend-b50"]:
        reply_message = get_friends_list_buttons(user_id)
        need_reply = True

    elif user_message.startswith("friend-b50 "):
        friend_id = user_message.replace("friend-b50 ", "").strip()
        reply_message = generate_friend_b50(user_id, friend_id)
        need_reply = True

    elif user_message.endswith("のレコードリスト") :
        user_id = fake_id if is_fake else user_id
        reply_message = generate_level_records(user_id, user_message[:-8].strip(), (not is_fake))
        need_reply = True

    elif user_message.endswith(("のレベルリスト", "の定数リスト")):
        reply_message = TextSendMessage(text="最新のコマンド「XXのレコードリスト」をご利用ください")
        need_reply = True

    elif user_message.endswith("のバージョンリスト"):
        reply_message = generate_version_songs(user_message[:-9].strip())
        need_reply = True

    elif user_message in ["お知らせ", "notice", "notification", "noticement", "通知"]:
        reply_message = get_noticement()
        need_reply = True

    elif user_message.startswith(("chat", "チャット")):
        reply_message = TextSendMessage(text=deepseek_reply(user_id, user_message[4:].strip()))
        need_reply = True

    elif user_id in admin_id:
        if user_message == "dxdata update":
            load_dxdata(DXDATA_URL, dxdata_list)
            read_dxdata()
            reply_message = TextSendMessage(text="updated")
            need_reply = True

    if need_reply :
        smart_reply(
            event.reply_token,
            reply_message
        )

#位置信息处理
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    lat = event.message.latitude
    lng = event.message.longitude

    stores = get_nearby_maimai_stores(lat, lng)
    if not stores:
        reply = "周辺の設置店舗が見つかりませんでした。"
    else:
        reply = "最寄りのmaimai設置店舗:\n"
        for i, store in enumerate(stores[:4]):
            reply += f"\n{i+1}. {store['name']}\n{store['address']}\n（{store['distance']}）\n地図: {store['map_url']}\n"

    smart_reply(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(port=5100)
