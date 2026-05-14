"""
JiETNG Maimai DX LINE Bot 主程序
"""

import os
import random
import requests
import json
import re
import traceback
import threading
import queue
import logging
import psutil
import platform
import socket
import secrets
import copy
import asyncio
import aiohttp
import urllib3
import time
import subprocess
import gc
import math
import base64 as b64mod

from functools import wraps
from datetime import datetime

from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO

from flask import (
    Flask,
    request,
    render_template,
    redirect,
    session,
    jsonify,
    send_file,
    send_from_directory
)
from flask_wtf.csrf import CSRFProtect

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    TextMessage,
    ImageMessage,
    TemplateMessage,
    ButtonsTemplate,
    MessageAction,
    URIAction,
    FlexMessage,
    FlexContainer
)
from linebot.v3.messaging.models import MarkMessagesAsReadByTokenRequest, ShowLoadingAnimationRequest
from linebot.v3.webhooks import (
    FollowEvent,
    UnfollowEvent,
    MessageEvent,
    PostbackEvent,
    JoinEvent,
    MemberJoinedEvent,
    TextMessageContent,
    LocationMessageContent
)

# Song and record generators
from modules.song_generator import song_info_generate, generate_version_list
from modules.record_generator import *

# User and data managers
from modules.user_manager import *
from modules.bindtoken_manager import (
    generate_bind_token, get_user_id_from_token,
    generate_perm_token, get_user_id_from_perm_token,
    generate_settings_token, get_user_id_from_settings_token,
)
from modules.notice_manager import *
from modules.notice_stats import *
from modules.tip_ad_manager import (
    load_tip_ad_data,
    get_all_tip_ads,
    create_tip_ad,
    update_tip_ad,
    delete_tip_ad,
    get_tip_ad_by_id
)
from modules.maimai_manager import *
from modules.dxdata_manager import update_dxdata_with_comparison
from modules.record_manager import *
from modules.devtoken_manager import (
    verify_dev_token,
    load_dev_tokens,
    create_dev_token,
    save_dev_tokens,
    list_dev_tokens,
    revoke_dev_token,
    get_token_info,
    flush_dev_tokens
)

from modules.perm_request_handler import (
    send_perm_request,
    accept_perm_request,
    reject_perm_request,
    get_pending_perm_requests
)

# Config loader
from modules.config_loader import *

# Backup manager
from modules.backup_manager import create_backup

# UI and message modules
from modules.message_manager import *

# Image processing
from modules.image_uploader import smart_upload, _start_periodic_cleanup
from modules.image_manager import *

# System utilities
from modules.system_checker import run_system_check, clean_unbound_users
from modules.event_tracker import track_event, get_business_stats, get_hourly_stats
from modules.rate_limiter import check_rate_limit
from modules.line_messenger import smart_reply, smart_push, notify_admins_error, notify_on_error
from modules.perm_request_generator import generate_perm_request_message
from modules.notification_manager import (
    get_notifications,
    clear_notifications,
    add_push_subscription,
    remove_push_subscription
)
from modules.song_matcher import find_matching_songs, normalize_text
from modules.memory_manager import memory_manager, cleanup_user_caches, cleanup_rate_limiter_tracking

# Module aliases for specific use cases
import modules.user_manager as user_manager_module
import modules.rate_limiter as rate_limiter_module

from modules.storelist_generator import generate_store_buttons

# ==================== 常量定义 ====================

# 队列配置
MAX_QUEUE_SIZE = 10
MAX_CONCURRENT_IMAGE_TASKS = 5  # 图片生成并发数
WEB_MAX_CONCURRENT_TASKS = 2    # 网络任务并发数
TASK_TIMEOUT_SECONDS = 120

# 搜索结果限制
MAX_SEARCH_RESULTS = 10

# ==================== 日志配置 ====================

# 配置日志
# 带颜色的日志格式化器
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    GRAY = '\033[90m'

    def format(self, record):
        # 为级别名添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # 时间戳使用灰色
        formatted = super().format(record)
        formatted = formatted.replace(record.asctime, f"{self.GRAY}{record.asctime}{self.RESET}", 1)

        return formatted

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='assets', static_url_path='/static')
app.secret_key = secrets.token_hex(32)  # 用于session加密

# 配置成绩命令列表
RANK_COMMANDS = {
    # Best 系列
    ("b50", "best50"): "best50",
    ("b40", "best40"): "best40",
    ("b35", "best35"): "best35",
    ("b15", "best15"): "best15",

    # All Best 系列
    ("ab35", "allb35"): "allb35",
    ("ab50", "allb50"): "allb50",

    # 特殊系列
    ("apb50", "ap50"): "apb50",
    ("fdxb50", "fdx50"): "fdxb50",
    ("rct50", "r50"): "rct50",
    ("idealb50", "idlb50"): "idlb50",
    ("unknown", "unkn"): "unknown",
}

# 启用 CSRF 保护
csrf = CSRFProtect(app)

# 配置安全响应头
@app.after_request
def set_security_headers(response):
    """设置安全响应头 + 内存清理"""
    # 防止 XSS 攻击
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:;"
    )

    # Strict Transport Security (如果使用 HTTPS)
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # 每次请求后执行快速垃圾回收（generation 0）
    gc.collect(0)

    return response

# 记录服务启动时间和统计
SERVICE_START_TIME = datetime.now()

# 使用字典存储统计数据,避免global变量问题
STATS = {
    'tasks_processed': 0,
    'response_time': 0.0
}
stats_lock = threading.Lock()  # 保护统计数据的线程锁

# ==================== 任务队列系统 ====================

# 图片生成任务队列 (处理图片生成任务，如 b50 等)
image_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
image_concurrency_limit = threading.Semaphore(MAX_CONCURRENT_IMAGE_TASKS)

# Web任务队列 (处理耗时的网络请求，如 maimai_update 等)
webtask_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
webtask_concurrency_limit = threading.Semaphore(WEB_MAX_CONCURRENT_TASKS)


def run_task_with_limit(func: callable, args: tuple, sem: threading.Semaphore,
                        q: queue.Queue, task_id: str = None, is_web_task: bool = False) -> None:
    """
    在并发限制下运行任务

    Args:
        func: 要执行的函数
        args: 函数参数元组
        sem: 信号量,用于控制并发数
        q: 任务队列
        task_id: 任务 ID
        is_web_task: 是否是 web 任务
    """
    start_time = datetime.now()

    # 添加到运行中的任务
    if task_id:
        with task_tracking_lock:
            # 从排队中移除
            task_tracking['queued'] = [t for t in task_tracking['queued'] if t.get('id') != task_id]
            # 添加到运行中
            # 智能提取 user_id：尝试多种方式
            user_id_for_tracking = 'Unknown'
            if args:
                if hasattr(args[0], 'source'):  # Event 对象
                    user_id_for_tracking = args[0].source.user_id
                elif isinstance(args[0], str) and args[0].startswith('U'):  # 直接传入的 user_id 字符串
                    user_id_for_tracking = args[0]

            task_info = {
                'id': task_id,
                'function': func.__name__,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': user_id_for_tracking
            }
            task_tracking['running'].append(task_info)

    with sem:
        task_done = threading.Event()

        def target():
            try:
                func(*args)
            except Exception as e:
                logger.error(f"[Task] ✗ Execution error: function={func.__name__}, error={e}", exc_info=True)

                # 尝试获取用户信息以便回复
                user_id = None
                reply_token = None
                if args:
                    if hasattr(args[0], 'source') and hasattr(args[0], 'reply_token'):
                        # Event 对象
                        user_id = args[0].source.user_id
                        reply_token = args[0].reply_token
                    elif isinstance(args[0], str) and args[0].startswith('U'):
                        # 直接传入的 user_id 字符串
                        user_id = args[0]
                        # reply_token 可能在 args[1]
                        if len(args) > 1 and isinstance(args[1], str):
                            reply_token = args[1]

                # 通知管理员
                notify_admins_error(
                    error_title=f"Task Execution Failed: {func.__name__}",
                    error_details=f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}",
                    context={
                        "Task": func.__name__,
                        "Error Type": type(e).__name__,
                    },
                    user_id=user_id
                )

                # 回复用户
                if user_id and reply_token:
                    try:
                        smart_reply(user_id, reply_token, system_error(user_id), configuration)
                    except Exception:
                        pass
            finally:
                task_done.set()

        thread = threading.Thread(target=target)
        thread.start()

        timer = threading.Timer(TASK_TIMEOUT_SECONDS, cancel_if_timeout, args=(task_done,))
        timer.start()

        thread.join()
        timer.cancel()

        # 任务完成后更新统计(在主流程中,不在子线程中)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000

        # 从运行中的任务移除，并添加到已完成列表
        if task_id:
            with task_tracking_lock:
                # 找到运行中的任务信息
                task_info = None
                for t in task_tracking['running']:
                    if t.get('id') == task_id:
                        task_info = t.copy()
                        break

                # 从运行中移除
                task_tracking['running'] = [t for t in task_tracking['running'] if t.get('id') != task_id]

                # 添加到已完成列表
                if task_info:
                    task_info['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
                    task_info['duration'] = f"{response_time/1000:.2f}s"

                    # 在列表开头插入（最新的在前面）
                    task_tracking['completed'].insert(0, task_info)

                    # 保持最多20个已完成任务
                    if len(task_tracking['completed']) > MAX_COMPLETED_TASKS:
                        task_tracking['completed'] = task_tracking['completed'][:MAX_COMPLETED_TASKS]

        with stats_lock:
            STATS['tasks_processed'] += 1
            STATS['response_time'] += response_time
            logger.info(f"[Task] ✓ Completed: function={func.__name__}, total={STATS['tasks_processed']}, avg_time={STATS['response_time']/STATS['tasks_processed']:.1f}ms")


@notify_on_error("Image Task Worker Error", context={"Worker": "image_worker"}, reraise=False)
def _run_image_task(item):
    func, args, task_id = (item if len(item) == 3 else (*item, None))
    run_task_with_limit(func, args, image_concurrency_limit, image_queue, task_id, False)


def image_worker() -> None:
    """图片生成任务队列的工作线程"""
    while True:
        item = image_queue.get()
        try:
            _run_image_task(item)
        finally:
            image_queue.task_done()


@notify_on_error("Web Task Worker Error", context={"Worker": "webtask_worker"}, reraise=False)
def _run_webtask(item):
    func, args, task_id = (item if len(item) == 3 else (*item, None))
    run_task_with_limit(func, args, webtask_concurrency_limit, webtask_queue, task_id, True)


def webtask_worker() -> None:
    """Web任务队列的工作线程"""
    while True:
        item = webtask_queue.get()
        try:
            _run_webtask(item)
        finally:
            webtask_queue.task_done()



def cancel_if_timeout(task_done: threading.Event) -> None:
    """
    检查任务是否超时

    Args:
        task_done: 任务完成事件
    """
    if not task_done.is_set():
        logger.warning(f"[Task] ⚠ Execution timeout: timeout={TASK_TIMEOUT_SECONDS}s")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ==================== API 认证装饰器 ====================

def require_dev_token(f):
    """
    验证开发者 token 的装饰器

    使用方法:
    @app.route('/api/endpoint')
    @require_dev_token
    def endpoint():
        # token_info 会被添加到 request 对象中
        token_info = request.token_info
        return jsonify({"status": "success"})
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从 Authorization header 获取 token
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                "error": "No authorization header",
                "message": "Authorization header is required"
            }), 401

        # 检查 Bearer token 格式
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                "error": "Invalid authorization header",
                "message": "Authorization header must be in format: Bearer <token>"
            }), 401

        token = parts[1]

        # 验证 token
        token_info = verify_dev_token(token)
        if not token_info:
            return jsonify({
                "error": "Invalid token",
                "message": "Token is invalid or has been revoked"
            }), 401

        # 将 token 信息添加到 request 对象中
        request.token_info = token_info

        return f(*args, **kwargs)

    return decorated_function


def require_user_permission(f):
    """
    验证 token 是否有权限访问指定用户的装饰器

    必须在 @require_dev_token 之后使用

    使用方法:
    @app.route('/api/endpoint/<user_id>')
    @csrf.exempt
    @require_dev_token
    @require_user_permission
    def endpoint(user_id):
        # 此时已验证 token 有权限访问 user_id
        return jsonify({"status": "success"})

    权限检查逻辑:
    1. 如果用户是通过该 token 创建的 (registered_via_token) - 允许访问
    2. 如果 token 的 allowed_users 列表包含该用户 - 允许访问
    3. 否则拒绝访问
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取 user_id 参数
        user_id = kwargs.get('user_id')
        if not user_id:
            return jsonify({
                "error": "Missing parameter",
                "message": "user_id is required"
            }), 400

        # 获取 token 信息（由 require_dev_token 装饰器提供）
        token_info = request.token_info
        token_id = token_info['token_id']

        # 使用辅助函数检查权限
        has_permission, error_response = check_user_permission(user_id, token_id)
        if not has_permission:
            return error_response

        return f(*args, **kwargs)

    return decorated_function


def require_owner_permission(f):
    """
    验证 token 是否为用户的所有者（创建者）的装饰器

    只允许创建该用户的 token 访问，不允许被授权的 token 访问
    用于敏感操作如：删除用户、管理权限等

    必须在 @require_dev_token 之后使用

    使用方法:
    @app.route('/api/endpoint/<user_id>')
    @csrf.exempt
    @require_dev_token
    @require_owner_permission
    def endpoint(user_id):
        # 此时已验证 token 是 user_id 的所有者（创建者）
        return jsonify({"status": "success"})

    权限检查逻辑:
    只检查用户是否通过该 token 创建 (registered_via_token)
    不检查 allowed_users 列表
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取 user_id 参数
        user_id = kwargs.get('user_id')
        if not user_id:
            return jsonify({
                "error": "Missing parameter",
                "message": "user_id is required"
            }), 400

        # 检查用户是否存在
        if user_id not in USERS:
            return jsonify({
                "error": "User not found",
                "message": f"User {user_id} does not exist"
            }), 404

        # 获取 token 信息（由 require_dev_token 装饰器提供）
        token_info = request.token_info
        token_id = token_info['token_id']

        # 只检查是否为所有者（创建者）
        if USERS[user_id].get('registered_via_token') != token_id:
            return jsonify({
                "error": "Forbidden",
                "message": "Only the owner token (creator) can perform this operation"
            }), 403

        return f(*args, **kwargs)

    return decorated_function


def check_user_permission(user_id, token_id):
    """
    检查 token 是否有权限访问指定用户的辅助函数

    Args:
        user_id: 用户ID
        token_id: Token ID

    Returns:
        tuple: (has_permission: bool, error_response: dict or None)
    """

    # 检查用户是否存在
    if user_id not in USERS:
        return False, (jsonify({
            "error": "User not found",
            "message": f"User {user_id} does not exist"
        }), 404)

    # 检查权限：方式1 - 用户是通过该 token 创建的
    if USERS[user_id].get('registered_via_token') == token_id:
        return True, None

    # 检查权限：方式2 - token 的 allowed_users 列表包含该用户
    dev_tokens = load_dev_tokens()
    if token_id in dev_tokens:
        allowed_users = dev_tokens[token_id].get('allowed_users', [])
        if user_id in allowed_users:
            return True, None

    # 没有权限
    return False, (jsonify({
        "error": "Permission denied",
        "message": f"Token does not have permission to access user {user_id}"
    }), 403)

# ==================== Flask 路由 ====================

@app.route("/linebot/webhook", methods=['POST'])
@csrf.exempt
def linebot_reply():
    """
    LINE Webhook 接收端点

    接收并处理来自LINE平台的webhook事件

    Returns:
        tuple: ('OK', 200) 表示成功接收
    """
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logger.info("[Webhook] → Received request")

    try:
        json_data = json.loads(body)
        destination = json_data.get("destination")
        request.destination = destination
        handler.handle(body, signature)
        # 签名校验通过后再追踪（避免把无效请求计入指标）
        try:
            for _ev in json_data.get('events', []):
                _uid = _ev.get('source', {}).get('userId')
                track_event('line_webhook', user_id=_uid, metadata={'type': _ev.get('type')})
        except Exception:
            pass

    except Exception as e:
        is_bad_request = isinstance(e, (json.JSONDecodeError, InvalidSignatureError))
        logger.error(f"[Webhook] ✗ {'Bad request' if is_bad_request else 'Handling error'}: error={e}", exc_info=not is_bad_request)

        # 尝试回复用户错误消息（非坏请求时，json_data 已解析成功）
        if not is_bad_request:
            try:
                events = json_data.get('events', [])
                if events:
                    ev = events[0]
                    reply_token = ev.get('replyToken')
                    uid = ev.get('source', {}).get('userId')
                    if reply_token and uid:
                        smart_reply(uid, reply_token, system_error(uid), configuration, addition=False)
            except Exception:
                pass

        _notif_uid = None
        if not is_bad_request:
            try:
                _notif_uid = json_data.get('events', [{}])[0].get('source', {}).get('userId')
            except Exception:
                pass
        notify_admins_error(
            error_title="Webhook Error",
            error_details=f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}",
            context={"Error": type(e).__name__, "Detail": str(e)[:200]},
            user_id=_notif_uid
        )

    return 'OK', 200

@app.route("/static/admin-icon.png")
def admin_pwa_icon():
    """动态生成带背景和留白的 PWA 图标"""
    size = 512
    padding = int(size * 0.18)  # 18% 留白
    logo_size = size - padding * 2

    bg_color = (22, 33, 62, 255)  # 深蓝背景，与 admin panel 风格一致

    canvas = Image.new('RGBA', (size, size), bg_color)

    with Image.open(LOGO_FILE) as logo:
        logo = logo.convert('RGBA')
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        canvas.paste(logo, (padding, padding), logo)

    buf = BytesIO()
    canvas.convert('RGB').save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route("/sw.js")
def service_worker():
    """提供 Service Worker 文件（必须从根路径提供以控制 /admin/ 范围）"""
    response = app.send_static_file('sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/admin/'
    return response


@app.route("/linebot/adding", methods=["GET"])
@app.route("/linebot/add", methods=["GET"])
def line_add_page():
    """重定向到LINE添加好友页面"""
    return redirect(LINE_ADDING_URL)


@app.route("/linebot/img/<image_id>", methods=["GET"])
def serve_image(image_id):
    """提供本地图床的图片访问

    Args:
        image_id: 图片ID

    Returns:
        图片文件或404错误
    """
    # 验证image_id格式（防止路径穿越攻击）
    if not image_id.replace('-', '').replace('_', '').isalnum():
        logger.warning(f"[ImageHost] ⚠ Invalid image_id format: id={image_id}")
        return send_from_directory('assets/pics', '404.png', mimetype='image/png'), 404

    # 添加.png扩展名
    filename = f"{image_id}.png"
    image_path = os.path.join(IMG_DIR, filename)

    # 检查文件是否存在
    if not os.path.exists(image_path):
        logger.warning(f"[ImageHost] ⚠ Image not found: id={image_id}")
        return send_from_directory('assets/pics', '404.png', mimetype='image/png'), 404

    logger.info(f"[ImageHost] → Serving image: id={image_id}")
    return send_from_directory(IMG_DIR, filename, mimetype='image/png')


@app.route("/linebot/sega_bind", methods=["GET", "POST"])
def website_segaid_bind():
    """
    SEGA账户绑定页面

    GET: 显示绑定表单
    POST: 处理绑定请求

    Query Args:
        token: 绑定Token (GET/POST)
        mode: 模式 (bind/rebind，默认 bind)

    Form Data (POST):
        segaid: SEGA ID
        password: 密码
        ver: 服务器版本 (jp/intl)
        aime: Aime卡选择 (仅jp有，intl默认1)
        timezone: 时区
        language: 语言
    """
    token = request.args.get("token")
    mode = request.args.get("mode", "bind")
    if not token:
        # Token 未提供的错误消息（此时还没有 user_id，三语同时显示）
        token_missing_message = """トークンが提供されていません。<br />
Token not provided. <br />
未提供令牌。"""
        return render_template("error.html", message=token_missing_message, language="ja"), 400

    try:
        user_id = get_user_id_from_token(token)
        if user_id not in USERS:
            token_invalid_message = "トークンが無効です。<br />Invalid token. <br />令牌无效。"
            return render_template("error.html", message=token_invalid_message, language="ja"), 400
        
    except Exception as e:
        logger.error(f"[Auth] ✗ Token verification failed: error={e}")
        token_invalid_message = "トークンが無効です。<br />Invalid token. <br />令牌无效。"
        return render_template("error.html", message=token_invalid_message, language="ja"), 400

    if request.method == "POST":
        segaid = request.form.get("segaid")
        password = request.form.get("password")
        user_version = request.form.get("ver", "jp")
        aime = request.form.get("aime", "0")

        # 获取用户数据
        user_data = USERS.get(user_id, {})

        if mode == "rebind":
            # rebind 模式下保持现有 timezone 和 language 不变
            user_timezone = str(user_data.get("timezone", 9))
            user_language = user_data.get("language", "ja")
        else:
            user_timezone = request.form.get("timezone", "9")
            user_language = request.form.get("language", user_data.get("language", "ja"))

        # 检查用户是否已经绑定账号（仅在 bind 模式下检查）
        has_account = all(key in user_data for key in ['sega_id', 'sega_pwd', 'version'])

        if mode == "bind" and has_account:
            error_messages = {
                "ja": "すでに SEGA アカウントが連携されています。再度連携する場合は、先に unbind コマンドで連携を解除してください。",
                "en": "A SEGA account is already linked. To rebind, please use the unbind command first to unlink your account.",
                "zh": "已绑定 SEGA 账号。如需重新绑定，请先使用 unbind 命令解除绑定。"
            }
            return render_template("error.html", message=error_messages.get(user_language, error_messages["ja"]), language=user_language), 400

        # 在 rebind 模式下，验证 segaid 必须与现有的一致
        if mode == "rebind":
            if not has_account:
                error_messages = {
                    "ja": "アカウントが連携されていません。",
                    "en": "No account is linked.",
                    "zh": "未绑定账号。"
                }
                return render_template("error.html", message=error_messages.get(user_language, error_messages["ja"]), language=user_language), 400

            if segaid != user_data.get('sega_id'):
                error_messages = {
                    "ja": "SEGA ID を変更することはできません。",
                    "en": "You cannot change the SEGA ID.",
                    "zh": "无法更改 SEGA ID。"
                }
                return render_template("error.html", message=error_messages.get(user_language, error_messages["ja"]), language=user_language), 400

        if not segaid or not password:
            missing_fields_messages = {
                "ja": "すべての項目を入力してください。",
                "en": "Please fill in all fields.",
                "zh": "请填写所有字段。"
            }
            return render_template("error.html", message=missing_fields_messages.get(user_language, missing_fields_messages["ja"]), language=user_language), 400

        # 转换时区为整数
        try:
            timezone_int = int(user_timezone)
        except (ValueError, TypeError):
            timezone_int = 9  # 默认 UTC+9

        # 转换 aime 为整数
        try:
            aime_int = int(aime)
        except (ValueError, TypeError):
            aime_int = 0  # 默认 0

        result = asyncio.run(process_sega_credentials(user_id, segaid, password, user_version, user_language, timezone_int, aime_int, (mode == "rebind")))
        if result == "MAINTENANCE":
            maintenance_messages = {
                "ja": "公式サイトがメンテナンス中です。しばらくしてからもう一度お試しください。",
                "en": "The official website is under maintenance. Please try again later.",
                "zh": "官方网站正在维护中。请稍后再试。"
            }
            return render_template("error.html", message=maintenance_messages.get(user_language, maintenance_messages["ja"]), language=user_language), 503
        elif result:
            via_token = "registered_via_token" in USERS.get(user_id, {})
            if mode == "bind":
                # API token 创建的用户不再跑 bind 自动同步推送，但依然计入绑定事件
                if not via_token:
                    task_id = f"bind_{secrets.token_hex(8)}"
                    webtask_queue.put_nowait((async_bind_update_task, (user_id, user_version), task_id))
                track_event('user_bind', user_id=user_id, metadata={'version': user_version, 'via_token': via_token})
            else:
                track_event('user_rebind', user_id=user_id, metadata={'version': user_version, 'via_token': via_token})
                if not via_token:
                    try:
                        smart_push(user_id, rebind_msg(user_id), configuration)
                    except Exception as e:
                        logger.error(f"[Rebind] ⚠ Failed to push: {e}")
            return render_template("success.html", language=user_language, mode=mode)
        else:
            invalid_credentials_messages = {
                "ja": "SEGA ID または パスワード が正しくありません。もう一度確認してください。",
                "en": "Invalid SEGA ID or password. Please check and try again.",
                "zh": "SEGA ID 或密码不正确。请检查后重试。"
            }
            return render_template("error.html", message=invalid_credentials_messages.get(user_language, invalid_credentials_messages["ja"]), language=user_language), 500

    # GET 请求时，从用户数据中获取语言设置和其他信息
    user_data = USERS.get(user_id, {})
    user_language = user_data.get("language")
    if not user_language:
        # 首次绑定时，尝试从 LINE profile 自动检测语言
        try:
            with ApiClient(configuration) as api_client:
                profile = MessagingApi(api_client).get_profile(user_id)
                profile_lang = getattr(profile, 'language', None) or ''
                if profile_lang.startswith('zh'):
                    user_language = 'zh'
                elif profile_lang.startswith('ja'):
                    user_language = 'ja'
                else:
                    user_language = 'en'
        except Exception:
            user_language = 'en'

    # 在 rebind 模式下，传递现有账号数据到模板（不含 timezone/language/权限）
    if mode == "rebind":
        return render_template(
            "bind_form.html",
            user_language=user_language,
            mode="rebind",
            segaid=user_data.get('sega_id', ''),
            password=user_data.get('sega_pwd', ''),
            version=user_data.get('version', 'jp'),
            aime=user_data.get('aime', 0),
        )
    else:
        return render_template("bind_form.html", user_language=user_language, mode="bind")


@app.route("/linebot/settings", methods=["GET", "POST"])
def website_settings():
    """
    个人偏好设置页面

    GET: 显示设置表单（timezone, language, 背景图, 权限管理）
    POST: 保存设置

    Query Args:
        token: 绑定Token

    Form Data (POST):
        timezone: 时区
        language: 语言
        bg_files: 逗号分隔的背景图文件名列表
        bg_enabled_hidden: 背景图开关（"1" 或 "0"）
    """
    token = request.args.get("token")
    if not token:
        token_missing_message = """トークンが提供されていません。<br />
Token not provided. <br />
未提供令牌。"""
        return render_template("error.html", message=token_missing_message, language="ja"), 400

    try:
        user_id = get_user_id_from_settings_token(token)
        if user_id not in USERS:
            token_invalid_message = "トークンが無効です。<br />Invalid token. <br />令牌无效。"
            return render_template("error.html", message=token_invalid_message, language="ja"), 400
    except Exception as e:
        logger.error(f"[Auth] ✗ Settings token verification failed: error={e}")
        token_invalid_message = "トークンが無効です。<br />Invalid token. <br />令牌无效。"
        return render_template("error.html", message=token_invalid_message, language="ja"), 400

    user_data = USERS.get(user_id, {})

    # 检查用户是否已绑定账号
    has_account = all(key in user_data for key in ['sega_id', 'sega_pwd', 'version'])
    if not has_account:
        error_messages = {
            "ja": "アカウントが連携されていません。",
            "en": "No account is linked.",
            "zh": "未绑定账号。"
        }
        user_language = user_data.get("language", "ja")
        return render_template("error.html", message=error_messages.get(user_language, error_messages["ja"]), language=user_language), 400

    custom_bg_filename = f"jietnguser_{user_id}.webp"

    if request.method == "POST":
        user_language = request.form.get("language", user_data.get("language", "ja"))
        user_timezone = request.form.get("timezone", "9")
        bg_files_str = request.form.get("bg_files", "")

        # 转换时区为整数
        try:
            timezone_int = int(user_timezone)
        except (ValueError, TypeError):
            timezone_int = 9

        # 解析背景图列表
        if bg_files_str.strip():
            bg_files_list = [f.strip() for f in bg_files_str.split(",") if f.strip()]
        else:
            bg_files_list = []

        # 处理背景图开关
        bg_enabled = request.form.get("bg_enabled_hidden", "0") == "1"

        # 保存设置
        edit_user_value(user_id, "language", user_language)
        edit_user_value(user_id, "timezone", timezone_int)
        edit_user_value(user_id, "bg_files", bg_files_list)
        edit_user_value(user_id, "bg_enabled", bg_enabled)

        return render_template("success.html", language=user_language, mode="settings")

    # GET: 准备数据
    user_language = user_data.get("language", "ja")

    # 扫描背景图目录
    try:
        other_bg_files = sorted([
            f for f in os.listdir(BG_DIR)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
            and not _is_user_custom_bg(f)
        ])
        # 自定义背景排在最前
        if os.path.exists(os.path.join(BG_DIR, custom_bg_filename)):
            all_bg_files = [custom_bg_filename] + other_bg_files
        else:
            all_bg_files = other_bg_files
    except Exception:
        all_bg_files = []

    user_bg_files = user_data.get("bg_files", [])
    has_custom_bg = os.path.exists(os.path.join(BG_DIR, custom_bg_filename))
    bg_enabled = user_data.get("bg_enabled", False)

    # 权限列表
    dev_tokens = load_dev_tokens()
    owner_token_id = user_data.get('registered_via_token', '')
    perm_list = []
    if owner_token_id and owner_token_id in dev_tokens:
        perm_list.append({
            'token_id': owner_token_id,
            'note': dev_tokens[owner_token_id].get('note', owner_token_id),
            'is_owner': True,
        })
    for tid, tdata in dev_tokens.items():
        if user_id in tdata.get('allowed_users', []):
            perm_list.append({
                'token_id': tid,
                'note': tdata.get('note', tid),
                'is_owner': False,
            })

    return render_template(
        "settings.html",
        user_language=user_language,
        timezone=user_data.get('timezone', 9),
        bg_files=all_bg_files,
        user_bg_files=user_bg_files,
        bg_enabled=bg_enabled,
        has_custom_bg=has_custom_bg,
        custom_bg_filename=custom_bg_filename,
        perm_token=generate_perm_token(user_id),
        perm_list=perm_list,
    )


@app.route("/linebot/settings/custom_bg", methods=["POST", "DELETE"])
@csrf.exempt
def manage_custom_bg():
    """上传或删除用户自定义背景图"""
    token = request.args.get("token")
    if not token:
        return jsonify({"success": False, "message": "Token not provided"}), 400

    try:
        user_id = get_user_id_from_settings_token(token)
        if user_id not in USERS:
            return jsonify({"success": False, "message": "Invalid token"}), 400
    except Exception:
        return jsonify({"success": False, "message": "Invalid token"}), 400

    ALLOWED_BG_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif'}
    MAX_BG_SIZE = 5 * 1024 * 1024
    custom_bg_filename = f"jietnguser_{user_id}.webp"
    custom_bg_path = os.path.join(BG_DIR, custom_bg_filename)

    if request.method == "DELETE":
        if os.path.exists(custom_bg_path):
            try:
                os.remove(custom_bg_path)
                logger.info(f"[Settings] ✓ Deleted custom bg: user_id={user_id}")
            except Exception as e:
                logger.error(f"[Settings] ✗ Failed to delete custom bg: user_id={user_id}, error={e}")
                return jsonify({"success": False, "message": "Failed to delete"}), 500

        bg_files = USERS[user_id].get("bg_files", [])
        if custom_bg_filename in bg_files:
            bg_files.remove(custom_bg_filename)
            edit_user_value(user_id, "bg_files", bg_files)

        return jsonify({"success": True}), 200

    # POST: 上传（接收 base64 JSON）
    body = request.get_json(silent=True)
    if not body or 'data' not in body or 'filename' not in body:
        return jsonify({"success": False, "message": "No file provided"}), 400

    original_ext = os.path.splitext(body['filename'])[1].lower()
    if original_ext not in ALLOWED_BG_EXTENSIONS:
        return jsonify({"success": False, "message": "Unsupported format"}), 400

    try:
        file_data = b64mod.b64decode(body['data'])
    except Exception:
        return jsonify({"success": False, "message": "Invalid data"}), 400

    if len(file_data) > MAX_BG_SIZE:
        return jsonify({"success": False, "message": "File too large"}), 400

    try:
        from PIL import Image as PILImage
        from io import BytesIO as BIO
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass
        img = PILImage.open(BIO(file_data))
        img.load()
        img = img.convert("RGB")
        img.save(custom_bg_path, "WEBP", quality=85)
        logger.info(f"[Settings] ✓ Uploaded custom bg: user_id={user_id}, ext={original_ext}, size={len(file_data)}")
    except Exception as e:
        logger.error(f"[Settings] ✗ Failed to process uploaded bg: user_id={user_id}, ext={original_ext}, error={e}")
        return jsonify({"success": False, "message": "Invalid image"}), 400

    return jsonify({"success": True, "filename": custom_bg_filename}), 201


def _is_user_custom_bg(filename):
    """判断文件名是否为用户自定义背景图（格式: jietnguser_{user_id}.webp）"""
    return filename.startswith('jietnguser_')


def _get_user_bg_filter(user_id):
    """
    根据用户设置返回 compose_images 的 bg_filter 参数
    - bg_enabled=False → []
    - bg_enabled=True, bg_files 非空 → bg_files
    - bg_enabled=True, bg_files 为空 → None (全部随机)
    """
    udata = USERS.get(user_id, {})
    if not udata.get('bg_enabled', False):
        return None
    bg_files = udata.get('bg_files', [])
    return bg_files


@app.route("/linebot/perms/revoke", methods=["POST"])
@csrf.exempt
def linebot_perms_revoke():
    """
    用户通过 bind_form 权限管理面板撤销某 token 的访问权限

    请求体 (JSON):
    - perm_token: 权限管理 Token（页面加载时生成，10分钟有效）
    - token_id: 要撤销的 token ID
    """
    data = request.form.to_dict() or request.get_json(force=True, silent=True) or {}
    perm_token = data.get('perm_token', '')
    token_id_to_revoke = data.get('token_id', '')

    try:
        user_id = get_user_id_from_perm_token(perm_token)
    except ValueError:
        return jsonify({"error": "Invalid or expired token"}), 401

    if user_id not in USERS:
        return jsonify({"error": "User not found"}), 404

    if USERS[user_id].get('registered_via_token') == token_id_to_revoke:
        return jsonify({"error": "Cannot revoke owner permission"}), 403

    dev_tokens = load_dev_tokens()
    if token_id_to_revoke not in dev_tokens:
        return jsonify({"error": "Token not found"}), 404

    allowed_users = dev_tokens[token_id_to_revoke].get('allowed_users', [])
    if user_id not in allowed_users:
        return jsonify({"error": "Permission not found"}), 404

    allowed_users.remove(user_id)
    dev_tokens[token_id_to_revoke]['allowed_users'] = allowed_users
    save_dev_tokens(dev_tokens)

    logger.info(f"[Permission] Web revoke: token_id={token_id_to_revoke}, user_id={user_id}")
    return jsonify({"success": True})


DEMO_CORS_ORIGIN = "https://jietng.matsuk1.com"

def _demo_cors(response):
    response.headers["Access-Control-Allow-Origin"] = DEMO_CORS_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.route("/linebot/demo", methods=["POST", "OPTIONS"])
@csrf.exempt
def demo_page():
    if request.method == "OPTIONS":
        return _demo_cors(app.make_response(("", 204)))

    segaid = request.form.get("segaid", "").strip()
    password = request.form.get("password", "").strip()
    ver = request.form.get("ver", "jp")
    cmd_type = request.form.get("cmd_type", "best50").strip()
    params = request.form.get("params", "").strip()
    try:
        tz = int(request.form.get("timezone", "9"))
        tz = max(-12, min(14, tz))
    except (ValueError, TypeError):
        tz = 9

    if not segaid or not password:
        return _demo_cors(jsonify({"error": "Please fill in SEGA ID and password."})), 400
    if ver not in ("jp", "intl"):
        return _demo_cors(jsonify({"error": "Invalid version."})), 400

    _VALID_CMD_TYPES = {"best50", "best40", "best35", "best15", "allb35", "allb50", "apb50", "fdxb50", "idlb50"}
    if cmd_type not in _VALID_CMD_TYPES:
        cmd_type = "best50"
    title = cmd_type.upper()

    async def _pipeline():
        cookies = await login_to_maimai(segaid, password, ver=ver)
        if not cookies or cookies == "MAINTENANCE":
            return cookies
        user_info, raw_records = await asyncio.gather(
            get_maimai_info(cookies, ver=ver),
            get_maimai_records(cookies, ver=ver)
        )
        song_record = get_detailed_info(raw_records, ver=ver)
        up_songs, down_songs, details = select_records(song_record, type=cmd_type, command=params, ver=ver)
        profile_img = generate_profile(user_info)
        records_img = generate_records_picture(up_songs, down_songs, title=title, ver=ver, details=details)
        return compose_images([profile_img, records_img], spacing=0, border_width=0, timezone_offset=tz)

    try:
        result = asyncio.run(_pipeline())
        if result == "MAINTENANCE":
            return _demo_cors(jsonify({"error": "The official website is under maintenance. Please try again later."})), 503
        if not result:
            return _demo_cors(jsonify({"error": "Login failed. Please check your SEGA ID and password."})), 401
        buf = BytesIO()
        result.save(buf, "PNG")
        buf.seek(0)
        return _demo_cors(send_file(buf, mimetype="image/png"))
    except Exception as e:
        logger.error(f"[Demo] Pipeline error: {e}", exc_info=True)
        return _demo_cors(jsonify({"error": "An error occurred while generating your score card."})), 500


async def process_sega_credentials(user_id, segaid, password, ver="jp", language="ja", timezone=9, aime=0, rebind=False):
    base = (
        "https://maimaidx-eng.com/maimai-mobile"
        if ver == "intl"
        else "https://maimaidx.jp/maimai-mobile"
    )

    cookies = await login_to_maimai(segaid, password, ver=ver, aime=aime)
    if cookies == "MAINTENANCE":
        return "MAINTENANCE"
    if not cookies:
        logger.warning(f"[Auth] ⚠ Login failed for user_id={user_id}")
        return False

    # 验证登录是否成功
    connector = aiohttp.TCPConnector(ssl=False, limit=10)
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    async with aiohttp.ClientSession(cookies=cookies, connector=connector, timeout=timeout) as session:
        dom = await fetch_dom(session, f"{base}/home/", ver)

        if dom is None:
            return False

    edit_user_value(user_id, 'sega_id', segaid)
    edit_user_value(user_id, 'sega_pwd', password)
    edit_user_value(user_id, 'version', ver)
    edit_user_value(user_id, 'aime', aime)
    edit_user_value(user_id, 'language', language)
    edit_user_value(user_id, 'timezone', timezone)

    return True


# ==================== 用户管理函数 ====================

def user_unbind(user_id):
    msg = unbind_msg(user_id)
    delete_user(user_id)
    return msg

# ==================== 异步任务处理函数 ====================

def async_maimai_update_task(event):
    """异步maimai更新任务 - 在webtask_queue中执行"""
    user_id = event.source.user_id
    reply_token = event.reply_token

    # 获取用户版本
    ver = "jp"
    if user_id in USERS and 'version' in USERS[user_id]:
        ver = USERS[user_id]['version']

    try:
        reply_msg = asyncio.run(maimai_update(user_id, ver))
        track_event('sync_task', user_id=user_id, metadata={'success': True, 'trigger': 'user'})
    except Exception as e:
        track_event('sync_task', user_id=user_id, metadata={'success': False, 'trigger': 'user', 'error': str(e)[:200]})
        raise
    if reply_token:
        smart_reply(user_id, reply_token, reply_msg, configuration)

def async_bind_update_task(user_id, ver):
    """绑定后异步数据更新任务 - 在webtask_queue中执行"""
    try:
        messages = asyncio.run(maimai_update(user_id, ver))
        track_event('sync_task', user_id=user_id, metadata={'success': True, 'trigger': 'bind'})
    except Exception as e:
        logger.error(f"[Bind Update] ⚠ Failed to update: {e}")
        track_event('sync_task', user_id=user_id, metadata={'success': False, 'trigger': 'bind', 'error': str(e)[:200]})
        messages = rebind_msg(user_id)
    try:
        smart_push(user_id, messages, configuration)
    except Exception as e:
        logger.error(f"[Bind Update] ⚠ Failed to push: {e}")

def async_generate_friend_record_task(event):
    """异步生成好友成绩任务 - 在webtask_queue中执行"""
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    # 检查是否在群聊中发送
    source_type = getattr(event.source, 'type', 'user')
    if source_type != 'user':
        # 在群聊中，返回警告消息
        reply_message = TextMessage(text=get_multilingual_text(friend_rcd_group_warning_text, user_id))
        return smart_reply(user_id, reply_token, reply_message, configuration, addition=False)

    # 只拆分前两个空格，剩余内容作为 command
    parts = user_message.replace("friend-rcd ", "").strip().split(maxsplit=2)
    friend_code = parts[0] if len(parts) > 0 else ""
    record_type = parts[1] if len(parts) > 1 else "best50"
    command = parts[2] if len(parts) > 2 else ""

    # 转换 record_type 为标准格式
    for aliases, standard_type in RANK_COMMANDS.items():
        if record_type.lower() in aliases:
            record_type = standard_type
            break

    # 获取用户版本
    ver = "jp"
    if user_id in USERS and 'version' in USERS[user_id]:
        ver = USERS[user_id]['version']

    try:
        track_event('image_gen', user_id=user_id, metadata={'command': 'friend-rcd', 'source': 'line'})
    except Exception: pass

    # 直接通过网页爬取获取好友信息
    reply_msg = asyncio.run(generate_friend_record(user_id, friend_code, record_type, command, ver))

    smart_reply(user_id, reply_token, reply_msg, configuration)

def async_get_song_record_task(event):
    """异步歌曲成绩查询任务 - 在webtask_queue中执行"""
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    # 检查 @ mention（提取被提到的用户 ID）
    mentioned_user_id = extract_single_mention(event, user_id)

    # 初始化用户版本和目标用户
    if user_id in USERS:
        mai_ver = USERS[user_id].get("version", "jp")
        # 只有当 mentioned_user_id 存在且已注册时才使用
        id_use = mentioned_user_id if mentioned_user_id else user_id
        mai_ver_use = USERS[id_use].get("version", "jp") if id_use in USERS else mai_ver
    else:
        id_use = user_id
        mai_ver = "jp"
        mai_ver_use = "jp"

    # 提取歌曲名称（移除命令后缀）
    acronym = re.sub(r"\s*(のレコード|song-record|record)$", "", user_message).strip()

    try:
        track_event('image_gen', user_id=user_id, metadata={'command': 'song-record', 'source': 'line'})
    except Exception: pass

    # 调用实际的查询函数
    reply_msg = asyncio.run(get_song_record(user_id, id_use, acronym, mai_ver_use))

    smart_reply(user_id, reply_token, reply_msg, configuration)

def async_get_song_record_by_id_task(event):
    """异步歌曲成绩查询任务（通过ID）- 在webtask_queue中执行"""
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    # 验证命令格式
    parts = user_message.split()
    if len(parts) < 2:
        smart_reply(user_id, reply_token, song_error(user_id), configuration)
        return

    # 提取歌曲ID并验证长度
    song_id = parts[1].split("&", 1)[0]
    if len(song_id) != 6:
        smart_reply(user_id, reply_token, song_error(user_id), configuration)
        return

    # 获取用户版本
    ver = "jp"
    id_use = user_id

    if user_id in USERS:
        if 'version' in USERS[user_id]:
            ver = USERS[user_id]['version']

    # 提取id_use参数
    if "id_use=" in user_message:
        id_use = user_message.split("id_use=", 1)[1]

    try:
        track_event('image_gen', user_id=user_id, metadata={'command': 'song-record-id', 'source': 'line'})
    except Exception: pass

    # 调用实际的查询函数
    reply_msg = asyncio.run(get_song_record_by_id(user_id, id_use, song_id, ver))

    smart_reply(user_id, reply_token, reply_msg, configuration)

def _classify_image_command(msg):
    """根据消息内容识别图片生成命令类型"""
    msg_lower = msg.lower().strip()
    msg_clean = re.sub(r"\s*-(uc|up|c)\s*$", "", msg_lower)

    # B 系列命令：统一为规范名称
    first_word = re.split(r"[ \n]", msg_lower, 1)[0]
    b_cmd_map = {
        "b50": "b50", "best50": "b50",
        "b40": "b40", "best40": "b40",
        "b35": "b35", "best35": "b35",
        "b15": "b15", "best15": "b15",
        "ab35": "ab35", "allb35": "ab35",
        "ab50": "ab50", "allb50": "ab50",
        "apb50": "apb50", "ap50": "apb50",
        "fdxb50": "fdxb50", "fdx50": "fdxb50",
        "rct50": "rct50", "r50": "rct50",
        "idealb50": "idealb50", "idlb50": "idealb50",
        "unknown": "unknown", "unkn": "unknown",
    }
    if first_word in b_cmd_map:
        return b_cmd_map[first_word]

    # 后缀匹配
    suffix_map = [
        (("ってどんな曲", "info", "song-info"), "song-info"),
        (("の達成状況", "achievement"), "plate"),
        (("のレコード", "song-record", "record"), "song-record"),
        (("のバージョンリスト", "version-list"), "version-list"),
        (("の定数リスト", "のレベルリスト", "level-list"), "level-list"),
        (("のレコードリスト", "record-list", "records"), "record-list"),
    ]
    for suffixes, cmd_name in suffix_map:
        for suffix in suffixes:
            if msg_clean.endswith(suffix):
                return cmd_name

    # 进度命令
    if re.match(r"^(\d+\+?)\s*(sss\+|ss\+|s\+|ap\+|fc\+|fdx\+|sss|ss|ap|fc|fdx|s)\s*(progress|進捗|进度)", msg_lower):
        return "progress"

    # random
    if msg_lower.startswith("random"):
        return "random"

    return first_word[:32]


def async_generate_image_task(event):
    """异步图片生成任务 - 在image_queue中执行"""
    try:
        user_id = getattr(event.source, 'user_id', None)
        msg = (event.message.text or '').strip() if getattr(event, 'message', None) else ''
        cmd = _classify_image_command(msg)
        track_event('image_gen', user_id=user_id, metadata={'command': cmd, 'source': 'line'})
    except Exception as e:
        logger.debug(f"[EventTracker] image_gen track skipped: {e}")
    handle_sync_text_command(event)

def async_admin_maimai_update_task(event):
    """管理员触发的maimai更新任务 - 在webtask_queue中执行"""
    user_id = event.source.user_id

    ver = "jp"
    if user_id in USERS and 'version' in USERS[user_id]:
        ver = USERS[user_id]['version']

    try:
        asyncio.run(maimai_update(user_id, ver))
        track_event('sync_task', user_id=user_id, metadata={'success': True, 'trigger': 'admin'})
    except Exception as e:
        track_event('sync_task', user_id=user_id, metadata={'success': False, 'trigger': 'admin', 'error': str(e)[:200]})
        raise


# ==================== 主程序入口 ====================

async def maimai_update(user_id, ver="jp"):
    # 记录开始时间
    start_time = time.time()

    messages = []
    func_status = {
        "User Info": True,
        "Best Records": True,
        "Recent Records": True,
        "Favorite Friends": 0
    }

    if user_id not in USERS:
        return segaid_error(user_id)

    elif 'sega_id' not in USERS[user_id] or 'sega_pwd' not in USERS[user_id]:
        return segaid_error(user_id)

    sega_id = USERS[user_id].get('sega_id')
    sega_pwd = USERS[user_id].get('sega_pwd')
    aime = USERS[user_id].get('aime', 0)

    # 定义数据获取函数（在重试循环外定义一次）
    async def fetch_all_data(cookies):
        return await asyncio.gather(
            get_maimai_info(cookies, ver),
            get_maimai_records(cookies, ver),
            get_recent_records(cookies, ver),
            get_friends_list(cookies, ver)
        )

    user_info = maimai_records = recent_records = friends_list = None

    cookies = await login_to_maimai(sega_id, sega_pwd, ver=ver, aime=aime)
    if cookies is None:
        logger.warning(f"[User] ⚠ Login failed: user_id={user_id}")
        return segaid_error(user_id)
    if cookies == "MAINTENANCE":
        return maintenance_error(user_id)

    # 使用异步函数并发获取所有数据
    user_info, maimai_records, recent_records, friends_list = await fetch_all_data(cookies)

    if (user_info == "MAINTENANCE" or
        maimai_records == "MAINTENANCE" or
        recent_records == "MAINTENANCE" or
        friends_list == "MAINTENANCE"):
        return maintenance_error(user_id)

    if not user_info or not maimai_records or not recent_records:
        logger.warning(f"[User] ⚠ Data fetch incomplete: user_id={user_id}, user_info={bool(user_info)}, records={bool(maimai_records)}, recent={bool(recent_records)}")

    error = False

    if user_info and user_info['rating'] != "ERROR":
        edit_user_value(user_id, "personal_info", user_info)
    else:
        func_status["User Info"] = False
        error = True

    if maimai_records:
        write_record(user_id, maimai_records)
    else:
        func_status["Best Records"] = False
        error = True

    if recent_records:
        write_record(user_id, recent_records, recent=True)
    else:
        func_status["Recent Records"] = False
        error = True

    if not error:
        edit_user_value(user_id, "mai_friends", friends_list)
        func_status["Favorite Friends"] = len(friends_list)

    # 计算耗时
    elapsed_time = time.time() - start_time

    if not error:
        # 记录更新时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        edit_user_value(user_id, "last_update", current_time)

        # 获取用户信息
        user_data = USERS[user_id]
        username = user_data.get('personal_info', {}).get('name', 'N/A')
        rating = user_data.get('personal_info', {}).get('rating', 'N/A')

        # 使用 flex message 显示更新结果
        messages.append(generate_update_result_flex(
            user_id=user_id,
            username=username,
            rating=rating,
            update_time=current_time,
            elapsed_time=elapsed_time,
            func_status=func_status,
            success=True
        ))
    else:
        # 获取用户信息
        user_data = USERS[user_id]
        username = user_data.get('personal_info', {}).get('name', 'N/A')
        rating = user_data.get('personal_info', {}).get('rating', 'N/A')
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 使用 flex message 显示错误结果
        messages.append(generate_update_result_flex(
            user_id=user_id,
            username=username,
            rating=rating,
            update_time=current_time,
            elapsed_time=elapsed_time,
            func_status=func_status,
            success=False
        ))

    if func_status["Best Records"]:
        messages.append(await generate_records(user_id, user_id, ver=ver))

    return messages

def handle_rc_command(msg: str, user_id: str):
    """
    处理 RC 命令，验证输入并生成 Rating 对照表

    Args:
        msg: 用户输入的消息（如 "rc 13.2"）
        user_id: 用户ID

    Returns:
        FlexMessage 或 TextMessage（错误消息）
    """
    # 提取数字
    level_str = re.sub(r"^rc\b[ 　]*", "", msg, flags=re.IGNORECASE).strip()

    # 尝试转换为浮点数
    try:
        level = float(level_str)
    except ValueError:
        language = get_user_language(user_id)
        error_texts = {
            'ja': '無効な定数です。1.0～15.0の範囲で入力してください。',
            'en': 'Invalid constant. Please enter a value between 1.0 and 15.0.',
            'zh': '无效的定数。请输入 1.0~15.0 范围内的数值。'
        }
        return TextMessage(text=error_texts.get(language, error_texts['ja']))

    # 验证范围：1.0 到 15.0
    if level < 1.0 or level > 15.0:
        language = get_user_language(user_id)
        error_texts = {
            'ja': f'定数 {level} は範囲外です。1.0～15.0の範囲で入力してください。',
            'en': f'Constant {level} is out of range. Please enter a value between 1.0 and 15.0.',
            'zh': f'定数 {level} 超出范围。请输入 1.0~15.0 范围内的数值。'
        }
        return TextMessage(text=error_texts.get(language, error_texts['ja']))

    # 验证小数位数：最多一位
    if round(level, 1) != level:
        language = get_user_language(user_id)
        error_texts = {
            'ja': f'定数 {level} は無効です。小数点以下は1桁まで入力可能です（例：13.2）。',
            'en': f'Constant {level} is invalid. Only one decimal place is allowed (e.g., 13.2).',
            'zh': f'定数 {level} 无效。仅支持一位小数（例如：13.2）。'
        }
        return TextMessage(text=error_texts.get(language, error_texts['ja']))

    return get_rc(level, user_id)


def get_rc(level: float, user_id=None):
    """
    生成指定难度的Rating对照表 FlexMessage

    Args:
        level: 谱面定数 (如 14.5)
        user_id: 用户ID（用于多语言）

    Returns:
        FlexMessage: Rating对照表
    """
    rc_data = []
    last_ra = 0

    for i in range(970000, 1005001):
        score = i / 10000
        ra = get_single_ra(level, score)
        if ra != last_ra:
            rc_data.append((score, ra))
            last_ra = ra

    return generate_rc_flex(level, rc_data, user_id)

async def random_song(user_id, key="", ver="jp"):
    songs, _ = read_dxdata(ver)
    length = len(songs)
    is_exit = False
    valid_songs = []
    result = []

    if key:
        level_values = parse_level_value(key)
        if not level_values:
            return song_error(user_id)

    for song in songs:
        for sheet in song['sheets']:
            if sheet['regions'][ver]:
                if not key or sheet['internalLevelValue'] in level_values:
                    valid_songs.append(song)
                    break

    if not valid_songs:
        return song_error(user_id)

    song = random.choice(valid_songs)
    song_id = song.get('id')

    user_tz = get_user_timezone(user_id)
    song_img = song_info_generate(song, timezone_offset=user_tz, ver=ver, bg_filter=_get_user_bg_filter(user_id))
    img_w, img_h = song_img.size
    original_url, preview_url = await smart_upload(song_img, user_id)
    return generate_song_info_flex(song_id, original_url, img_w, img_h, user_id, mode='info')

async def search_song(user_id, acronym, ver="jp"):
    """
    搜索歌曲并返回歌曲信息图片

    Args:
        user_id: 用户ID
        acronym: 搜索关键词
        ver: 服务器版本 (jp/intl)

    Returns:
        搜索结果消息列表 或搜索结果flex message 或错误消息
    """
    songs, _ = read_dxdata(ver)

    # 使用优化的歌曲匹配函数
    matching_songs = find_matching_songs(acronym, songs, max_results=MAX_SEARCH_RESULTS, )

    # 没有匹配结果
    if not matching_songs:
        return song_error(user_id)

    # 返回搜索结果列表
    if len(matching_songs) > 1:
        return generate_search_results_flex(user_id, matching_songs, 'song')
    
    # 单个结果，调用 search_song_by_id
    song = matching_songs[0]
    song_id = song.get('id')
    return await search_song_by_id(user_id, song_id, ver)


async def search_song_by_id(user_id, song_id, ver="jp"):
    """
    通过歌曲ID搜索歌曲并返回歌曲信息图片

    Args:
        user_id: 用户ID
        song_id: 歌曲唯一ID (6个字符)
        ver: 服务器版本 (jp/intl)

    Returns:
        歌曲信息图片消息 或错误消息
    """
    songs, _ = read_dxdata(ver)

    matching_song = None
    for song in songs:
        if song.get('id') == song_id:
            matching_song = song
            break

    # 没有匹配结果
    if not matching_song:
        return song_error(user_id)

    user_tz = get_user_timezone(user_id)
    song_img = song_info_generate(matching_song, timezone_offset=user_tz, ver=ver, bg_filter=_get_user_bg_filter(user_id))
    img_w, img_h = song_img.size
    original_url, preview_url = await smart_upload(song_img, user_id)
    return generate_song_info_flex(song_id, original_url, img_w, img_h, user_id, mode='info')

def get_ranking(user_id, id_use, ver=None):
    """
    生成 Rating 排行榜（按版本 jp/intl 分开）

    Args:
        user_id: 当前用户ID
        id_use: 使用的用户ID
        ver: 指定版本 "jp"/"intl"，None 则使用用户自身版本

    Returns:
        FlexMessage: 排行榜
    """
    user_ver = ver or USERS.get(id_use, {}).get('version', 'jp')

    # 收集同版本且有 rating 的用户
    ranked_users = []
    for uid, data in USERS.items():
        if data.get('version', 'jp') != user_ver:
            continue
        info = data.get('personal_info')
        if info and info.get('rating') and info['rating'] != 'ERROR':
            try:
                rating_val = int(info['rating'])
            except (ValueError, TypeError):
                continue
            ranked_users.append({
                "user_id": uid,
                "name": info.get('name', 'N/A'),
                "rating_int": rating_val,
                "rating": info['rating']
            })

    if not ranked_users:
        return TextMessage(text=get_multilingual_text(ranking_no_data_text, user_id))

    # 按 rating 降序排序
    ranked_users.sort(key=lambda x: x["rating_int"], reverse=True)

    # 分配排名（相同 rating 同排名）
    for i, u in enumerate(ranked_users):
        if i == 0:
            u["rank"] = 1
        elif u["rating_int"] == ranked_users[i - 1]["rating_int"]:
            u["rank"] = ranked_users[i - 1]["rank"]
        else:
            u["rank"] = i + 1

    # 指定版本时直接显示前15名，不做个人区域
    if ver is not None:
        top15 = []
        for u in ranked_users[:15]:
            top15.append({"rank": u["rank"], "name": u["name"], "rating": u["rating"]})
        return generate_ranking_flex(user_id, top15, nearby_entries=None, ver=user_ver)

    # 找到当前用户在排名列表中的索引
    user_idx = None
    for i, u in enumerate(ranked_users):
        if u["user_id"] == id_use:
            user_idx = i
            break

    # 前5名
    top5 = []
    for u in ranked_users[:5]:
        entry = {"rank": u["rank"], "name": u["name"], "rating": u["rating"]}
        if u["user_id"] == id_use:
            entry["is_user"] = True
        top5.append(entry)

    # 用户在前5名内，不需要附近区域
    user_in_top5 = user_idx is not None and user_idx < 5

    # 用户不在前5时，构建以用户为中心的附近名单（前后各3名）
    nearby_entries = None
    if not user_in_top5 and user_idx is not None:
        # 避免与前5名重叠，附近区域从索引5开始
        nearby_start = max(5, user_idx - 3)
        nearby_end = min(len(ranked_users), user_idx + 4)
        nearby_entries = []
        for u in ranked_users[nearby_start:nearby_end]:
            entry = {"rank": u["rank"], "name": u["name"], "rating": u["rating"]}
            if u["user_id"] == id_use:
                entry["is_user"] = True
            nearby_entries.append(entry)

    return generate_ranking_flex(user_id, top5, nearby_entries=nearby_entries, ver=user_ver)


def search_by_artist(user_id, artist_query, ver="jp", page=1, source_type="user"):
    """
    通过艺术家名搜索歌曲

    Args:
        user_id: 用户ID
        artist_query: 艺术家名关键词
        ver: 服务器版本 (jp/intl)
        page: 页码
        source_type: 来源类型 (user/group/room)

    Returns:
        FlexMessage 歌曲列表 或错误消息
    """
    if source_type != 'user':
        return TextMessage(text=get_multilingual_text(search_group_warning_text, user_id))

    songs, _ = read_dxdata(ver)

    matching_songs = []
    query_lower = artist_query.lower()
    for song in songs:
        artist = song.get('artist') or ''
        if query_lower in artist.lower():
            matching_songs.append(song)

    if not matching_songs:
        return song_error(user_id)

    title = f"Artist: {artist_query}"
    return generate_song_list_flex(user_id, title, matching_songs, page, "artist", artist_query)

def search_by_designer(user_id, designer_query, ver="jp", page=1, source_type="user"):
    """
    通过谱面设计师搜索歌曲

    Args:
        user_id: 用户ID
        designer_query: 谱面设计师名关键词
        ver: 服务器版本 (jp/intl)
        page: 页码
        source_type: 来源类型 (user/group/room)

    Returns:
        FlexMessage 歌曲列表 或错误消息
    """
    if source_type != 'user':
        return TextMessage(text=get_multilingual_text(search_group_warning_text, user_id))

    songs, _ = read_dxdata(ver)

    matching_songs = []
    matched_sheets_map = {}
    query_lower = designer_query.lower()

    for song in songs:
        matched_sheets = []
        for sheet in song.get('sheets', []):
            designer = sheet.get('noteDesigner', '')
            if designer and query_lower in designer.lower():
                matched_sheets.append(sheet)
        if matched_sheets:
            matching_songs.append(song)
            matched_sheets_map[song.get('id', '')] = matched_sheets

    if not matching_songs:
        return song_error(user_id)

    title = f"Designer: {designer_query}"
    return generate_song_list_flex(user_id, title, matching_songs, page, "designer", designer_query, matched_sheets_map)

def calc_by_id(user_id, song_id, ver="jp"):
    """
    通过歌曲ID搜索歌曲并返回歌曲calc结果

    Args:
        user_id: 用户ID
        song_id: 歌曲唯一ID (6个字符)
        ver: 服务器版本 (jp/intl)

    Returns:
        歌曲信息图片消息和calc结果列表 或错误消息
    """
    songs, _ = read_dxdata(ver)

    matching_song = None
    for song in songs:
        if song.get('id') == song_id:
            matching_song = song
            break

    # 没有匹配结果
    if not matching_song:
        return song_error(user_id)

    # 收集calc数据
    calc_data = []
    for sheet in matching_song.get('sheets', []):
        difficulty = sheet.get('difficulty', 'unknown')

        # 只处理master和remaster难度
        if difficulty not in ['master', 'remaster']:
            continue

        notes_counts = sheet.get('noteCounts', {})
        level = sheet.get('internalLevelValue', 0)
        notes = {
            'tap': notes_counts.get('tap', 0),
            'hold': notes_counts.get('hold', 0),
            'slide': notes_counts.get('slide', 0),
            'touch': notes_counts.get('touch', 0),
            'break': notes_counts.get('break', 0)
        }

        # 计算分数
        scores = get_note_score(notes)
        calc_data.append((notes, scores, difficulty, level))

    calc_carousel = generate_calc_carousel(calc_data)
    return calc_carousel

def get_user_info(user_id, source_type):
    if source_type != 'user':
        # 在群聊中，返回警告消息
        return TextMessage(text=get_multilingual_text(private_info_group_warning_text, user_id))

    return generate_user_info_flex(user_id)

def get_friend_list(user_id, source_type):
    if user_id not in USERS:
        return segaid_error(user_id)

    elif 'mai_friends' not in USERS[user_id]:
        return friend_error(user_id)

    if source_type != 'user':
        # 在群聊中，返回警告消息
        return TextMessage(text=get_multilingual_text(friend_rcd_group_warning_text, user_id))

    friend_list = copy.deepcopy(USERS[user_id].get("mai_friends"))
    if not friend_list:
        friend_list = []

    friend_num = len(friend_list)
    
    if friend_num <= 10:
        group_size = 10
    elif 14 < friend_num <= 16:
        group_size = 8
    elif 17 <= friend_num <= 18:
        group_size = 9
    else:
        group_size = 7

    return generate_friend_buttons(user_id, get_friend_list_alt_text(user_id), friend_list, group_size)

def get_bot_status(user_id):
    """
    获取 Bot 状态信息

    Args:
        user_id: 用户ID（用于多语言）

    Returns:
        FlexMessage: Bot 状态信息
    """
    # 计算运行时长
    uptime = datetime.now() - SERVICE_START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m"

    # 获取系统信息
    cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)

    memory = psutil.virtual_memory()
    memory_percent = round(memory.percent, 1)
    total_memory = round(memory.total / (1024**3), 1)  # GB
    memory_used_gb = round(memory.used / (1024**3), 1)  # GB

    # 线程安全地读取统计数据
    with stats_lock:
        total_tasks = STATS['tasks_processed']
        total_time = STATS['response_time']

    # 计算平均响应时间
    if total_tasks > 0:
        avg_response = f"{round(total_time / total_tasks, 1)} ms"
    else:
        avg_response = "N/A"

    return generate_bot_status_flex(
        uptime_str=uptime_str,
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        memory_used_gb=memory_used_gb,
        total_memory=total_memory,
        avg_response_time=avg_response,
        user_id=user_id
    )

async def get_song_record(user_id, id_use, acronym, ver="jp"):
    """
    查询用户在特定歌曲上的游玩记录

    Args:
        user_id: 用户ID
        id_use: 使用的ID
        acronym: 歌曲搜索关键词
        ver: 服务器版本 (jp/intl)

    Returns:
        包含用户成绩的歌曲信息图片消息列表 或搜索结果flex message 或错误消息
    """
    if id_use not in USERS:
        return mention_error(user_id) if id_use != user_id else segaid_error(user_id)

    if "personal_info" not in USERS[id_use]:
        return mention_error(user_id) if id_use != user_id else info_error(user_id)
    
    song_record = read_record(id_use)

    if not len(song_record):
        return record_error(user_id)
        
    # 使用优化的歌曲匹配函数
    songs, _ = read_dxdata(ver)
    matching_songs = find_matching_songs(acronym, songs, max_results=MAX_SEARCH_RESULTS, )

    if not matching_songs:
        return song_error(user_id)

    # 过滤出有游玩记录的歌曲
    songs_with_records = []
    for song in matching_songs:
        has_record = False
        for rcd in song_record:
            if rcd['cover_name'] == song['cover_name'] and rcd['type'] == song['type']:
                has_record = True
                break
        if has_record:
            songs_with_records.append(song)

    # 没有找到任何有记录的歌曲
    if len(songs_with_records) == 0:
        return song_error(user_id)

    # 返回搜索结果列表
    if len(songs_with_records) > 1:
        return generate_search_results_flex(user_id, matching_songs, 'record', id_use)

    # 单个结果，调用 get_song_record_by_id
    song = songs_with_records[0]
    song_id = song.get('id')
    return await get_song_record_by_id(user_id, id_use, song_id, ver)

async def get_song_record_by_id(user_id, id_use, song_id, ver="jp"):
    """
    通过歌曲ID查询用户在特定歌曲上的游玩记录

    Args:
        user_id: 用户ID
        id_use: 使用的ID
        song_id: 歌曲唯一ID (6个字符)
        ver: 服务器版本 (jp/intl)

    Returns:
        包含用户成绩的歌曲信息图片消息 或错误消息
    """
    if id_use not in USERS:
        return mention_error(user_id) if id_use != user_id else segaid_error(user_id)

    if "personal_info" not in USERS[id_use]:
        return mention_error(user_id) if id_use != user_id else info_error(user_id)

    song_record = read_record(id_use)

    if not len(song_record):
        return record_error(user_id)

    matching_song = None
    songs, _ = read_dxdata(ver)
    for song in songs:
        if song.get('id') == song_id:
            matching_song = song
            break

    # 没有匹配结果
    if not matching_song:
        return song_error(user_id)

    # 查找用户的游玩记录
    played_data = []
    for rcd in song_record:
        if rcd['cover_name'] == matching_song['cover_name'] and rcd['type'] == matching_song['type']:
            played_data.append(rcd)
            song_name = rcd['name']

    # 如果该歌曲没有游玩记录
    if not played_data:
        return song_error(user_id)

    # 尝试使用新函数获取更详细的成绩（包含游玩次数和最后游玩时间）
    try:
        if 'sega_id' in USERS[id_use] and 'sega_pwd' in USERS[id_use] and user_id == id_use:
            sega_id = USERS[id_use]['sega_id']
            sega_pwd = USERS[id_use]['sega_pwd']
            aime = USERS[id_use].get('aime', 0)
            cookies = await login_to_maimai(sega_id, sega_pwd, ver=ver, aime=aime)
            if cookies is None:
                logger.warning(f"[Song Record] ⚠ Login failed: user_id={user_id}")

            if cookies:
                detailed_records = await get_single_record(song_name, matching_song['type'], cookies, ver=ver)

                if detailed_records and detailed_records != "MAINTENANCE":
                    # 用详细成绩更新 played_data
                    for rcd in played_data:
                        # 找到对应难度的详细成绩
                        for detail in detailed_records:
                            if detail['difficulty'] == rcd['difficulty']:
                                # 更新现有字段
                                rcd['score'] = detail['score']
                                rcd['dx_score'] = detail['dx_score']
                                rcd['score_icon'] = detail['score_icon']
                                rcd['combo_icon'] = detail['combo_icon']
                                rcd['sync_icon'] = detail['sync_icon']
                                # 添加新字段
                                rcd['play_count'] = detail['play_count']
                                rcd['last_play_time'] = detail['last_play_time']
                                rcd = get_detailed_info([rcd], ver)[0]
                                break
    except Exception as e:
        # 如果获取详细成绩失败，继续使用原成绩
        logger.exception(f"[Song Record] Failed to get detailed record for {matching_song.get('title', 'unknown')}: {e}")

    # 生成歌曲信息图片
    user_tz = get_user_timezone(user_id)
    song_img = song_info_generate(matching_song, played_data, timezone_offset=user_tz, ver=ver, bg_filter=_get_user_bg_filter(user_id))
    img_w, img_h = song_img.size
    original_url, preview_url = await smart_upload(song_img, user_id)
    return generate_song_info_flex(song_id, original_url, img_w, img_h, user_id, mode='record')

async def generate_plate_rcd(user_id, id_use, title, ver="jp", filter_mode=None):
    if id_use not in USERS:
        return mention_error(user_id) if id_use != user_id else segaid_error(user_id)

    if "personal_info" not in USERS[id_use]:
        return mention_error(user_id) if id_use != user_id else info_error(user_id)

    if not (len(title) == 2 or len(title) == 3):
        return plate_error(user_id)

    song_record = read_record(id_use)

    if not len(song_record):
        return record_error(user_id)

    title = title.replace("晓", "暁").replace("极", "極")

    version_name = title[0]
    plate_type = title[1:]

    songs, versions = read_dxdata(ver)

    target_version = []
    target_icon = []
    target_type = ""

    if version_name in TEMP_VERSION["abbr"]:
        target_version.append(TEMP_VERSION["title"])

    for version in versions:
        if version_name in version['abbr']:
            target_version.append(version['version'])

    if not len(target_version):
        return version_error(user_id)

    if plate_type == "極":
        target_type = "combo"
        target_icon = ["fc", "fcp", "ap", "app"]

    elif plate_type == "将":
        target_type = "score"
        target_icon = ["sss", "sssp"]

    elif plate_type == "神":
        target_type = "combo"
        target_icon = ["ap", "app"]

    elif plate_type == "舞舞":
        target_type = "sync"
        target_icon = ["fdx", "fdxp"]

    else:
        return plate_error(user_id)

    version_rcd_data = list(filter(lambda x: x['version'] in target_version, song_record))
    if not version_rcd_data:
        return version_error(user_id)

    target_data = []
    target_num = {
        'basic': {'all': 0, 'clear': 0},
        'advanced': {'all': 0, 'clear': 0},
        'expert': {'all': 0, 'clear': 0},
        'master': {'all': 0, 'clear': 0}
    }

    # 优化：构建用户记录的哈希表，避免嵌套循环 O(n*m*p) -> O(n*m)

    rcd_map = {}
    for rcd in version_rcd_data:
        name = rcd['name']
        difficulty = rcd['difficulty']
        type = rcd['type']

        # 策略1: 精确匹配
        key1 = (name, difficulty, type)
        rcd_map[key1] = rcd

        # 策略2: 标准化匹配 (处理全角半角、特殊符号等)
        normalized_name = normalize_text(name)
        key2 = (normalized_name, difficulty, type)
        rcd_map[key2] = rcd

    for song in songs:
        if song['version'] not in target_version or song['type'] == 'utage':
            continue

        for sheet in song['sheets']:
            if not sheet['regions'][ver] or sheet["difficulty"] not in target_num:
                continue

            icon = "back"
            achieved = False
            achievement_rate = 0.0
            target_num[sheet['difficulty']]['all'] += 1

            # O(1) 哈希查找，尝试多种匹配策略
            song_title = song['title']
            difficulty = sheet['difficulty']
            song_type = song['type']

            # 尝试精确匹配
            key1 = (song_title, difficulty, song_type)
            if key1 in rcd_map:
                rcd = rcd_map[key1]
                icon = rcd[f'{target_type}_icon']
                # 获取达成率
                score_str = rcd.get('score', '0.0000%')
                achievement_rate = float(score_str[:-1]) if score_str.endswith('%') else 0.0
                if icon in target_icon:
                    target_num[difficulty]['clear'] += 1
                    achieved = True
            else:
                # 尝试标准化匹配
                normalized_title = normalize_text(song_title)
                key2 = (normalized_title, difficulty, song_type)
                if key2 in rcd_map:
                    rcd = rcd_map[key2]
                    icon = rcd[f'{target_type}_icon']
                    # 获取达成率
                    score_str = rcd.get('score', '0.0000%')
                    achievement_rate = float(score_str[:-1]) if score_str.endswith('%') else 0.0
                    if icon in target_icon:
                        target_num[difficulty]['clear'] += 1
                        achieved = True

            if sheet['difficulty'] == "master":
                # 构建 complete_info：检查所有难度是否符合牌子条件
                complete_info = {}
                for diff in ["basic", "advanced", "expert", "master"]:
                    # 尝试查找该难度的记录
                    key_check = (song_title, diff, song_type)
                    key_check_normalized = (normalize_text(song_title), diff, song_type)

                    meets_condition = False
                    if key_check in rcd_map:
                        rcd = rcd_map[key_check]
                        diff_icon = rcd[f'{target_type}_icon']
                        meets_condition = diff_icon in target_icon
                    elif key_check_normalized in rcd_map:
                        rcd = rcd_map[key_check_normalized]
                        diff_icon = rcd[f'{target_type}_icon']
                        meets_condition = diff_icon in target_icon

                    complete_info[diff] = meets_condition

                target_data.append({
                    "img": generate_cover(song['cover_url'], song_type, icon, target_type, cover_name=song.get('cover_name'), complete_info=complete_info, achieved=achieved),
                    "level": sheet['level'],
                    "achieved": achieved,
                    "achievement_rate": achievement_rate
                })

    # 按 filter_mode 过滤数据
    if filter_mode == "uncleared":
        target_data = [d for d in target_data if not d["achieved"]]
    elif filter_mode == "unplayed":
        target_data = [d for d in target_data if d["achievement_rate"] == 0.0 and not d["achieved"]]
    elif filter_mode == "cleared":
        target_data = [d for d in target_data if d["achieved"]]

    if not target_data:
        return record_error(user_id)

    plate_img = generate_plate_image(target_data, title, headers = target_num)

    # 清理 target_data 中的封面图片对象
    for entry in target_data:
        entry.pop("img", None)
    del target_data

    # 获取用户信息并创建用户信息图片
    user_info = USERS[id_use].get('personal_info')
    profile_img = generate_profile(user_info, user_id=id_use)
    user_tz = get_user_timezone(user_id)
    img = compose_images([profile_img, plate_img], spacing=0, border_width=0, timezone_offset=user_tz, bg_filter=_get_user_bg_filter(user_id))

    # 清理中间图片对象
    del profile_img, plate_img
    gc.collect(0)

    original_url, preview_url = await smart_upload(img, user_id)

    # 清理最终图片对象
    del img
    gc.collect(0)

    # 检查上传是否成功
    if not original_url or not preview_url:
        logger.error(f"[Image] ✗ Upload failed")
        return system_error(user_id)

    message = ImageMessage(original_content_url=original_url, preview_image_url=preview_url)

    return message


async def generate_level_rank_progress(user_id, id_use, level, rank=None, ver="jp", filter_mode=None):
    """
    生成指定难度和评级的达成情况图片（定数列表+统计卡片）

    参数:
        user_id: 请求用户ID
        id_use: 目标用户ID
        level: 难度等级（如 "13", "13+", "14", "14+", "15"）
        rank: 评级（如 "s", "s+", "ss", "ss+", "sss", "sss+", "ap", "ap+", "fdx", "fdx+"），可选
        ver: 服务器版本（"jp" 或 "intl"）
        filter_mode: 过滤模式（"uncleared"=只显示未完成, "unplayed"=只显示未游玩, "cleared"=只显示已完成）
    """

    if id_use not in USERS:
        return mention_error(user_id) if id_use != user_id else segaid_error(user_id)

    if "personal_info" not in USERS[id_use]:
        return mention_error(user_id) if id_use != user_id else info_error(user_id)

    # 检查等级是否支持
    supported_levels = ["11", "11+", "12", "12+", "13", "13+", "14", "14+", "15"]
    if level not in supported_levels:
        return level_not_supported(user_id)

    # 评级映射：用户输入 -> 内部标识
    rank_mapping = {
        "s": ("score", ["s", "sp", "ss", "ssp", "sss", "sssp"]),
        "s+": ("score", ["sp", "ss", "ssp", "sss", "sssp"]),
        "ss": ("score", ["ss", "ssp", "sss", "sssp"]),
        "ss+": ("score", ["ssp", "sss", "sssp"]),
        "sss": ("score", ["sss", "sssp"]),
        "sss+": ("score", ["sssp"]),
        "fc": ("combo", ["fc", "fcp", "ap", "app"]),
        "fc+": ("combo", ["fcp", "ap", "app"]),
        "ap": ("combo", ["ap", "app"]),
        "ap+": ("combo", ["app"]),
        "fdx": ("sync", ["fdx", "fdxp"]),
        "fdx+": ("sync", ["fdxp"])
    }

    if rank is not None and rank not in rank_mapping:
        return song_error(user_id)

    target_type, target_icons = rank_mapping[rank] if rank else (None, None)
    song_record = read_record(id_use)

    if not len(song_record):
        return record_error(user_id)

    region_key = ver

    # 构建用户记录的哈希表
    rcd_map = {}
    for rcd in song_record:
        name = rcd['name']
        difficulty = rcd['difficulty']
        type = rcd['type']

        # 精确匹配
        key1 = (name, difficulty, type)
        rcd_map[key1] = rcd

    # 收集数据并统计
    target_data = []
    total_charts = 0  # 总谱面数
    achieved_count = 0  # 已达成
    unachieved_count = 0  # 未达成（有记录但未达标）
    unplayed_count = 0  # 未游玩
    
    songs, _ = read_dxdata(ver)
    for song in songs:
        if song['type'] == 'utage':
            continue

        for sheet in song['sheets']:
            if not sheet['regions'].get(region_key, False):
                continue

            # 只处理指定等级的谱面
            # 14+ 包含 14+ 和 15 级别
            if level == "14+":
                if sheet['level'] not in ["14+", "15"]:
                    continue
            else:
                if sheet['level'] != level:
                    continue

            difficulty = sheet['difficulty']
            total_charts += 1

            # 查找用户记录
            song_title = song['title']
            song_type = song['type']
            icon = "back"
            achieved = False
            has_record = False
            achievement_rate = 0.0  # 达成率

            # 尝试精确匹配
            key1 = (song_title, difficulty, song_type)
            if key1 in rcd_map:
                rcd = rcd_map[key1]
                has_record = True
                # 获取达成率
                score_str = rcd.get('score', '0.0000%')
                achievement_rate = float(score_str[:-1]) if score_str.endswith('%') else 0.0

                if rank is not None:
                    # 如果指定了评级，检查是否达成
                    user_icon = rcd.get(f'{target_type}_icon', "back")
                    icon = user_icon  # 始终显示用户实际达到的评级
                    if user_icon in target_icons:
                        achieved = True
                        achieved_count += 1
                    else:
                        unachieved_count += 1
                else:
                    # 如果没有指定评级，所有有记录的都算已达成
                    achieved = True
                    achieved_count += 1
            else:
                # 尝试标准化匹配
                normalized_title = normalize_text(song_title)
                key2 = (normalized_title, difficulty, song_type)
                if key2 in rcd_map:
                    rcd = rcd_map[key2]
                    has_record = True
                    # 获取达成率
                    score_str = rcd.get('score', '0.0000%')
                    achievement_rate = float(score_str[:-1]) if score_str.endswith('%') else 0.0

                    if rank is not None:
                        # 如果指定了评级，检查是否达成
                        user_icon = rcd.get(f'{target_type}_icon', "back")
                        icon = user_icon  # 始终显示用户实际达到的评级
                        if user_icon in target_icons:
                            achieved = True
                            achieved_count += 1
                        else:
                            unachieved_count += 1
                    else:
                        # 如果没有指定评级，所有有记录的都算已达成
                        achieved = True
                        achieved_count += 1

            # 如果没有记录，算作未游玩
            if not has_record:
                unplayed_count += 1

            # 生成所有难度的封面
            target_data.append({
                "img": generate_cover(song['cover_url'], song_type, icon if rank else None, target_type if rank else None, cover_name=song.get('cover_name'), difficulty=difficulty, achieved=achieved if rank else None, song_title=song_title),
                "internal_level": sheet['internalLevelValue'],
                "achieved": achieved,
                "difficulty": difficulty,
                "achievement_rate": achievement_rate
            })

    if not target_data:
        return record_error(user_id)

    # 按 filter_mode 过滤数据
    if filter_mode == "uncleared":
        target_data = [d for d in target_data if not d["achieved"]]
    elif filter_mode == "unplayed":
        target_data = [d for d in target_data if d["achievement_rate"] == 0.0 and not d["achieved"]]
    elif filter_mode == "cleared":
        target_data = [d for d in target_data if d["achieved"]]

    if not target_data:
        return record_error(user_id)

    # 生成标题
    level_display = level.replace("+", "⁺")
    rank_display = rank.upper().replace("+", "⁺") if rank else ""

    # 总体统计数据
    stats = {
        "achieved": achieved_count,
        "unachieved": unachieved_count,
        "unplayed": unplayed_count,
        "total": total_charts
    }

    # 生成图片（定数列表+统计卡片）
    record_img = generate_level_rank_progress_image(
        target_data,
        level_display,
        rank_display,
        stats
    )

    # 清理 target_data 中的封面图片对象
    for entry in target_data:
        entry.pop("img", None)
    del target_data

    # 获取用户信息并创建用户信息图片
    user_info = USERS[id_use].get('personal_info')
    profile_img = generate_profile(user_info, scale=1.5, user_id=id_use)
    user_tz = get_user_timezone(user_id)
    img = compose_images([profile_img, record_img], spacing=0, border_width=0, timezone_offset=user_tz, bg_filter=_get_user_bg_filter(user_id))

    del profile_img, record_img
    gc.collect(0)

    original_url, preview_url = await smart_upload(img, user_id)
    message = ImageMessage(original_content_url=original_url, preview_image_url=preview_url)

    del img
    gc.collect(0)

    return message


def generate_profile(user_info, scale=1, user_id=None):
    """
    创建用户信息图片

    Args:
        user_info: 用户个人信息字典（包含 name, rating, icon_url 等）
        scale: 图片缩放比例
        user_id: LINE用户ID（可选，用于获取LINE头像作为默认图标）

    Returns:
        PIL.Image: 用户信息图片
    """

    img_width = 1363
    img_height = 218
    info_img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(info_img)

    def paste_image(key, position, size, round=False):
        nonlocal user_info
        if key in user_info and user_info[key]:
            try:
                url = user_info[key]

                # 默认不带 headers
                headers = None

                if url.startswith("https://maimaidx-eng.com"):
                    headers = {
                        "Referer": "https://lng-tgk-aime-gw.am-all.net/common_auth/login?site_id=maimaidxex&redirect_url=https://maimaidx-eng.com/maimai-mobile/&back_url=https://maimai.sega.com/",
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/127.0.0.0 Safari/537.36"
                        ),
                        "Host": "maimaidx-eng.com",
                    }

                with requests.get(url, headers=headers, verify=False) as response:
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content))
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                img_resized = img.resize(size, Image.LANCZOS)
                if round:
                    img_resized = round_corner(img_resized, radius=10)
                info_img.paste(img_resized, position, img_resized)
                return True

            except Exception as e:
                logger.error(f"[Image] ✗ Failed to load image: url={user_info[key]}, error={e}")
                return None
        return None

    paste_image("nameplate_url", (0, 0), (1363, 218))

    # icon_url 为默认值时，尝试使用 LINE 头像
    default_icon = [
        "https://maimaidx.jp/maimai-mobile/img/Icon/",
        "https://maimaidx.jp/maimai-mobile/img/Icon/c22d52b387e3f829.png",
        "https://maimaidx-eng.com/maimai-mobile/img/Icon/",
        "https://maimaidx-eng.com/maimai-mobile/img/Icon/c22d52b387e3f829.png"
    ]
    icon_url = user_info.get("icon_url", "")
    round = False
    if icon_url in default_icon and user_id:
        try:
            with ApiClient(configuration) as api_client:
                profile = MessagingApi(api_client).get_profile(user_id)
                if profile.picture_url:
                    user_info = {**user_info, "icon_url": profile.picture_url}
                    round = True
        except Exception as e:
            logger.error(f"[Image] ✗ Failed to load user profile image: {e}")

    paste_image("icon_url", (26, 24), (170, 170), round)

    # rating block: 优先使用本地图片，兼容旧版 URL
    if "rating_block_path" in user_info and user_info["rating_block_path"]:
        try:
            with Image.open(user_info["rating_block_path"]) as _rb:
                rb_img = _rb.convert("RGBA")
            rb_img = rb_img.resize((296, 58), Image.LANCZOS)
            info_img.paste(rb_img, (219, 24), rb_img)
        except Exception as e:
            logger.error(f"[Image] ✗ Failed to load rating block: {e}")
    else:
        paste_image("rating_block_url", (219, 24), (223, 58))

    # 使用等宽方式绘制 rating 数字
    rating_text = user_info['rating'].rjust(5)
    char_width = 23  # 每个字符的固定宽度
    start_x = 359
    for i, char in enumerate(rating_text):
        # 计算字符的实际宽度
        char_bbox = draw.textbbox((0, 0), char, font=font_profile)
        actual_char_width = char_bbox[2] - char_bbox[0]
        # 在固定宽度区域内居中
        offset = (char_width - actual_char_width) / 2
        draw.text((start_x + i * char_width + offset, 28), char, fill=(255, 255, 255), font=font_profile)

    # 绘制昵称
    draw.rounded_rectangle([219, 89, 671, 145], radius=10, fill=(255, 255, 255), outline=(180, 180, 180), width=2)
    draw.text((235, 94), user_info['name'], fill=(0, 0, 0), font=font_profile)

    paste_image("class_rank_url", (530, 6), (148, 85))
    paste_image("cource_rank_url", (550, 93), (117, 48))
    paste_image("trophy_url", (219, 158), (452, 36))

    trophy_content = truncate_text(draw, user_info['trophy_content'], font_trophy, 430)
    bbox = draw.textbbox((0, 0), trophy_content, font=font_trophy)
    text_width = bbox[2] - bbox[0]
    rect_width = 452
    center_x = 219 + (rect_width - text_width) // 2
    draw.text((center_x, 157), trophy_content, fill=(255, 255, 255), font=font_trophy, stroke_width=2, stroke_fill=(0, 0, 0))

    info_img = info_img.resize((int(img_width * scale), int(img_height * scale)), Image.Resampling.LANCZOS)
    return info_img

def select_records(song_record, type="best50", command="", ver="jp"):
    page = 1
    times = 1
    sort_rule = lambda x: (x["ra"], float(x["score"][:-1]))
    filter_rules = [
        (lambda x: x['new_song'] == False),
        (lambda x: x['new_song'] == True)
    ]
    details = {}
    if not command == "":
        cmds = re.findall(r"-(\w+)(?:\s+([^-]+))?", command)
        for cmd, cmd_num in cmds:
            if cmd in ["diff", "difficulty"]:
                diff_map = {
                    'bas': 'basic',
                    'adv': 'advanced',
                    'exp': 'expert',
                    'mas': 'master',
                    'rem': 'remaster'
                }
                raw_diffs = cmd_num.split()
                difficulties = []
                for d in raw_diffs:
                    d_lower = d.strip().lower()
                    if d_lower:
                        if d_lower in diff_map:
                            difficulties.append(diff_map[d_lower])
                        elif d_lower in ['basic', 'advanced', 'expert', 'master', 'remaster']:
                            difficulties.append(d_lower)
                if difficulties:
                    song_record = list(filter(lambda x: x.get('difficulty', '').lower() in difficulties, song_record))
                    details['Diff'] = ' '.join(d for d in difficulties)
            elif cmd in ["lv", "level"]:
                parts = cmd_num.split()
                if len(parts) == 1:
                    level = float(parts[0])
                    song_record = list(filter(lambda x: x['internalLevelValue'] == level, song_record))
                    details['Lv'] = f'{level}'
                else:
                    lv_start, lv_stop = map(float, parts[:2])
                    song_record = list(filter(lambda x: lv_start <= x['internalLevelValue'] <= lv_stop, song_record))
                    details['Lv'] = f'{lv_start} ~ {lv_stop}'
            elif cmd in ["next", "nxt"]:
                filter_rules = [
                    (lambda x: x['version'] != MAIMAI_VERSION[ver][-1]),
                    (lambda x: x['version'] == MAIMAI_VERSION[ver][-1])
                ]
                details['NextVer'] = 'ON'
            elif cmd in ["ra", "rating"]:
                parts = cmd_num.split()
                if len(parts) == 1:
                    ra = int(parts[0])
                    song_record = list(filter(lambda x: x['ra'] == ra, song_record))
                    details['RA'] = f'{ra}'
                else:
                    ra_start, ra_stop = map(int, parts[:2])
                    song_record = list(filter(lambda x: ra_start <= x['ra'] <= ra_stop, song_record))
                    details['RA'] = f'{ra_start} ~ {ra_stop}'
            elif cmd in ["dx", "dxscore"]:
                parts = cmd_num.split()
                if not len(parts):
                    sort_rule = lambda x: (x["dx_percentage"], float(x["score"][:-1]))
                    details['Sort'] = 'DX Score'
                elif len(parts) == 1:
                    dx_percentage = int(re.sub(r"\D", "", parts[0]))
                    song_record = list(filter(lambda x: x['dx_percentage'] * 100 >= dx_percentage, song_record))
                    details['DxScr'] = f'≧ {dx_percentage}%'
                else:
                    dx_start = int(re.sub(r"\D", "", parts[0]))
                    dx_stop = int(re.sub(r"\D", "", parts[1]))
                    song_record = list(filter(lambda x: dx_start <= x['dx_percentage'] * 100 <= dx_stop, song_record))
                    details['DxScr'] = f'{dx_start}% ~ {dx_stop}%'
            elif cmd in ["dxstar", "star"]:
                parts = cmd_num.split()
                if len(parts) == 1:
                    dx_star = int(re.sub(r"\D", "", parts[0]))
                    song_record = list(filter(lambda x: x['dx_star'] == dx_star, song_record))
                    details['Star'] = f'{dx_star}'
                else:
                    dx_start = int(re.sub(r"\D", "", parts[0]))
                    dx_stop = int(re.sub(r"\D", "", parts[1]))
                    song_record = list(filter(lambda x: dx_start <= x['dx_star'] <= dx_stop, song_record))
                    details['Star'] = f'{dx_start} ~ {dx_stop}'
            elif cmd in ["score", "scr"]:
                parts = cmd_num.split()
                if len(parts) == 1:
                    score = float(re.sub(r"[^0-9.]", "", parts[0]))
                    song_record = list(filter(lambda x: float(x['score'].replace("%", "")) >= score, song_record))
                    details['Scr'] = f'≧ {score:.4f}%'
                else:
                    scr_start = float(re.sub(r"[^0-9.]", "", parts[0]))
                    scr_stop = float(re.sub(r"[^0-9.]", "", parts[1]))
                    song_record = list(filter(lambda x: scr_start <= float(x['score'].replace("%", "")) <= scr_stop, song_record))
                    details['Scr'] = f'{scr_start}% ~ {scr_stop}%'
            elif cmd in ["ver", "version"]:
                # 处理版本筛选：-ver [version1] [version2] ...
                raw_versions = cmd_num.split()
                versions = []
                for v in raw_versions:
                    if v.strip():
                        # 将 + 替换为 " PLUS"
                        processed = v.strip().replace("+", " PLUS").lower().replace("dx", "maimaiでらっくす").replace("deluxe", "maimaiでらっくす")
                        versions.append(processed)
                # 筛选歌曲版本在指定列表中的记录（忽略大小写）
                song_record = list(filter(lambda x: (x.get('version') or '').lower() in versions, song_record))
                details['Ver'] = ""
                for version in versions:
                    plus = False
                    if "plus" in version:
                        plus = True
                    details['Ver'] += version.lower().replace("maimaiでらっくす", "dx").replace("plus", "")[:3].strip()
                    if plus:
                        details['Ver'] += "+"
                    details['Ver'] += " "
            elif cmd in ["type", "tp"]:
                # 处理谱面类型筛选：-type dx / -type std
                raw_types = [t.strip().lower() for t in cmd_num.split() if t.strip()]
                valid_types = []
                for t in raw_types:
                    if t in ('dx', 'std'):
                        valid_types.append(t)
                if valid_types:
                    song_record = list(filter(lambda x: x.get('type', '').lower() in valid_types, song_record))
                    details['Type'] = ' / '.join(t.upper() for t in valid_types)
            elif cmd in ["page", "pg"]:
                try:
                    page = max(1, int(cmd_num.strip()))
                    if page > 1:
                        details['Page'] = str(page)
                except ValueError:
                    pass
            elif cmd in ["times", "tm"]:
                parts = cmd_num.split()
                times = min(float(parts[0]), 2.5)
                if times > 0:
                    details['Times'] = times
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
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page-1)*num_35 : page*num_35]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page-1)*num_15 : page*num_15]

    elif type == "best40":
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page-1)*num_25 : page*num_25]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page-1)*num_15 : page*num_15]

    elif type == "best35":
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page-1)*num_35 : page*num_35]

    elif type == "best15":
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page-1)*num_15 : page*num_15]

    elif type == "allb35":
        up_songs = sorted(song_record, key=sort_rule, reverse=True)[(page-1)*num_35 : page*num_35]

    elif type == "allb50":
        up_songs = sorted(song_record, key=sort_rule, reverse=True)[(page-1)*num_50 : page*num_50]

    elif type == "apb50":
        up_songs_data = [x for x in up_songs_data if x.get("combo_icon") in ("ap", "app")]
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page-1)*num_35 : page*num_35]

        down_songs_data = [x for x in down_songs_data if x.get("combo_icon") in ("ap", "app")]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page-1)*num_15 : page*num_15]

    elif type == "fdxb50":
        up_songs_data = [x for x in up_songs_data if x.get("sync_icon") in ("fdx", "fdxp")]
        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page-1)*num_35 : page*num_35]

        down_songs_data = [x for x in down_songs_data if x.get("sync_icon") in ("fdx", "fdxp")]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page-1)*num_15 : page*num_15]

    elif type == "unknown":
        up_songs = list(filter(lambda x: x['version'] == "UNKNOWN", song_record))

    elif type == "rct50":
        up_songs = song_record

    elif type == "idlb50":
        for rcd in up_songs_data:
            ideal_score, score_icon = get_ideal_score(float(rcd['score'][:-1]))
            rcd['score'] = f"{ideal_score:.4f}%"
            if score_icon:
                rcd['score_icon'] = score_icon
            if ideal_score == 101:
                rcd['combo_icon'] = "app"
            rcd['ra'] = get_single_ra(rcd['internalLevelValue'], ideal_score, ideal_score == 101)

        for rcd in down_songs_data:
            ideal_score, score_icon = get_ideal_score(float(rcd['score'][:-1]))
            rcd['score'] = f"{ideal_score:.4f}%"
            if score_icon:
                rcd['score_icon'] = score_icon
            if ideal_score == 101:
                rcd['combo_icon'] = "app"
            rcd['ra'] = get_single_ra(rcd['internalLevelValue'], ideal_score, ideal_score == 101)

        up_songs = sorted(up_songs_data, key=sort_rule, reverse=True)[(page-1)*num_35 : page*num_35]
        down_songs = sorted(down_songs_data, key=sort_rule, reverse=True)[(page-1)*num_15 : page*num_15]

    else:
        return select_records(song_record, "best50", command, ver)

    return up_songs, down_songs, details

async def generate_records(user_id, id_use, type="best50", command="", ver="jp"):
    if id_use not in USERS:
        return mention_error(user_id) if id_use != user_id else segaid_error(user_id)

    if "personal_info" not in USERS[id_use]:
        return mention_error(user_id) if id_use != user_id else info_error(user_id)

    recent = (type == "rct50")
    recent_type = (type == "best40")
    song_record = read_record(id_use, recent, recent_type)
    if not len(song_record):
        return record_error(user_id)

    up_songs, down_songs, details = select_records(song_record, type, command, ver)
    if not up_songs and not down_songs:
        return song_error(user_id)

    if type == "unknown":
        type = "未だ知らず"

    record_img = generate_records_picture(up_songs, down_songs, type.upper(), ver, details)

    # 获取用户信息并创建用户信息图片
    user_info = USERS[id_use].get('personal_info')
    profile_img = generate_profile(user_info, user_id=id_use)
    user_tz = get_user_timezone(user_id)
    img = compose_images([profile_img, record_img], spacing=0, border_width=0, timezone_offset=user_tz, bg_filter=_get_user_bg_filter(user_id))

    # 清理中间图片对象
    del profile_img, record_img
    gc.collect(0)

    original_url, preview_url = await smart_upload(img, user_id)

    # 清理最终图片对象
    del img
    gc.collect(0)

    # 检查上传是否成功
    if not original_url or not preview_url:
        logger.error(f"[Image] ✗ Upload failed")
        return system_error(user_id)

    message = ImageMessage(original_content_url=original_url, preview_image_url=preview_url)

    return message

async def generate_friend_record(user_id, friend_code, type="best50", cmd="", ver="jp"):
    if user_id not in USERS:
        return segaid_error(user_id)

    elif 'sega_id' not in USERS[user_id] or 'sega_pwd' not in USERS[user_id]:
        return segaid_error(user_id)

    sega_id = USERS[user_id]['sega_id']
    sega_pwd = USERS[user_id]['sega_pwd']

    # 使用异步登录和获取好友成绩
    async def fetch_friend_data():
        cookies = await login_to_maimai(sega_id, sega_pwd, ver)
        if cookies is None or cookies == "MAINTENANCE":
            return cookies, None, None
        tasks = [
            get_friend_info(cookies, friend_code, ver),
            get_friend_records(cookies, friend_code, ver)
        ]
        friend_info, friend_records = await asyncio.gather(*tasks)
        return None, friend_info, friend_records

    error, friend_info, friend_records = await fetch_friend_data()

    if error == "MAINTENANCE":
        return maintenance_error(user_id)
    if error is None and friend_records is None:
        return segaid_error(user_id)

    # 检查 friend_info 是否包含维护错误
    if isinstance(friend_info, dict) and friend_info.get("error") == "MAINTENANCE":
        return maintenance_error(user_id)

    # 检查 friend_records 是否为维护模式字符串
    if friend_records == "MAINTENANCE":
        return maintenance_error(user_id)

    if not friend_records:
        return friend_rcd_error(user_id)

    recent_type = (type == "best40")
    friend_records = get_detailed_info(friend_records, ver, recent_type)

    up_songs, down_songs, details = select_records(friend_records, type, cmd, ver)

    if not (len(up_songs) + len(down_songs)):
        return song_error(user_id)

    user_info_img = generate_profile(friend_info)
    rcd_img = generate_records_picture(up_songs, down_songs, type.upper(), ver, details)
    user_tz = get_user_timezone(user_id)
    img = compose_images([user_info_img, rcd_img], spacing=0, border_width=0, timezone_offset=user_tz, bg_filter=_get_user_bg_filter(user_id))

    # 清理中间图片对象
    del user_info_img, rcd_img
    gc.collect(0)

    original_url, preview_url = await smart_upload(img, user_id)
    message = [
        TextMessage(text=get_multilingual_text(friend_rcd_text, user_id).format(name=friend_info["name"])),
        ImageMessage(original_content_url=original_url, preview_image_url=preview_url)
    ]

    # 清理最终图片对象
    del img
    gc.collect(0)

    return message

async def generate_level_records(user_id, id_use, level, ver="jp", page=1):
    if id_use not in USERS:
        return mention_error(user_id) if id_use != user_id else segaid_error(user_id)

    if "personal_info" not in USERS[id_use]:
        return mention_error(user_id) if id_use != user_id else info_error(user_id)

    song_record = read_record(id_use)

    if not len(song_record):
        return record_error(user_id)

    level_values = parse_level_value(level)
    if not level_values:
        return song_error(user_id)

    lv_min = min(level_values)
    lv_max = max(level_values)
    command = f"-lv {lv_min} {lv_max} -page {page}"

    up_level_list, down_level_list, _ = select_records(song_record, "best50", command, ver)

    if not up_level_list and not down_level_list:
        return level_record_not_found(level, page, user_id)

    title = f"Lv {level}"

    record_img = generate_records_picture(up_level_list, down_level_list, title.replace("+", "⁺"), ver)

    # 获取用户信息并创建用户信息图片
    user_info = USERS[id_use].get('personal_info')
    profile_img = generate_profile(user_info, user_id=id_use)
    user_tz = get_user_timezone(user_id)
    img = compose_images([profile_img, record_img], spacing=0, border_width=0, timezone_offset=user_tz, bg_filter=_get_user_bg_filter(user_id))

    # 清理中间图片对象
    del profile_img, record_img
    gc.collect(0)

    original_url, preview_url = await smart_upload(img, user_id)

    # 清理最终图片对象
    del img
    gc.collect(0)

    message = [
        ImageMessage(original_content_url=original_url, preview_image_url=preview_url),
        level_record_page_hint(page, user_id) if page == 1 else None
    ]
    message = [m for m in message if m]
    return message

async def generate_version_songs(user_id, version_title, ver="jp"):
    songs, versions = read_dxdata(ver)

    target_version = []
    target_icon = []
    target_type = ""

    version_title = version_title.lower().replace("dx", "maimaiでらっくす").replace("deluxe", "maimaiでらっくす")

    for version in versions:
        if version_title == version['version'].lower():
            target_version.append(version['version'])

    if not len(target_version):
        return version_error(user_id)

    version_img = None
    version_img_path = os.path.join(VERSIONS_DIR, f"{version_title.replace(' ', '_')}.png")
    try:
        with Image.open(version_img_path) as _ver:
            version_img = resize_by_width(_ver.copy(), 1340)
    except Exception as e:
        logger.error(f"[VersionImage] ✗ Failed to load image: file={version_img_path}, error={e}")

    songs_data = list(filter(lambda x: x['version'] in target_version and x['type'] not in ['utage'], songs))
    version_list_img = generate_version_list(songs_data)

    user_tz = get_user_timezone(user_id)
    user_bg_filter = _get_user_bg_filter(user_id)
    if version_img is None:
        img = compose_images([version_list_img], border_width=0, timezone_offset=user_tz, bg_filter=user_bg_filter)
    else:
        img = compose_images([version_img, version_list_img], border_width=0, timezone_offset=user_tz, bg_filter=user_bg_filter)

    # 清理中间图片对象
    if version_img is not None:
        del version_img
    del version_list_img
    gc.collect(0)

    original_url, preview_url = await smart_upload(img, user_id)

    # 清理最终图片对象
    del img
    gc.collect(0)

    # 检查上传是否成功
    if not original_url or not preview_url:
        logger.error(f"[Image] ✗ Upload failed")
        return system_error(user_id)

    message = ImageMessage(original_content_url=original_url, preview_image_url=preview_url)

    return message

# ==================== 消息处理 ====================

# Web任务路由规则 (需要网络请求的耗时任务)
WEB_TASK_ROUTES = {
    # 精确匹配规则
    'exact': {
        "maimai update": async_maimai_update_task,
        "update": async_maimai_update_task,
    },
    # 前缀匹配规则
    'prefix': {
        "friend-rcd ": async_generate_friend_record_task,
        "search-record ": async_get_song_record_by_id_task,
    },
    # 后缀匹配规则
    'suffix': {
        "のレコード": async_get_song_record_task,
        "song-record": async_get_song_record_task,
        "record": async_get_song_record_task,
    }
}

def show_loading(user_id):
    """在私聊中显示加载动画"""
    try:
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).show_loading_animation(
                ShowLoadingAnimationRequest(chatId=user_id, loadingSeconds=20)
            )
    except Exception:
        pass

def route_to_web_queue(event):
    """
    路由消息到Web任务队列

    Args:
        event: LINE消息事件

    Returns:
        bool: True表示已路由到web队列, False表示不是web任务
    """
    user_message = event.message.text.strip()
    user_id = event.source.user_id

    # 检查精确匹配的web任务
    if user_message in WEB_TASK_ROUTES['exact']:
        task_func = WEB_TASK_ROUTES['exact'][user_message]

        # 频率限制检查
        if check_rate_limit(user_id, task_func.__name__):
            smart_reply(user_id, event.reply_token, rate_limit_msg(user_id), configuration)
            return True

        try:
            # 生成任务ID
            task_id = f"user_{user_id}_{datetime.now().timestamp()}"

            # 获取用户昵称
            nickname = get_user_nickname_wrapper(user_id, use_cache=True)

            # 添加到任务追踪
            with task_tracking_lock:
                task_tracking['queued'].append({
                    'id': task_id,
                    'function': task_func.__name__,
                    'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': user_id,
                    'nickname': nickname
                })

            show_loading(user_id)
            webtask_queue.put_nowait((task_func, (event,), task_id))
            return True
        except queue.Full:
            smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
            return True

    # 检查前缀匹配的web任务
    for prefix, task_func in WEB_TASK_ROUTES['prefix'].items():
        if user_message.startswith(prefix):
            # 频率限制检查
            if check_rate_limit(user_id, task_func.__name__):
                smart_reply(user_id, event.reply_token, rate_limit_msg(user_id), configuration)
                return True

            try:
                # 生成任务ID
                task_id = f"user_{user_id}_{datetime.now().timestamp()}"

                # 获取用户昵称
                nickname = get_user_nickname_wrapper(user_id, use_cache=True)

                # 添加到任务追踪
                with task_tracking_lock:
                    task_tracking['queued'].append({
                        'id': task_id,
                        'function': task_func.__name__,
                        'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'user_id': user_id,
                        'nickname': nickname
                    })

                show_loading(user_id)
                webtask_queue.put_nowait((task_func, (event,), task_id))
                return True
            except queue.Full:
                smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
                return True

    # 检查后缀匹配的web任务
    for suffix, task_func in WEB_TASK_ROUTES['suffix'].items():
        if user_message.endswith(suffix):
            # 频率限制检查
            if check_rate_limit(user_id, task_func.__name__):
                smart_reply(user_id, event.reply_token, rate_limit_msg(user_id), configuration)
                return True

            try:
                # 生成任务ID
                task_id = f"user_{user_id}_{datetime.now().timestamp()}"

                # 获取用户昵称
                nickname = get_user_nickname_wrapper(user_id, use_cache=True)

                # 添加到任务追踪
                with task_tracking_lock:
                    task_tracking['queued'].append({
                        'id': task_id,
                        'function': task_func.__name__,
                        'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'user_id': user_id,
                        'nickname': nickname
                    })

                show_loading(user_id)
                webtask_queue.put_nowait((task_func, (event,), task_id))
                return True
            except queue.Full:
                smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
                return True

    # 不是web任务,返回False
    return False

# 图片生成任务路由规则
IMAGE_TASK_ROUTES = {
    # 精确匹配规则 - 这些命令会生成图片
    'exact': {},
    # 前缀匹配规则
    'prefix': [],
    # 后缀匹配规则
    'suffix': [
        ("ってどんな曲", "info", "song-info"),
        ("の達成状況", "achievement"),
        ("のレコード", "song-record", "record"),
        ("のバージョンリスト", "version-list"),
        ("の定数リスト", "のレベルリスト", "level-list")
    ],
    # B系列命令 (生成图片)
    'b_commands': {
        "b50", "best50",
        "b40", "best40",
        "b35", "best35",
        "b15", "best15",
        "ab35", "allb35",
        "ab50", "allb50",
        "apb50", "ap50",
        "fdxb50", "fdx50",
        "rct50", "r50",
        "idealb50", "idlb50",
        "unknown"
    }
}

def route_to_image_queue(event):
    """
    路由消息到图片生成任务队列

    Args:
        event: LINE消息事件

    Returns:
        bool: True表示已路由到image队列, False表示不是图片生成任务
    """
    user_message = event.message.text.strip()
    user_id = event.source.user_id

    # 剥离末尾过滤后缀（-uc / -up），用于后续匹配
    msg_for_match = re.sub(r"\s*-(uc|up|c)\s*$", "", user_message)

    # 检查精确匹配的图片生成任务
    if msg_for_match in IMAGE_TASK_ROUTES['exact']:
        # 频率限制检查 - 使用消息类型作为任务类型
        if check_rate_limit(user_id, f"image:{user_message}"):
            smart_reply(user_id, event.reply_token, rate_limit_msg(user_id), configuration)
            return True

        try:
            task_id = f"image_{user_id}_{datetime.now().timestamp()}"
            nickname = get_user_nickname_wrapper(user_id, use_cache=True)

            with task_tracking_lock:
                task_tracking['queued'].append({
                    'id': task_id,
                    'function': 'async_generate_image_task',
                    'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': user_id,
                    'nickname': nickname
                })

            show_loading(user_id)
            image_queue.put_nowait((async_generate_image_task, (event,), task_id))
            return True
        except queue.Full:
            smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
            return True

    # 检查后缀匹配的图片生成任务（用剥离过滤后缀后的消息匹配）
    for suffixes in IMAGE_TASK_ROUTES['suffix']:
        for suffix in suffixes:
            if msg_for_match.endswith(suffix):
                try:
                    task_id = f"image_{user_id}_{datetime.now().timestamp()}"
                    nickname = get_user_nickname_wrapper(user_id, use_cache=True)

                    with task_tracking_lock:
                        task_tracking['queued'].append({
                            'id': task_id,
                            'function': 'async_generate_image_task',
                            'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'user_id': user_id,
                            'nickname': nickname
                        })

                    show_loading(user_id)
                    image_queue.put_nowait((async_generate_image_task, (event,), task_id))
                    return True
                except queue.Full:
                    smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
                    return True

    # 检查レコードリスト (带数字的)
    if re.match(r".+(のレコードリスト|record-list)[ 　]*\d*$", user_message):
        try:
            task_id = f"image_{user_id}_{datetime.now().timestamp()}"
            nickname = get_user_nickname_wrapper(user_id, use_cache=True)

            with task_tracking_lock:
                task_tracking['queued'].append({
                    'id': task_id,
                    'function': 'async_generate_image_task',
                    'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': user_id,
                    'nickname': nickname
                })

            show_loading(user_id)
            image_queue.put_nowait((async_generate_image_task, (event,), task_id))
            return True
        except queue.Full:
            smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
            return True

    # 检查 B 系列命令
    first_word = re.split(r"[ \n]", user_message.lower(), 1)[0]
    if first_word in IMAGE_TASK_ROUTES['b_commands']:
        # 频率限制检查 - B系列命令使用统一的限制
        if check_rate_limit(user_id, "image:b_series"):
            smart_reply(user_id, event.reply_token, rate_limit_msg(user_id), configuration)
            return True

        try:
            task_id = f"image_{user_id}_{datetime.now().timestamp()}"
            nickname = get_user_nickname_wrapper(user_id, use_cache=True)

            with task_tracking_lock:
                task_tracking['queued'].append({
                    'id': task_id,
                    'function': 'async_generate_image_task',
                    'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': user_id,
                    'nickname': nickname
                })

            show_loading(user_id)
            image_queue.put_nowait((async_generate_image_task, (event,), task_id))
            return True
        except queue.Full:
            smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
            return True

    # 检查 ランダム曲 / random-song
    if user_message.startswith("random"):
        try:
            task_id = f"image_{user_id}_{datetime.now().timestamp()}"
            nickname = get_user_nickname_wrapper(user_id, use_cache=True)

            with task_tracking_lock:
                task_tracking['queued'].append({
                    'id': task_id,
                    'function': 'async_generate_image_task',
                    'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': user_id,
                    'nickname': nickname
                })

            show_loading(user_id)
            image_queue.put_nowait((async_generate_image_task, (event,), task_id))
            return True
        except queue.Full:
            smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
            return True

    # 检查难度评级进度命令（如 "13sss+進捗", "14AP progress", "15SSS進捗-uc"）
    if re.match(r"^(\d+\+?)\s*(sss\+|ss\+|s\+|ap\+|fc\+|fdx\+|sss|ss|ap|fc|fdx|s)\s*(progress|進捗|进度)\s*(?:-(uc|up|c))?\s*$", user_message.lower()):
        try:
            task_id = f"image_{user_id}_{datetime.now().timestamp()}"
            nickname = get_user_nickname_wrapper(user_id, use_cache=True)

            with task_tracking_lock:
                task_tracking['queued'].append({
                    'id': task_id,
                    'function': 'async_generate_image_task',
                    'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': user_id,
                    'nickname': nickname
                })

            show_loading(user_id)
            image_queue.put_nowait((async_generate_image_task, (event,), task_id))
            return True
        except queue.Full:
            smart_reply(user_id, event.reply_token, access_error(user_id), configuration)
            return True

    # 不是图片生成任务
    return False


def handle_accept_perm_request(user_id: str, request_id: str) -> TextMessage:
    """
    处理接受权限请求的命令

    Args:
        user_id: 用户ID
        request_id: 请求ID

    Returns:
        TextMessage对象
    """

    result = accept_perm_request(user_id, request_id)

    if result['success']:
        text = get_multilingual_text(perm_request_accept_success_text, user_id).format(
            token_id=result['token_id'],
            requester_name=result.get('requester_name', result['token_id'])
        )
    elif result.get('error') == 'Request not found':
        text = get_multilingual_text(perm_request_already_processed_text, user_id)
    else:
        notify_admins_error(
            error_title="Permission Request Accept Error",
            error_details=f"Error: {result['error']}\nMessage: {result['message']}\nRequest ID: {request_id}",
            context={
                "Request ID": request_id,
                "Error Type": result['error']
            },
            user_id=user_id
        )
        text = get_multilingual_text(system_error_text, user_id)

    return TextMessage(text=text)


def handle_reject_perm_request(user_id: str, request_id: str) -> TextMessage:
    """
    处理拒绝权限请求的命令

    Args:
        user_id: 用户ID
        request_id: 请求ID

    Returns:
        TextMessage对象
    """

    result = reject_perm_request(user_id, request_id)

    if result['success']:
        text = get_multilingual_text(perm_request_reject_success_text, user_id).format(
            token_id=result['token_id'],
            requester_name=result.get('requester_name', result['token_id'])
        )
    elif result.get('error') == 'Request not found':
        text = get_multilingual_text(perm_request_already_processed_text, user_id)
    else:
        notify_admins_error(
            error_title="Permission Request Reject Error",
            error_details=f"Error: {result['error']}\nMessage: {result['message']}\nRequest ID: {request_id}",
            context={
                "Request ID": request_id,
                "Error Type": result['error']
            },
            user_id=user_id
        )
        text = get_multilingual_text(system_error_text, user_id)

    return TextMessage(text=text)


def mark_message_as_read(mark_as_read_token: str, user_id: str = None):
    """
    标记用户消息为已读

    Args:
        mark_as_read_token: 消息的已读标记 token
        user_id: LINE用户ID (仅用于日志)
    """
    if not mark_as_read_token:
        logger.debug(f"[MarkAsRead] ⊘ No token provided: user_id={user_id}")
        return

    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            mark_request = MarkMessagesAsReadByTokenRequest(
                mark_as_read_token=mark_as_read_token
            )
            line_bot_api.mark_messages_as_read_by_token(mark_request)
            logger.info(f"[MarkAsRead] ✓ Marked messages as read: user_id={user_id}")
    except Exception as e:
        logger.error(f"[MarkAsRead] ✗ Failed to mark as read: user_id={user_id}, error={e}")


# ==================== Mention 处理函数 ====================

def check_mention_filter(event):
    """检查是否应该过滤消息（@ALL 或多个 mention）

    逻辑：
    - @ALL → 过滤
    - 总 mention 数 >= 3 → 过滤（假设其中一个是 bot）
    - 总 mention 数 <= 2 → 允许（可能是 @bot + @user）

    Args:
        event: LINE 消息事件

    Returns:
        bool: True 表示应该忽略此消息，False 表示可以处理
    """
    if not hasattr(event.message, 'mention') or not event.message.mention:
        return False

    mentionees = event.message.mention.mentionees
    if not mentionees:
        return False

    user_id = event.source.user_id

    # 检查 @ALL
    for mentionee in mentionees:
        mention_type = getattr(mentionee, 'type', None)
        if mention_type == 'all':
            logger.info(f"[Mention] @ALL detected, ignoring message: user_id={user_id}, text='{event.message.text}'")
            return True

    # 统计非 bot 的用户 mention 数量
    user_mention_count = 0
    for mentionee in mentionees:
        is_self = getattr(mentionee, 'is_self', False)
        if not is_self:
            user_mention_count += 1

    # 如果有 2 个或以上的用户 mention（不包括 bot），则过滤
    # 允许的情况:
    # - @user → 1 个用户 mention → 允许
    # - @bot @user → 1 个用户 mention（跳过 bot）→ 允许
    # 过滤的情况:
    # - @user1 @user2 → 2 个用户 mentions → 过滤
    # - @bot @user1 @user2 → 2 个用户 mentions → 过滤
    if user_mention_count >= 2:
        logger.info(f"[Mention] Multiple user mentions ({user_mention_count}) detected, ignoring message: user_id={user_id}, text='{event.message.text}'")
        return True

    return False


def extract_single_mention(event, user_id):
    """提取单个 mention 的用户 ID

    注意：@bot 会被自动跳过

    Args:
        event: LINE 消息事件
        user_id: 发送消息的用户 ID

    Returns:
        str or None: 被提及的用户 ID，如果没有 mention 或用户未注册则返回 None
    """
    if not hasattr(event.message, 'mention') or not event.message.mention:
        return None

    mentionees = event.message.mention.mentionees
    if not mentionees or len(mentionees) == 0:
        return None

    # 跳过 @bot，查找第一个非 bot 的 mention
    for mentionee in mentionees:
        # 跳过 bot 自己
        is_self = getattr(mentionee, 'is_self', False)
        if is_self:
            continue

        mentioned_user_id = getattr(mentionee, 'user_id', None)
        if mentioned_user_id:
            if mentioned_user_id in USERS:
                logger.info(f"[Mention] User mentioned: user_id={user_id}, mentioned_user_id={mentioned_user_id}")
                return mentioned_user_id
            else:
                logger.debug(f"[Mention] Mentioned user not registered: mentioned_user_id={mentioned_user_id}")

    return None


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """
    文本消息处理入口

    根据消息类型智能路由:
    - Web任务 → webtask_queue (网络请求，如 maimai_update)
    - 图片生成任务 → image_queue (图片生成，如 b50 等)
    - 其他任务 → 同步处理 (快速文本响应)
    """
    # 标记消息为已读（使用 webhook 提供的 token）
    mark_as_read_token = getattr(event.message, 'mark_as_read_token', None)
    mark_message_as_read(mark_as_read_token, event.source.user_id)

    # 检查 mention 情况 - @ALL 或多个 @ 时直接忽略不回复
    if check_mention_filter(event):
        return

    # 清理消息文本中的 mention 特殊字符（LINE 的 mention 格式是 \ufffd@显示名\ufffd）
    # 移除所有不可见的 Unicode 字符和 @ 后的用户名
    original_text = event.message.text
    cleaned_text = original_text

    # 如果有 mention 信息，使用官方 API 提供的索引精确删除
    # 参考: https://developers.line.biz/en/docs/messaging-api/receiving-messages/
    # 注意：会删除所有 mention 文本（包括 @bot 和 @user）
    if hasattr(event.message, 'mention') and event.message.mention and event.message.mention.mentionees:
        # 从后往前删除，避免索引偏移问题
        # mentionees 数组包含 index（起始位置）和 length（长度）属性
        for mentionee in reversed(event.message.mention.mentionees):
            if hasattr(mentionee, 'index') and hasattr(mentionee, 'length'):
                start = mentionee.index
                end = start + mentionee.length
                # 精确删除 mention 文本（包括 @bot，支持包含空格的用户名）
                cleaned_text = cleaned_text[:start] + cleaned_text[end:]

    # 删除不可见字符（在删除 mention 之后，避免影响索引）
    cleaned_text = re.sub(r'[\ufffd]', '', cleaned_text)
    cleaned_text = cleaned_text.strip()

    # 替换 event.message.text 用于命令匹配
    event.message.text = cleaned_text

    if original_text != cleaned_text:
        logger.debug(f"[TextCleaning] Cleaned mention: original='{original_text}', cleaned='{cleaned_text}'")

    # 检查是否是web任务
    if route_to_web_queue(event):
        return

    # 检查是否是图片生成任务
    if route_to_image_queue(event):
        return

    # 同步处理其他文本命令
    handle_sync_text_command(event)


# ==================== 任务处理函数 ====================

def handle_sync_text_command(event):
    """
    同步处理文本命令 - 直接在主线程执行

    命令分类：
    1. 基础命令 - donate, unbind, profile, friend list
    2. 模糊匹配命令 - 歌曲查询、Rating 对照、达成情况等
    3. B 系列命令 - b50, rct50, apb50 等
    4. 特殊命令 - bind, language, calc
    5. 管理员命令 - dxdata update, devtoken
    """
    # 记录开始时间以统计响应时间
    start_time = time.time()

    def tracked_reply(user_id, reply_token, reply_message, addition=True):
        """包装 smart_reply 并更新统计"""
        # 计算响应时间
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒

        # 更新统计
        with stats_lock:
            STATS['tasks_processed'] += 1
            STATS['response_time'] += response_time
            logger.debug(f"[Sync] ✓ Command processed: total={STATS['tasks_processed']}, avg_time={STATS['response_time']/STATS['tasks_processed']:.1f}ms")

        return smart_reply(user_id, reply_token, reply_message, configuration, addition)

    user_message = event.message.text.strip()
    user_id = event.source.user_id
    source_type = getattr(event.source, 'type', 'user')
    # ========================================
    # 用户上下文初始化
    # ========================================

    # 检查 @ mention（提取被提到的用户 ID）
    mentioned_user_id = extract_single_mention(event, user_id)

    # 初始化用户版本和目标用户
    if user_id in USERS:
        mai_ver = USERS[user_id].get("version", "jp")
        # 只有当 mentioned_user_id 存在且已注册时才使用
        id_use = mentioned_user_id if mentioned_user_id else user_id
        mai_ver_use = USERS[id_use].get("version", "jp") if id_use in USERS else mai_ver
    else:
        id_use = user_id
        mai_ver = "jp"
        mai_ver_use = "jp"

    # ========================================
    # 0. Unbind 命令特殊处理（需要二次确认）
    # ========================================
    UNBIND_COMMANDS = ["unbind"]
    if user_message in UNBIND_COMMANDS:
        # 第一步：返回确认提示
        reply_message = TextMessage(text=get_multilingual_text(unbind_confirm_text, user_id))
        return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

    UNBIND_CONFIRM_COMMANDS = ["unbind confirm"]
    if user_message in UNBIND_CONFIRM_COMMANDS:
        # 第二步：执行解绑操作
        reply_message = user_unbind(user_id)
        return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

    # ========================================
    # 1. 基础命令 - 精确匹配
    # ========================================
    COMMAND_MAP = {
        # 捐赠
        "donate": lambda: donate_message,

        # 账户管理
        "profile": lambda: get_user_info(user_id, source_type),
        "getme": lambda: get_user_info(user_id, source_type),

        # 好友列表
        "friend list": lambda: get_friend_list(user_id, source_type),
        "friends": lambda: get_friend_list(user_id, source_type),

        # 系统状态
        "status": lambda: get_bot_status(user_id),
    }

    if user_message in COMMAND_MAP:
        reply_message = COMMAND_MAP[user_message]()
        return tracked_reply(user_id, event.reply_token, reply_message)

    # ========================================
    # 2. 模糊匹配命令 - 规则匹配
    # ========================================
    SPECIAL_RULES = [
        # 排行榜（rank/ranking [jp/intl]）
        (lambda msg: re.match(r"^(rank|ranking)(\s+(jp|intl))?$", msg),
         lambda msg: get_ranking(user_id, id_use, re.match(r"^(rank|ranking)(\s+(jp|intl))?$", msg).group(3))),

        # 歌曲搜索（通过ID）
        (lambda msg: msg.startswith("search ") and len(msg.split()) == 2 and len(msg.split()[1]) == 6,
         lambda msg: asyncio.run(search_song_by_id(user_id, msg.split()[1], mai_ver))),

        # Calc （通过ID）
        (lambda msg: msg.startswith("calc-song ") and len(msg.split()) == 2 and len(msg.split()[1]) == 6,
         lambda msg: calc_by_id(user_id, msg.split()[1], mai_ver)),

        # 艺术家搜索（artist <keyword> [page]）
        (lambda msg: msg.startswith("artist ") and len(msg.split()) >= 2,
         lambda msg: search_by_artist(
             user_id,
             ' '.join(msg.split()[1:-1]) if msg.split()[-1].isdigit() and len(msg.split()) >= 3 else ' '.join(msg.split()[1:]),
             mai_ver,
             int(msg.split()[-1]) if msg.split()[-1].isdigit() and len(msg.split()) >= 3 else 1,
             source_type)),

        # 谱面设计师搜索（designer <keyword> [page]）
        (lambda msg: msg.startswith("designer ") and len(msg.split()) >= 2,
         lambda msg: search_by_designer(
             user_id,
             ' '.join(msg.split()[1:-1]) if msg.split()[-1].isdigit() and len(msg.split()) >= 3 else ' '.join(msg.split()[1:]),
             mai_ver,
             int(msg.split()[-1]) if msg.split()[-1].isdigit() and len(msg.split()) >= 3 else 1,
             source_type)),

        # 歌曲信息查询
        (lambda msg: msg.endswith(("ってどんな曲", "info", "song-info")),
         lambda msg: asyncio.run(search_song(user_id, re.sub(r"\s*(ってどんな曲|info|song-info)$", "", msg).strip(), mai_ver))),

        # 随机歌曲
        (lambda msg: msg.startswith("random"),
         lambda msg: asyncio.run(random_song(user_id, re.sub(r"^(random)", "", msg).strip(), mai_ver))),

        # Rating 对照表
        (lambda msg: msg.startswith(("rc ", "RC ", "Rc ")),
         lambda msg: handle_rc_command(msg, user_id)),

        # 版本达成情况（支持 -uc/-up 过滤）
        (lambda msg: re.sub(r"\s*-(uc|up|c)\s*$", "", msg).endswith(("の達成状況", "achievement")),
         lambda msg: asyncio.run(generate_plate_rcd(
             user_id, id_use,
             re.sub(r"\s*(の達成状況|achievement)$", "", re.sub(r"\s*-(uc|up|c)\s*$", "", msg)).strip(),
             mai_ver_use,
             filter_mode="uncleared" if re.search(r"-uc\s*$", msg) else ("unplayed" if re.search(r"-up\s*$", msg) else ("cleared" if re.search(r"-c\s*$", msg) else None))))),

        # 等级成绩列表
        (lambda msg: re.match(r".+(のレコードリスト|record-list|records)[ 　]*\d*$", msg),
         lambda msg: asyncio.run(generate_level_records(
             user_id,
             id_use,
             re.sub(r"\s*(のレコードリスト|record-list|records)[ 　]*\d*$", "", msg).strip(),
             mai_ver_use,
             int(re.search(r"(\d+)$", msg).group(1)) if re.search(r"(\d+)$", msg) else 1))),

        # 版本歌曲列表
        (lambda msg: msg.endswith(("のバージョンリスト", "version-list")),
         lambda msg: asyncio.run(generate_version_songs(user_id, re.sub(r"\s*\+\s*", " PLUS", re.sub(r"(のバージョンリスト|version-list)$", "", msg)).strip(), mai_ver))),

        # 定数查询
        (lambda msg: msg.endswith(("の定数リスト", "のレベルリスト", "level-list")),
         lambda msg: asyncio.run(generate_level_rank_progress(user_id, user_id, re.sub(r"\s*(の定数リスト|のレベルリスト|level-list)$", "", msg), ver=mai_ver))),

        # 难度+评级达成情况（如 "13sss+進捗", "14AP progress-uc", "15SSS進捗 -up"）
        (lambda msg: re.match(r"^(\d+\+?)\s*(sss\+|ss\+|s\+|ap\+|fc\+|fdx\+|sss|ss|ap|fc|fdx|s)\s*(progress|進捗|进度)\s*(?:-(uc|up|c))?\s*$", msg.lower()),
         lambda msg: asyncio.run(generate_level_rank_progress(
             user_id,
             id_use,
             re.match(r"^(\d+\+?)", msg.lower()).group(1),
             re.search(r"(sss\+|ss\+|s\+|ap\+|fc\+|fdx\+|sss|ss|ap|fc|fdx|s)", msg.lower()).group(1),
             mai_ver_use,
             filter_mode="uncleared" if re.search(r"-uc\s*$", msg.lower()) else ("unplayed" if re.search(r"-up\s*$", msg.lower()) else ("cleared" if re.search(r"-c\s*$", msg.lower()) else None))))),

        # 权限请求管理
        (lambda msg: msg.startswith("accept-perm-request "),
         lambda msg: handle_accept_perm_request(user_id, re.sub(r"^accept-perm-request ", "", msg).strip())),

        (lambda msg: msg.startswith("reject-perm-request "),
         lambda msg: handle_reject_perm_request(user_id, re.sub(r"^reject-perm-request ", "", msg).strip()))
    ]

    for cond, func in SPECIAL_RULES:
        if cond(user_message):
            reply_message = func(user_message)
            return tracked_reply(user_id, event.reply_token, reply_message)

    # ========================================
    # 3. B 系列命令 - 成绩排行
    # ========================================
    first_word = re.split(r"[ \n]", user_message.lower(), 1)[0]
    rest_text = re.split(r"[ \n]", user_message.lower(), 1)[1] if re.search(r"[ \n]", user_message) else ""

    for aliases, mode in RANK_COMMANDS.items():
        if first_word in aliases:
            reply_message = asyncio.run(generate_records(user_id, id_use, mode, rest_text, mai_ver_use))
            return tracked_reply(user_id, event.reply_token, reply_message)

    # ========================================
    # 4. SEGA ID 绑定
    # ========================================
    BIND_COMMANDS = ["bind"]
    if user_message.lower() in BIND_COMMANDS:
        # 检查是否在群聊中发送
        source_type = getattr(event.source, 'type', 'user')
        if source_type != 'user':
            # 在群聊中，返回警告消息
            reply_message = TextMessage(text=get_multilingual_text(bind_group_warning_text, user_id))
            return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

        # 检查是否已经绑定账号
        add_user(user_id)
        user_data = USERS.get(user_id, {})
        has_account = all(key in user_data for key in ['sega_id', 'sega_pwd', 'version'])

        if has_account:
            # 已经绑定过账号，提示先解绑
            reply_message = TextMessage(text=get_multilingual_text(already_bound_text, user_id))
            return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

        # 返回绑定链接
        bind_url = f"https://{DOMAIN}/linebot/sega_bind?token={generate_bind_token(user_id)}"
        buttons_template = ButtonsTemplate(
            title=sega_bind_title_text,
            text=sega_bind_description_text,
            actions=[URIAction(
                label=sega_bind_button_text,
                uri=bind_url
            )]
        )
        reply_message = TemplateMessage(
            alt_text=sega_bind_alt_text,
            template=buttons_template
        )

        return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

    # ========================================
    # 5 账号重新绑定 (rebind)
    # ========================================
    REBIND_COMMANDS = ["rebind"]
    if user_message.lower() in REBIND_COMMANDS:
        # 检查是否在群聊中发送
        source_type = getattr(event.source, 'type', 'user')
        if source_type != 'user':
            reply_message = TextMessage(text=get_multilingual_text(rebind_group_warning_text, user_id))
            return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

        # 检查用户是否已绑定账号
        user_data = USERS.get(user_id, {})
        has_account = all(key in user_data for key in ['sega_id', 'sega_pwd', 'version'])

        if not has_account:
            reply_message = TextMessage(text=get_multilingual_text(rebind_not_bound_text, user_id))
            return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

        rebind_url = f"https://{DOMAIN}/linebot/sega_bind?token={generate_bind_token(user_id)}&mode=rebind"

        buttons_template = ButtonsTemplate(
            title=get_multilingual_text(rebind_title_alt_text, user_id),
            text=get_multilingual_text(rebind_description_text, user_id),
            actions=[URIAction(
                label=get_multilingual_text(rebind_button_text, user_id),
                uri=rebind_url
            )]
        )
        reply_message = TemplateMessage(
            alt_text=get_multilingual_text(rebind_title_alt_text, user_id),
            template=buttons_template
        )

        return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

    # ========================================
    # 5b 个人设置 (settings)
    # ========================================
    SETTINGS_COMMANDS = ["settings"]
    if user_message.lower() in SETTINGS_COMMANDS:
        # 检查是否在群聊中发送
        source_type = getattr(event.source, 'type', 'user')
        if source_type != 'user':
            reply_message = TextMessage(text=get_multilingual_text(settings_group_warning_text, user_id))
            return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

        # 检查用户是否已绑定账号
        user_data = USERS.get(user_id, {})
        has_account = all(key in user_data for key in ['sega_id', 'sega_pwd', 'version'])

        if not has_account:
            reply_message = TextMessage(text=get_multilingual_text(rebind_not_bound_text, user_id))
            return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

        settings_url = f"https://{DOMAIN}/linebot/settings?token={generate_settings_token(user_id)}"

        buttons_template = ButtonsTemplate(
            title=get_multilingual_text(settings_title_alt_text, user_id),
            text=get_multilingual_text(settings_description_text, user_id),
            actions=[URIAction(
                label=get_multilingual_text(settings_button_text, user_id),
                uri=settings_url
            )]
        )
        reply_message = TemplateMessage(
            alt_text=get_multilingual_text(settings_title_alt_text, user_id),
            template=buttons_template
        )

        return tracked_reply(user_id, event.reply_token, reply_message, addition=False)

    # ========================================
    # 6. Calc 计算器
    # ========================================
    if user_message.startswith("calc "):
        try:
            num = list(map(int, user_message[5:].split()))
            if len(num) == 4:
                num = [num[0], num[1], num[2], 0, num[3]]
            if len(num) != 5:
                raise ValueError
            notes = dict(zip(['tap', 'hold', 'slide', 'touch', 'break'], num))
            scores = get_note_score(notes)
            reply_message = generate_calc_result_flex(notes, scores)
        except Exception:
            reply_message = input_error(user_id)
        return tracked_reply(user_id, event.reply_token, reply_message)

    # ========================================
    # 默认：未匹配任何命令
    # ========================================
    return

#位置信息处理
@handler.add(MessageEvent, message=LocationMessageContent)
def handle_location_message(event):
    """
    位置消息处理 - 异步获取附近机厅
    """
    # 标记消息为已读（使用 webhook 提供的 token）
    mark_as_read_token = getattr(event.message, 'mark_as_read_token', None)
    mark_message_as_read(mark_as_read_token, event.source.user_id)

    lat = event.message.latitude
    lng = event.message.longitude
    user_id = event.source.user_id

    stores = asyncio.run(get_nearby_maimai_stores(lat, lng, USERS[user_id].get('version', "jp")))

    # 检查维护状态
    if stores == "MAINTENANCE":
        reply_message = maintenance_error(user_id)
    elif not stores:
        reply_message = store_error(user_id)
    else:
        # 使用 LINE SDK v3 对象构建的 Flex Message（已修复结构问题）
        user_id = event.source.user_id
        reply_message = generate_store_buttons(
            user_id,
            get_nearby_stores_alt_text(user_id),
            stores[:35]
        )

    smart_reply(
        event.source.user_id,
        event.reply_token,
        reply_message,
        configuration
    )

# Postback 事件处理
@handler.add(PostbackEvent)
def handle_postback(event):
    """
    处理 Postback 事件

    支持：
    - 公告投票 (action=vote_notice)
    - 其他 Postback 事件（作为文本消息处理）

    注意：PostbackEvent 不包含 message 属性和 mark_as_read_token，
    因为它是按钮点击事件，不是用户发送的消息事件。
    """
    user_id = event.source.user_id
    postback_data = event.postback.data

    logger.info(f"[Postback] user_id={user_id}, data={postback_data}")

    try:
        # 处理公告投票
        if 'action=vote_notice' in postback_data:
            # 解析postback data
            params = dict(param.split('=') for param in postback_data.split('&'))
            action = params.get('action')
            notice_id = params.get('notice_id')
            vote_type = params.get('vote')  # 'support' | 'oppose'

            if action == 'vote_notice' and notice_id and vote_type in ['support', 'oppose']:
                # 验证公告存在且启用投票
                notice = get_notice_by_id(notice_id)
                if not notice:
                    logger.warning(f"[Notice] ⚠ Notice not found: notice_id={notice_id}")
                    return

                if not notice.get('voting_enabled'):
                    logger.warning(f"[Notice] ⚠ Voting not enabled: notice_id={notice_id}")
                    return

                # 记录投票
                success = record_notice_vote(user_id, notice_id, vote_type)

                if success:
                    # 获取统计数据
                    stats = calculate_notice_stats(notice_id)

                    # 获取用户语言
                    lang = get_user_language(user_id)

                    # 构建反馈消息（多语言）
                    vote_success_text = {
                        'ja': f"投票ありがとうございます！\n\n支持: {stats['support_count']}人 ({stats['support_count']/(stats['support_count']+stats['oppose_count'])*100 if stats['support_count']+stats['oppose_count'] > 0 else 0:.1f}%)\n反対: {stats['oppose_count']}人 ({stats['oppose_count']/(stats['support_count']+stats['oppose_count'])*100 if stats['support_count']+stats['oppose_count'] > 0 else 0:.1f}%)",
                        'en': f"Thank you for voting!\n\nSupport: {stats['support_count']} ({stats['support_count']/(stats['support_count']+stats['oppose_count'])*100 if stats['support_count']+stats['oppose_count'] > 0 else 0:.1f}%)\nOppose: {stats['oppose_count']} ({stats['oppose_count']/(stats['support_count']+stats['oppose_count'])*100 if stats['support_count']+stats['oppose_count'] > 0 else 0:.1f}%)",
                        'zh': f"感谢您的投票！\n\n支持: {stats['support_count']}人 ({stats['support_count']/(stats['support_count']+stats['oppose_count'])*100 if stats['support_count']+stats['oppose_count'] > 0 else 0:.1f}%)\n反对: {stats['oppose_count']}人 ({stats['oppose_count']/(stats['support_count']+stats['oppose_count'])*100 if stats['support_count']+stats['oppose_count'] > 0 else 0:.1f}%)"
                    }

                    reply_message = TextMessage(text=vote_success_text.get(lang, vote_success_text['ja']))

                    # 发送回复
                    smart_reply(user_id, event.reply_token, reply_message, configuration, addition=False)

                    logger.info(f"[Notice] ✓ Vote processed: user_id={user_id}, notice_id={notice_id}, vote={vote_type}")
                    return
                else:
                    logger.error(f"[Notice] ✗ Vote failed: user_id={user_id}, notice_id={notice_id}")
                    return

        # 其他Postback事件：走原有的文本命令逻辑
        # 创建一个模拟的 TextMessageContent 对象
        class MockTextMessage:
            def __init__(self, text):
                self.text = text
                self.type = 'text'

        # 创建一个模拟的 MessageEvent 对象
        class MockMessageEvent:
            def __init__(self, original_event, text):
                self.source = original_event.source
                self.reply_token = original_event.reply_token
                self.message = MockTextMessage(text)

        # 创建模拟事件，使用 postback data 作为消息文本
        mock_event = MockMessageEvent(event, postback_data)

        # 检查是否是web任务
        if route_to_web_queue(mock_event):
            return

        # 检查是否是图片生成任务
        if route_to_image_queue(mock_event):
            return

        # 同步处理文本命令（走和 MessageEvent 相同的逻辑）
        handle_sync_text_command(mock_event)

    except Exception as e:
        logger.error(f"[Postback] ✗ Error processing postback: user_id={user_id}, data={postback_data}, error={e}")
        logger.error(traceback.format_exc())


# Follow 事件处理
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    reply_token = event.reply_token

    add_user(user_id)
        
    bind_url = f"https://{DOMAIN}/linebot/sega_bind?token={generate_bind_token(user_id)}"
    buttons_template = ButtonsTemplate(
        title=sega_bind_title_text,
        text=sega_bind_description_text,
        actions=[URIAction(
            label=sega_bind_button_text,
            uri=bind_url
        )]
    )

    reply_message = [
        TextMessage(text=welcome_msg_text),
        TemplateMessage(
            alt_text=sega_bind_alt_text,
            template=buttons_template
        )
    ]

    return smart_reply(user_id, reply_token, reply_message, configuration, False)


# Unfollow 事件处理
@handler.add(UnfollowEvent)
def handle_unfollow(event):
    user_id = event.source.user_id
    logger.info(f"[UnfollowEvent] {user_id} left")
    try:
        track_event('user_unbind', user_id=user_id, metadata={'source': 'line_unfollow'})
    except Exception: pass
    return delete_user(user_id)


# Join 事件处理
@handler.add(JoinEvent)
def handle_join(event):
    reply_token = event.reply_token
    group_id = event.source.group_id
    logger.info(f"[JoinEvent] Joined {group_id}")
    reply_msg = TextMessage(text=welcome_msg_text)
    return smart_reply(None, reply_token, reply_msg, configuration, False)


# MemberJoined 事件处理
@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    reply_token = event.reply_token
    logger.info(f"[MemberJoinedEvent] New Member(s) Joined")
    reply_msg = TextMessage(text=group_welcome_msg_text)
    return smart_reply(None, reply_token, reply_msg, configuration, False)


# Default 事件处理 - 未匹配的事件类型，已读并忽略
@handler.default()
def handle_default(event):
    logger.debug(f"[DefaultHandler] Unhandled event: {event.__class__.__name__}")
    mark_as_read_token = getattr(getattr(event, 'message', None), 'mark_as_read_token', None)
    mark_message_as_read(mark_as_read_token)


# ==================== 管理后台路由 ====================

# 任务队列追踪
task_tracking = {
    'running': [],
    'queued': [],
    'completed': []  # 存储已完成的任务 (最多保留20个)
}
task_tracking_lock = threading.Lock()
MAX_COMPLETED_TASKS = 20  # 最多保留20个已完成任务

# ==================== 辅助函数 ====================

def check_admin_auth():
    """检查管理员是否已登录"""
    return session.get('admin_authenticated', False)

def get_user_nickname_wrapper(user_id, use_cache=True):
    """
    获取用户昵称的wrapper函数
    在main.py中使用,自动传递line_bot_api
    若无法通过LINE API获取昵称,则从用户数据中获取nickname字段
    """
    nickname = None

    # 尝试从LINE API获取昵称
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            nickname = get_user_nickname(user_id, line_bot_api, use_cache)

            # 检查是否为错误消息
            if nickname and ("Unknown" in nickname or "API Error" in nickname or "Blocked" in nickname):
                nickname = None
    except Exception as e:
        logger.debug(f"[User] Failed to get LINE nickname: user_id={user_id}, error={e}")
        nickname = None

    # 如果LINE API失败,尝试从用户数据获取
    if not nickname:
        if user_id in USERS and USERS[user_id].get('nickname'):
            nickname = USERS[user_id].get('nickname')

    return nickname if nickname else f"User {user_id[:8]}..."

@app.route("/admin/panel", methods=["GET", "POST"])
def admin_panel():
    """管理后台主页面"""
    if request.method == "POST":
        # 处理登录
        password = request.form.get("password", "")

        # 验证密码
        if password and password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            session.permanent = True
            return redirect("/admin/panel")
        else:
            return render_template("admin_login.html", error="Invalid password")

    # GET请求
    if not check_admin_auth():
        return render_template("admin_login.html")

    # 准备用户数据 - 不获取昵称,使用懒加载
    users_data = {}
    for user_id, user_info in USERS.items():
        users_data[user_id] = {
            'nickname': 'Loading...',  # 初始占位符
            'json_str': json.dumps(user_info, indent=2, ensure_ascii=False)
        }

    # 获取统计信息
    total_users = len(USERS)
    jp_users = sum(1 for user in USERS.values() if user.get("version") == "jp")
    intl_users = sum(1 for user in USERS.values() if user.get("version") == "intl")

    # 计算运行时长
    uptime = datetime.now() - SERVICE_START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m"

    # 计算百分比
    jp_percent = round((jp_users / total_users * 100) if total_users > 0 else 0, 1)
    intl_percent = round((intl_users / total_users * 100) if total_users > 0 else 0, 1)

    # 获取系统信息
    cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)
    cpu_count = psutil.cpu_count()
    cpu_count_used = round(cpu_percent / 100 * cpu_count, 1)

    memory = psutil.virtual_memory()
    memory_percent = round(memory.percent, 1)
    total_memory = round(memory.total / (1024**3), 1)  # GB
    memory_used_gb = round(memory.used / (1024**3), 1)  # GB

    # 获取线程信息
    thread_count = threading.active_count()

    # 线程安全地读取统计数据
    with stats_lock:
        total_tasks = STATS['tasks_processed']
        total_time = STATS['response_time']

    # 计算平均响应时间
    avg_response = round(total_time / total_tasks if total_tasks > 0 else 0, 1)

    stats = {
        'total_users': total_users,
        'jp_users': jp_users,
        'intl_users': intl_users,
        'jp_percent': jp_percent,
        'intl_percent': intl_percent,
        'cpu_percent': cpu_percent,
        'cpu_count_total': cpu_count,
        'cpu_count_used': cpu_count_used,
        'memory_percent': memory_percent,
        'memory_used_gb': memory_used_gb,
        'total_memory': total_memory,
        'uptime': uptime_str,
        'python_version': platform.python_version(),
        'platform': f"{platform.system()} {platform.release()}",
        'platform_short': platform.system(),
        'hostname': socket.gethostname(),
        'port': PORT,
        'image_queue_size': image_queue.qsize(),
        'web_queue_size': webtask_queue.qsize(),
        'max_queue_size': MAX_QUEUE_SIZE,
        'thread_count': thread_count,
        'total_tasks_processed': total_tasks,
        'avg_response_time': avg_response,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 合并业务指标（?refresh=<任何值> 跳过 30s 缓存）
    force_refresh = bool(request.args.get('refresh'))
    stats.update(get_business_stats(force_refresh=force_refresh))

    # 读取日志
    logs = ""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = ''.join(f.readlines()[-100:])
    except Exception as e:
        logs = f"Error reading logs: {e}"

    return render_template(
        "admin_panel.html",
        users_data=users_data,
        total_users=total_users,
        stats=stats,
        logs=logs
    )

@app.route("/admin/logout", methods=["GET"])
def admin_logout():
    """管理员登出"""
    session.pop('admin_authenticated', None)
    return redirect("/admin/panel")

@app.route("/admin/api/hourly", methods=["GET"])
def admin_api_hourly():
    """获取指定日期的小时分布数据"""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    date_str = request.args.get("date", "")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400
    return jsonify(get_hourly_stats(date_str))

@app.route("/admin/trigger_update", methods=["POST"])
@csrf.exempt
def admin_trigger_update():
    """触发指定用户的maimai_update"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    try:
        # 创建一个模拟的event对象用于异步任务
        class MockEvent:
            def __init__(self, user_id):
                self.source = type('obj', (object,), {'user_id': user_id})()
                self.reply_token = None

        mock_event = MockEvent(user_id)

        # 生成任务ID
        task_id = f"admin_update_{user_id}_{datetime.now().timestamp()}"

        # 获取用户昵称用于显示
        nickname = get_user_nickname_wrapper(user_id, use_cache=True)

        # 添加到任务追踪（在入队之前）
        with task_tracking_lock:
            task_tracking['queued'].append({
                'id': task_id,
                'function': 'async_admin_maimai_update_task',
                'queue_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': user_id,
                'nickname': nickname
            })

        # 添加到webtask队列（使用3元组格式）
        webtask_queue.put_nowait((async_admin_maimai_update_task, (mock_event,), task_id))

        return jsonify({
            'success': True,
            'message': f'Update task queued for user {user_id}'
        })
    except queue.Full:
        return jsonify({
            'success': False,
            'message': 'Task queue is full'
        }), 503
    except Exception as e:
        logger.error(f"[Admin] ✗ Trigger update error: user_id={user_id}, error={e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/get_logs", methods=["GET"])
def admin_get_logs():
    """获取最新日志"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = ''.join(f.readlines()[-100:])
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'logs': f'Error reading logs: {e}'})

@app.route("/admin/get_notices", methods=["GET"])
def admin_get_notices():
    """获取所有公告(包括草稿)"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        notices = get_all_notices(include_drafts=True)
        return jsonify({'success': True, 'notices': notices})
    except Exception as e:
        logger.error(f"[Admin] ✗ Get notices error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/create_notice", methods=["POST"])
@csrf.exempt
def admin_create_notice():
    """创建新公告 - 支持多语言、草稿、投票"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    # 多语言内容
    content_zh = data.get('content_zh', '').strip()
    content_ja = data.get('content_ja', '').strip()
    content_en = data.get('content_en', '').strip()

    # 验证至少填写一种语言
    if not any([content_ja, content_en, content_zh]):
        return jsonify({'success': False, 'message': 'At least one language content is required'}), 400

    # 构建多语言内容对象
    content_dict = {
        'zh': content_zh,
        'ja': content_ja,
        'en': content_en,
    }

    # 获取其他参数
    status = data.get('status', 'published')  # 'draft' | 'published'
    voting_enabled = data.get('voting_enabled', False)
    created_by = session.get('user_id', 'admin')

    # 按钮参数
    button_type = data.get('button_type')
    button_label_zh = data.get('button_label_zh', '').strip()
    button_label_ja = data.get('button_label_ja', '').strip()
    button_label_en = data.get('button_label_en', '').strip()
    button_value = data.get('button_value', '').strip()

    # 构建按钮标签字典
    button_label = None
    if button_type and button_value:
        button_label = {
            'zh': button_label_zh,
            'ja': button_label_ja,
            'en': button_label_en
        }

    try:
        notice_id = upload_notice(
            content=content_dict,
            status=status,
            voting_enabled=voting_enabled,
            created_by=created_by,
            button_type=button_type,
            button_label=button_label,
            button_value=button_value
        )

        # 仅发布状态的公告才清除阅读状态
        if status == 'published':
            clear_notice_read_status(notice_id)
            logger.info(f"[Admin] ✓ Notice published: notice_id={notice_id}")
        else:
            logger.info(f"[Admin] ✓ Notice saved as draft: notice_id={notice_id}")

        return jsonify({
            'success': True,
            'message': f'Notice {"published" if status == "published" else "saved as draft"} successfully',
            'notice_id': notice_id
        })
    except Exception as e:
        logger.error(f"[Admin] ✗ Create notice error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/update_notice", methods=["POST"])
@csrf.exempt
def admin_update_notice():
    """更新公告 - 支持多语言"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    notice_id = data.get('notice_id')

    # 多语言内容
    content_zh = data.get('content_zh', '').strip()
    content_ja = data.get('content_ja', '').strip()
    content_en = data.get('content_en', '').strip()

    if not notice_id or not any([content_ja, content_en, content_zh]):
        return jsonify({'success': False, 'message': 'Notice ID and at least one language content are required'}), 400

    content_dict = {
        'zh': content_zh,
        'ja': content_ja,
        'en': content_en,
    }

    # 按钮参数
    button_type = data.get('button_type')
    button_label_zh = data.get('button_label_zh', '').strip()
    button_label_ja = data.get('button_label_ja', '').strip()
    button_label_en = data.get('button_label_en', '').strip()
    button_value = data.get('button_value', '').strip()
    remove_button = data.get('remove_button', False)

    # 构建按钮标签字典
    button_label = None
    if button_type and button_value:
        button_label = {
            'zh': button_label_zh,
            'ja': button_label_ja,
            'en': button_label_en
        }

    try:
        # 检查是否为最新已发布公告
        latest_notice = get_latest_published_notice()
        is_latest = latest_notice and latest_notice.get('id') == notice_id

        success = update_notice(
            notice_id,
            content_dict,
            button_type=button_type,
            button_label=button_label,
            button_value=button_value,
            remove_button=remove_button
        )

        if success:
            notice = get_notice_by_id(notice_id)
            # 如果修改的是已发布的公告,清除阅读状态
            if notice.get('status') == 'published' and is_latest:
                clear_notice_read_status(notice_id)
                logger.info(f"[Admin] ✓ Updated latest published notice: notice_id={notice_id}")
            else:
                logger.info(f"[Admin] ✓ Updated notice: notice_id={notice_id}")

            return jsonify({'success': True, 'message': 'Notice updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Notice not found'}), 404

    except Exception as e:
        logger.error(f"[Admin] ✗ Update notice error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/delete_notice", methods=["POST"])
@csrf.exempt
def admin_delete_notice():
    """删除公告"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    notice_id = data.get('notice_id')

    if not notice_id:
        return jsonify({'success': False, 'message': 'Notice ID is required'}), 400

    try:
        clear_notice_record(notice_id)
        success = delete_notice(notice_id)

        if success:
            logger.info(f"[Admin] ✓ Notice deleted: notice_id={notice_id}")
            return jsonify({'success': True, 'message': 'Notice deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Notice not found'}), 404

    except Exception as e:
        logger.error(f"[Admin] ✗ Delete notice error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/publish_notice", methods=["POST"])
@csrf.exempt
def admin_publish_notice():
    """发布草稿公告"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    notice_id = data.get('notice_id')

    if not notice_id:
        return jsonify({'success': False, 'message': 'Notice ID is required'}), 400

    try:
        success = publish_notice(notice_id)

        if success:
            # 清除所有用户的阅读状态
            clear_notice_read_status(notice_id)
            logger.info(f"[Admin] ✓ Published draft notice: notice_id={notice_id}")
            return jsonify({'success': True, 'message': 'Notice published successfully'})
        else:
            return jsonify({'success': False, 'message': 'Notice not found or already published'}), 404

    except Exception as e:
        logger.error(f"[Admin] ✗ Publish notice error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/get_notice_stats", methods=["GET"])
def admin_get_notice_stats():
    """获取公告统计数据"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    notice_id = request.args.get('notice_id')

    try:
        if notice_id:
            # 获取单个公告的统计
            stats = calculate_notice_stats(notice_id)
            if stats is None:
                return jsonify({'success': False, 'message': 'Notice not found'}), 404
            return jsonify({'success': True, 'stats': stats})
        else:
            # 获取所有公告的统计
            stats = get_all_notices_stats()
            return jsonify({'success': True, 'stats': stats})

    except Exception as e:
        logger.error(f"[Admin] ✗ Get notice stats error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/linebot/notice_vote", methods=["POST"])
@csrf.exempt
def notice_vote():
    """
    用户投票端点
    通过 LINE LIFF 或 Postback 调用
    """
    data = request.get_json()
    user_id = data.get('user_id')
    notice_id = data.get('notice_id')
    vote_type = data.get('vote_type')  # 'support' | 'oppose'

    if not all([user_id, notice_id, vote_type]):
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400

    if vote_type not in ['support', 'oppose']:
        return jsonify({'success': False, 'message': 'Invalid vote type'}), 400

    try:
        # 验证公告存在且启用投票
        notice = get_notice_by_id(notice_id)
        if not notice:
            return jsonify({'success': False, 'message': 'Notice not found'}), 404

        if not notice.get('voting_enabled'):
            return jsonify({'success': False, 'message': 'Voting is not enabled for this notice'}), 400

        # 记录投票
        success = record_notice_vote(user_id, notice_id, vote_type)

        if success:
            # 返回最新统计
            stats = calculate_notice_stats(notice_id)
            logger.info(f"[Notice] ✓ User voted: user_id={user_id}, notice_id={notice_id}, vote={vote_type}")
            return jsonify({
                'success': True,
                'message': 'Vote recorded successfully',
                'stats': stats
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to record vote'}), 500

    except Exception as e:
        logger.error(f"[Notice] ✗ Vote error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== Tip/Ad 管理 API ====================

@app.route("/admin/tip_ads", methods=["GET"])
def admin_get_tip_ads():
    """获取所有 tip/ad"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        tip_ads = get_all_tip_ads()
        return jsonify({'success': True, 'tip_ads': tip_ads})
    except Exception as e:
        logger.error(f"[Admin] ✗ Get tip/ads error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/tip_ads/<tip_ad_id>", methods=["GET"])
def admin_get_tip_ad(tip_ad_id):
    """获取单个 tip/ad"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        tip_ad = get_tip_ad_by_id(tip_ad_id)
        return jsonify({'success': True, 'tip_ad': tip_ad})
    except Exception as e:
        logger.error(f"[Admin] ✗ Get tip/ads by id error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/tip_ads", methods=["POST"])
@csrf.exempt
def admin_create_tip_ads():
    """创建新的 tip/ad"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    tip_type = data.get('type')
    text_zh = data.get('text_zh')
    text_en = data.get('text_en')
    text_ja = data.get('text_ja')
    button_type = data.get('button_type')
    button_label_zh = data.get('button_label_zh')
    button_label_en = data.get('button_label_en')
    button_label_ja = data.get('button_label_ja')
    button_value = data.get('button_value')
    enabled = data.get('enabled', True)

    if not all([tip_type, text_zh, text_en, text_ja]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    if tip_type not in ['tip', 'ad']:
        return jsonify({'success': False, 'message': 'Invalid type'}), 400

    try:
        tip_ad = create_tip_ad(
            tip_type=tip_type,
            text_zh=text_zh,
            text_en=text_en,
            text_ja=text_ja,
            button_type=button_type,
            button_label_zh=button_label_zh,
            button_label_en=button_label_en,
            button_label_ja=button_label_ja,
            button_value=button_value,
            enabled=enabled
        )
        logger.info(f"[Admin] ✓ Created tip/ad: id={tip_ad['id']}, type={tip_type}")
        return jsonify({'success': True, 'tip_ad': tip_ad})
    except Exception as e:
        logger.error(f"[Admin] ✗ Create tip/ad error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/tip_ads/<tip_ad_id>", methods=["PUT"])
@csrf.exempt
def admin_put_tip_ads(tip_ad_id):
    """更新 tip/ad"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    if not tip_ad_id:
        return jsonify({'success': False, 'message': 'Missing id'}), 400

    tip_type = data.get('type')
    text_zh = data.get('text_zh')
    text_en = data.get('text_en')
    text_ja = data.get('text_ja')
    button_type = data.get('button_type')
    button_label_zh = data.get('button_label_zh')
    button_label_en = data.get('button_label_en')
    button_label_ja = data.get('button_label_ja')
    button_value = data.get('button_value')
    enabled = data.get('enabled')
    remove_button = data.get('remove_button', False)

    try:
        tip_ad = update_tip_ad(
            tip_ad_id=tip_ad_id,
            tip_type=tip_type,
            text_zh=text_zh,
            text_en=text_en,
            text_ja=text_ja,
            button_type=button_type,
            button_label_zh=button_label_zh,
            button_label_en=button_label_en,
            button_label_ja=button_label_ja,
            button_value=button_value,
            enabled=enabled,
            remove_button=remove_button
        )

        if tip_ad:
            logger.info(f"[Admin] ✓ Updated tip/ad: id={tip_ad_id}")
            return jsonify({'success': True, 'tip_ad': tip_ad})
        else:
            return jsonify({'success': False, 'message': 'Tip/ad not found'}), 404
    except Exception as e:
        logger.error(f"[Admin] ✗ Update tip/ad error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/tip_ads/<tip_ad_id>", methods=["DELETE"])
@csrf.exempt
def admin_delete_tip_ads(tip_ad_id):
    """删除 tip/ad"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    if not tip_ad_id:
        return jsonify({'success': False, 'message': 'Missing id'}), 400

    try:
        success = delete_tip_ad(tip_ad_id)
        if success:
            logger.info(f"[Admin] ✓ Deleted tip/ad: id={tip_ad_id}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Tip/ad not found'}), 404
    except Exception as e:
        logger.error(f"[Admin] ✗ Delete tip/ad error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 背景图管理 API ====================

@app.route("/admin/backgrounds", methods=["GET", "POST"])
@csrf.exempt
def admin_backgrounds():
    """
    背景图资源

    GET:  列出所有背景图
    POST: 上传新背景图（multipart/form-data, field: file）
    """
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == "GET":
        try:
            files = []
            for f in sorted(os.listdir(BG_DIR)):
                if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    continue
                filepath = os.path.join(BG_DIR, f)
                size_bytes = os.path.getsize(filepath)
                if size_bytes < 1024:
                    size_str = f"{size_bytes}B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f}KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f}MB"
                files.append({
                    'name': f,
                    'size': size_str,
                    'is_user': _is_user_custom_bg(f),
                })
            return jsonify({'success': True, 'files': files})
        except Exception as e:
            logger.error(f"[Admin] ✗ List backgrounds error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    # POST: 上传
    uploaded = request.files.get('file')
    if not uploaded or not uploaded.filename:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    original_name = uploaded.filename
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in {'.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif'}:
        return jsonify({'success': False, 'message': 'Unsupported format. Only PNG/JPG/WebP/HEIC.'}), 400

    file_data = uploaded.read()
    if len(file_data) > 10 * 1024 * 1024:
        return jsonify({'success': False, 'message': 'File too large (max 10MB)'}), 400

    try:
        from PIL import Image as PILImage
        from io import BytesIO
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass
        img = PILImage.open(BytesIO(file_data))
        img.load()
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid or corrupted image file'}), 400

    safe_name = os.path.splitext(os.path.basename(original_name))[0] + ext
    if not safe_name or safe_name.startswith('.'):
        return jsonify({'success': False, 'message': 'Invalid filename'}), 400

    # HEIC/HEIF 转换为 WebP 保存
    if ext in {'.heic', '.heif'}:
        safe_name = os.path.splitext(safe_name)[0] + '.webp'
        save_path = os.path.join(BG_DIR, safe_name)
        try:
            img = img.convert("RGB")
            img.save(save_path, "WEBP", quality=85)
        except Exception as e:
            logger.error(f"[Admin] ✗ HEIC conversion error: {e}")
            return jsonify({'success': False, 'message': 'Failed to convert HEIC'}), 500
    else:
        save_path = os.path.join(BG_DIR, safe_name)
        try:
            with open(save_path, 'wb') as f:
                f.write(file_data)
        except Exception as e:
            logger.error(f"[Admin] ✗ Upload background error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    logger.info(f"[Admin] ✓ Uploaded background: {safe_name}")
    return jsonify({'success': True, 'filename': safe_name}), 201


@app.route("/admin/backgrounds/<filename>", methods=["DELETE"])
@csrf.exempt
def admin_delete_background(filename):
    """删除指定背景图"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    safe_name = os.path.basename(filename)
    filepath = os.path.join(BG_DIR, safe_name)

    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': 'File not found'}), 404

    try:
        os.remove(filepath)
        logger.info(f"[Admin] ✓ Deleted background: {safe_name}")

        for uid, udata in USERS.items():
            user_bg_list = udata.get('bg_files', [])
            if safe_name in user_bg_list:
                user_bg_list.remove(safe_name)
                edit_user_value(uid, 'bg_files', user_bg_list)

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"[Admin] ✗ Delete background error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 用户管理 API ====================

@app.route("/admin/edit_user", methods=["POST"])
@csrf.exempt
def admin_edit_user():
    """编辑用户数据"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = data.get('user_id')
    user_data = data.get('user_data')

    if not user_id or user_data is None:
        return jsonify({
            'success': False,
            'message': 'User ID and user data required'
        }), 400

    try:
        if user_id not in USERS:
            return jsonify({
                'success': False,
                'message': f'User {user_id} not found'
            }), 404

        # 更新用户数据
        USERS[user_id] = user_data
        mark_user_dirty()

        logger.info(f"[Admin] ✓ User data edited: user_id={user_id}")

        # 不再发送通知给管理员

        return jsonify({
            'success': True,
            'message': 'User data updated successfully'
        })

    except Exception as e:
        logger.error(f"[Admin] ✗ Edit user error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/delete_user", methods=["POST"])
@csrf.exempt
def admin_delete_user():
    """删除用户"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({
            'success': False,
            'message': 'User ID required'
        }), 400

    try:
        if user_id not in USERS:
            return jsonify({
                'success': False,
                'message': f'User {user_id} not found'
            }), 404

        # 使用 delete_user 函数删除用户
        delete_user(user_id)

        logger.info(f"[Admin] ✓ User deleted: user_id={user_id}")

        return jsonify({
            'success': True,
            'message': f'User {user_id} deleted successfully'
        })

    except Exception as e:
        logger.error(f"[Admin] ✗ Delete user error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/clear_cache", methods=["POST"])
@csrf.exempt
def admin_clear_cache():
    """清除昵称缓存"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        with nickname_cache_lock:
            cache_size = len(nickname_cache)
            nickname_cache.clear()

        logger.info(f"[Admin] ✓ Nickname cache cleared: entries={cache_size}")

        return jsonify({
            'success': True,
            'message': f'Cache cleared ({cache_size} entries)'
        })

    except Exception as e:
        logger.error(f"[Admin] ✗ Clear cache error: error={e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/get_user_data", methods=["POST"])
@csrf.exempt
def admin_get_user_data():
    """获取单个用户的最新数据"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({
            'success': False,
            'message': 'User ID required'
        }), 400

    try:
        if user_id not in USERS:
            return jsonify({
                'success': False,
                'message': f'User {user_id} not found'
            }), 404

        # 获取用户数据
        user_info = USERS[user_id]

        # 获取昵称(不使用缓存,强制刷新)
        nickname = get_user_nickname_wrapper(user_id, use_cache=False)

        # 格式化 JSON
        json_str = json.dumps(user_info, indent=2, ensure_ascii=False)

        return jsonify({
            'success': True,
            'nickname': nickname,
            'json_str': json_str,
            'user_data': user_info
        })

    except Exception as e:
        logger.error(f"[Admin] ✗ Get user data error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/load_nicknames", methods=["POST"])
@csrf.exempt
def admin_load_nicknames():
    """批量加载用户昵称"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取所有用户的昵称
        nicknames = {}
        for user_id in USERS.keys():
            nickname = get_user_nickname_wrapper(user_id, use_cache=True)
            nicknames[user_id] = nickname

        return jsonify({
            'success': True,
            'nicknames': nicknames,
            'count': len(nicknames)
        })

    except Exception as e:
        logger.error(f"[Admin] ✗ Load nicknames error: error={e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/backups", methods=["POST"])
def admin_create_backup():
    """从管理面板创建系统备份"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        db_config = {
            'host': DB_HOST,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'database': DB_NAME
        }

        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        success, message, backup_path = create_backup(
            users_data=USERS,
            config_data=config_data,
            db_config=db_config,
            backup_password=ADMIN_PASSWORD,
        )

        return jsonify({'success': success, 'message': message})
    except Exception as e:
        logger.error(f"[Admin] ✗ Create backup error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})


@app.route("/admin/get_backups", methods=["GET"])
def admin_get_backups():
    """获取所有备份文件列表"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        backup_files = []

        # 扫描备份目录
        if os.path.exists(BACKUP_DIR):
            for filename in os.listdir(BACKUP_DIR):
                if filename.startswith("backup_") and filename.endswith(".zip"):
                    filepath = os.path.join(BACKUP_DIR, filename)
                    stat = os.stat(filepath)

                    backup_files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'created_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': stat.st_mtime
                    })

        # 按时间倒序排序（最新的在前）
        backup_files.sort(key=lambda x: x['timestamp'], reverse=True)

        return jsonify({
            'success': True,
            'backups': backup_files,
            'count': len(backup_files)
        })

    except Exception as e:
        logger.error(f"[Admin] ✗ Get backups error: error={e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/download_backup", methods=["GET"])
def admin_download_backup():
    """下载指定的备份文件"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        filename = request.args.get('file')
        if not filename:
            return jsonify({
                'success': False,
                'message': 'Missing file parameter'
            }), 400

        # 安全检查：只允许备份文件
        if not filename.startswith("backup_") or not filename.endswith(".zip"):
            return jsonify({
                'success': False,
                'message': 'Invalid backup filename'
            }), 400

        # 防止路径遍历攻击
        if ".." in filename or "/" in filename or "\\" in filename:
            return jsonify({
                'success': False,
                'message': 'Invalid filename'
            }), 400

        backup_path = os.path.join(BACKUP_DIR, filename)

        # 检查文件是否存在
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'message': 'Backup file not found'
            }), 404

        # 发送文件
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )

    except Exception as e:
        logger.error(f"[Admin] ✗ Download backup error: file={filename}, error={e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/delete_backup", methods=["POST"])
@csrf.exempt
def admin_delete_backup():
    """删除指定的备份文件"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({
                'success': False,
                'message': 'Missing filename parameter'
            }), 400

        # 安全检查：只允许备份文件
        if not filename.startswith("backup_") or not filename.endswith(".zip"):
            return jsonify({
                'success': False,
                'message': 'Invalid backup filename'
            }), 400

        # 防止路径遍历攻击
        if ".." in filename or "/" in filename or "\\" in filename:
            return jsonify({
                'success': False,
                'message': 'Invalid filename'
            }), 400

        backup_path = os.path.join(BACKUP_DIR, filename)

        # 检查文件是否存在
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'message': 'Backup file not found'
            }), 404

        # 删除文件
        os.remove(backup_path)
        logger.info(f"[Admin] ✓ Backup deleted: file={filename}")

        return jsonify({
            'success': True,
            'message': f'Backup {filename} deleted successfully'
        })

    except Exception as e:
        logger.error(f"[Admin] ✗ Delete backup error: error={e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/admin/dxdata_status", methods=["GET"])
def admin_dxdata_status():
    """获取 DXData 状态（歌曲数、谱面数、版本数）"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        songs, versions = read_dxdata()
        # 统计歌曲数
        total_songs = len(songs)
        std_songs = len([s for s in songs if s['type'] == 'std'])
        dx_songs = len([s for s in songs if s['type'] == 'dx'])
        utage_songs = len([s for s in songs if s['type'] == 'utage'])

        # 统计谱面数（不包括宴会曲）
        total_sheets = 0
        jp_sheets = 0
        intl_sheets = 0

        for song in songs:
            if song['type'] == 'utage':
                continue
            for sheet in song['sheets']:
                total_sheets += 1
                if sheet['regions'].get('jp', False):
                    jp_sheets += 1
                if sheet['regions'].get('intl', False):
                    intl_sheets += 1

        total_versions = len(versions)
        version_names = [v.get('abbr', '') for v in versions]

        return jsonify({
            'songs': {
                'total': total_songs,
                'std': std_songs,
                'dx': dx_songs,
                'utage': utage_songs
            },
            'sheets': {
                'total': total_sheets,
                'jp': jp_sheets,
                'intl': intl_sheets
            },
            'versions': total_versions,
            'version_names': version_names
        })

    except Exception as e:
        logger.error(f"[Admin] ✗ DXData status error: error={e}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500

@app.route("/admin/update_dxdata", methods=["POST"])
@csrf.exempt
def admin_update_dxdata():
    """触发 DXData 更新"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        result = update_dxdata_with_comparison(DXDATA_URL, DXDATA_FILE)
        message = build_dxdata_update_message(result, None)
        diff = result.get('diff', {})
        return jsonify({
            'success': True,
            'message': message,
            'sheets_added': diff.get('sheets_added', 0),
            'songs_added': diff.get('songs_added', 0)
        })
    except Exception as e:
        logger.error(f"[Admin] ✗ Update DXData error: error={e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/admin/notifications", methods=["GET"])
def admin_get_notifications():
    """获取所有系统通知"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify(get_notifications())


@app.route("/admin/notifications", methods=["DELETE"])
def admin_clear_notifications():
    """清空所有系统通知"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    clear_notifications()
    return jsonify({'success': True})


@app.route("/admin/vapid-public-key", methods=["GET"])
def admin_vapid_public_key():
    """返回 VAPID 公钥（前端订阅 push 时使用）"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    return VAPID_PUBLIC_KEY, 200, {'Content-Type': 'text/plain'}


@app.route("/admin/push-subscription", methods=["POST"])
def admin_add_push_subscription():
    """保存浏览器 push 订阅"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    sub = request.get_json()
    if not sub or not sub.get('endpoint'):
        return jsonify({'error': 'Invalid subscription'}), 400

    add_push_subscription(sub)
    return jsonify({'success': True})


@app.route("/admin/push-subscription", methods=["DELETE"])
def admin_remove_push_subscription():
    """删除浏览器 push 订阅"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    endpoint = data.get('endpoint') if data else None
    if not endpoint:
        return jsonify({'error': 'Missing endpoint'}), 400

    remove_push_subscription(endpoint)
    return jsonify({'success': True})


# ==================== Admin DevToken Management ====================

@app.route("/admin/devtokens", methods=["GET"])
def admin_list_devtokens():
    """获取所有开发者 token 列表"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        tokens = list_dev_tokens()
        # 补充 allowed_users 数量
        all_tokens = load_dev_tokens()
        for t in tokens:
            token_data = all_tokens.get(t['token_id'], {})
            t['allowed_users_count'] = len(token_data.get('allowed_users', []))
        return jsonify({'success': True, 'tokens': tokens})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route("/admin/devtokens", methods=["POST"])
def admin_create_devtoken():
    """创建新的开发者 token"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    note = data.get('note', '').strip() if data else ''
    if not note:
        return jsonify({'success': False, 'message': 'Note is required'})

    result = create_dev_token(note, created_by='admin')
    if result:
        return jsonify({
            'success': True,
            'token_id': result['token_id'],
            'token': result['token']
        })
    return jsonify({'success': False, 'message': 'Failed to create token'})


@app.route("/admin/devtokens/<token_id>", methods=["PATCH"])
def admin_update_devtoken(token_id):
    """更新开发者 token 状态（如撤销）"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if data and data.get('revoked'):
        if revoke_dev_token(token_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Token not found'})

    return jsonify({'success': False, 'message': 'No valid fields to update'})


@app.route("/admin/devtokens/<token_id>", methods=["DELETE"])
def admin_delete_devtoken(token_id):
    """删除开发者 token"""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    tokens = load_dev_tokens()
    if token_id not in tokens:
        return jsonify({'success': False, 'message': 'Token not found'})

    del tokens[token_id]
    save_dev_tokens(tokens, force=True)
    return jsonify({'success': True})


# ==================== 开发者 API ====================

@app.route("/api/v2/users", methods=["GET"])
@app.route("/api/v1/users", methods=["GET"])
@csrf.exempt
@require_dev_token
def api_list_users():
    """
    获取所有用户列表 API

    需要 Bearer Token 认证

    返回该 token 有权限访问的所有用户（包括创建的用户和授权访问的用户）
    """
    try:
        token_info = request.token_info
        token_id = token_info['token_id']

        # 获取 token 的 allowed_users 列表
        dev_tokens = load_dev_tokens()
        allowed_users = dev_tokens.get(token_id, {}).get('allowed_users', [])

        users_list = []
        for user_id in USERS.keys():
            # 检查是否有访问权限（创建的用户或授权访问的用户）
            has_access = False
            access_type = None

            if 'registered_via_token' in USERS[user_id] and USERS[user_id]['registered_via_token'] == token_id:
                has_access = True
                access_type = "owner"
            elif user_id in allowed_users:
                has_access = True
                access_type = "granted"

            if has_access:
                nickname = get_user_nickname_wrapper(user_id, use_cache=True)
                users_list.append({
                    "user_id": user_id,
                    "nickname": nickname,
                    "access_type": access_type
                })

        # 记录 API 访问日志
        logger.info(f"[API] List users: token_id={token_id}, note={token_info['note']}, count={len(users_list)}")

        return jsonify({
            "success": True,
            "count": len(users_list),
            "users": users_list
        })

    except Exception as e:
        logger.error(f"[API] ✗ List users error: error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v2/users", methods=["POST"])
@app.route("/api/v1/users", methods=["POST"])
@csrf.exempt
@require_dev_token
def api_create_user():
    """
    创建用户 API (RESTful) - 生成绑定链接

    需要 Bearer Token 认证

    请求体 (JSON):
    - user_id: 必需，用户ID
    - nickname: 必需，用户昵称

    返回:
    - bind_url: 绑定页面链接
    - token: 绑定 token（2分钟有效）
    - expires_in: token 过期时间（秒）
    """
    user_id = ''
    try:
        # 获取请求数据（支持 JSON body 和 form data）
        data = request.form.to_dict() or request.get_json(force=True, silent=True) or {}
        user_id = data.get('user_id', '')
        nickname = data.get('nickname', '')

        # user_id 是必需参数
        if not user_id:
            return jsonify({
                "error": "Missing parameter",
                "message": "Parameter 'user_id' is required"
            }), 400

        # nickname 是必需参数
        if not nickname:
            return jsonify({
                "error": "Missing parameter",
                "message": "Parameter 'nickname' is required"
            }), 400

        # 记录 API 访问日志
        token_info = request.token_info
        logger.info(f"[API] Create user: user_id={user_id}, nickname={nickname}, token_id={token_info['token_id']}, note={token_info['note']}")

        # 读取用户数据
        if user_id in USERS:
            return jsonify({
                "error": "User already exists",
                "message": f"User {user_id} was created already."
            }), 409

        # 生成绑定 token
        bind_token = generate_bind_token(user_id)

        # 构建绑定 URL
        bind_url = f"https://{DOMAIN}/linebot/sega_bind?token={bind_token}"

        # 初始化用户数据
        add_user(user_id)
        edit_user_value(user_id, "nickname", nickname)
        edit_user_value(user_id, "registered_via_token", token_info['token_id'])
        edit_user_value(user_id, "registered_at", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        logger.info(f"[API] ✓ User created: user_id={user_id}, token_id={token_info['token_id']}")

        return jsonify({
            "success": True,
            "user_id": user_id,
            "nickname": nickname,
            "bind_url": bind_url,
            "token": bind_token,
            "expires_in": 120,
            "message": "Bind URL generated successfully."
        }), 201

    except Exception as e:
        logger.error(f"[API] ✗ Create user error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v2/users/<user_id>", methods=["GET"])
@app.route("/api/v1/users/<user_id>", methods=["GET"])
@csrf.exempt
@require_dev_token
@require_user_permission
def api_get_user(user_id):
    """
    获取用户信息 API

    需要 Bearer Token 认证并拥有该用户的访问权限
    """
    try:
        user_data = USERS[user_id]
        nickname = get_user_nickname_wrapper(user_id, use_cache=True)

        # 记录 API 访问日志
        token_info = request.token_info
        logger.info(f"[API] Get user: user_id={user_id}, token_id={token_info['token_id']}, note={token_info['note']}")

        # 过滤敏感字段
        sensitive_keys = {'sega_id', 'sega_pwd', 'perm_requests', 'registered_via_token'}
        safe_data = {k: v for k, v in user_data.items() if k not in sensitive_keys}

        return jsonify({
            "success": True,
            "user_id": user_id,
            "nickname": nickname,
            "data": safe_data
        })

    except Exception as e:
        logger.error(f"[API] ✗ Get user error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v2/users/<user_id>", methods=["DELETE"])
@app.route("/api/v1/users/<user_id>", methods=["DELETE"])
@csrf.exempt
@require_dev_token
@require_owner_permission
def api_delete_user(user_id):
    """
    删除用户 API

    需要 Bearer Token 认证（该 token 必须是用户的创建者）
    """
    try:
        # 获取用户信息用于日志
        nickname = get_user_nickname_wrapper(user_id, use_cache=True)

        # 删除用户
        delete_user(user_id)

        # 记录 API 访问日志
        token_info = request.token_info
        logger.info(f"[API] Delete user: user_id={user_id}, nickname={nickname}, token_id={token_info['token_id']}, note={token_info['note']}")
        track_event('user_unbind', user_id=user_id, metadata={'token_id': token_info['token_id']})

        return jsonify({
            "success": True,
            "user_id": user_id,
            "message": f"User {user_id} has been deleted successfully"
        })

    except Exception as e:
        logger.error(f"[API] ✗ Delete user error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v2/users/<user_id>/rebind-url", methods=["GET"])
@app.route("/api/v1/users/<user_id>/rebind-url", methods=["GET"])
@csrf.exempt
@require_dev_token
@require_user_permission
def api_create_rebind_url(user_id):
    """
    生成换绑 URL API

    需要 Bearer Token 认证并拥有该用户的访问权限

    返回:
    - rebind_url: 绑定页面链接（2分钟有效）
    - expires_in: token 过期时间（秒）
    """
    try:
        token_info = request.token_info
        logger.info(f"[API] Create rebind URL: user_id={user_id}, token_id={token_info['token_id']}, note={token_info['note']}")

        rebind_token = generate_bind_token(user_id)
        rebind_url = f"https://{DOMAIN}/linebot/sega_bind?token={rebind_token}&mode=rebind"

        return jsonify({
            "success": True,
            "user_id": user_id,
            "rebind_url": rebind_url,
            "expires_in": 120,
            "message": "Rebind URL generated successfully."
        }), 201

    except Exception as e:
        logger.error(f"[API] ✗ Create rebind URL error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v2/users/<user_id>/settings-url", methods=["GET"])
@app.route("/api/v1/users/<user_id>/settings-url", methods=["GET"])
@csrf.exempt
@require_dev_token
@require_user_permission
def api_create_settings_url(user_id):
    """
    生成设置 URL API

    需要 Bearer Token 认证并拥有该用户的访问权限

    返回:
    - settings_url: 绑定页面链接（2分钟有效）
    - expires_in: token 过期时间（秒）
    """
    try:
        token_info = request.token_info
        logger.info(f"[API] Create settings URL: user_id={user_id}, token_id={token_info['token_id']}, note={token_info['note']}")

        settings_token = generate_settings_token(user_id)
        settings_url = f"https://{DOMAIN}/linebot/settings?token={settings_token}"

        return jsonify({
            "success": True,
            "user_id": user_id,
            "settings_url": settings_url,
            "expires_in": 1800,
            "message": "Settings URL generated successfully."
        }), 201

    except Exception as e:
        logger.error(f"[API] ✗ Create settings URL error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v2/users/<user_id>/bind", methods=["POST"])
@csrf.exempt
@require_dev_token
@require_user_permission
def api_bind_user(user_id):
    """
    绑定 SEGA 账号 API

    需要 Bearer Token 认证并拥有该用户的访问权限

    请求体 (JSON / form-data):
    - sega_id: 必需，SEGA ID
    - password: 必需，密码
    - ver: 服务器版本 jp/intl（默认 jp）
    - aime: Aime卡选择（默认 0，仅jp有效）
    - timezone: 时区偏移（默认 9）
    - language: 语言 ja/en/zh（默认 en）
    """
    try:
        token_info = request.token_info
        data = request.form.to_dict() or request.get_json(force=True, silent=True) or {}

        sega_id = data.get('sega_id', '')
        password = data.get('password', '')
        ver = data.get('ver', 'jp').strip().lower()
        aime = data.get('aime', '0')
        timezone = data.get('timezone', '9')
        language = data.get('language', 'en').strip().lower()

        if not sega_id:
            return jsonify({"error": "Missing parameter", "message": "Parameter 'sega_id' is required"}), 400
        if not password:
            return jsonify({"error": "Missing parameter", "message": "Parameter 'password' is required"}), 400
        if ver not in ('jp', 'intl'):
            return jsonify({"error": "Invalid parameter", "message": "Parameter 'ver' must be jp or intl"}), 400
        if language not in ('ja', 'en', 'zh'):
            language = 'en'

        try:
            timezone_int = int(timezone)
        except (ValueError, TypeError):
            timezone_int = 9
        try:
            aime_int = int(aime)
        except (ValueError, TypeError):
            aime_int = 0

        # 检查用户是否已绑定
        user_data = USERS.get(user_id, {})
        has_account = all(key in user_data for key in ['sega_id', 'sega_pwd', 'version'])
        if has_account:
            return jsonify({"error": "Already bound", "message": "User already has a SEGA account linked. Use PUT to rebind."}), 409

        result = asyncio.run(process_sega_credentials(user_id, sega_id, password, ver, language, timezone_int, aime_int, False))
        if result == "MAINTENANCE":
            return jsonify({"error": "Maintenance", "message": "The official website is under maintenance. Please try again later."}), 503
        elif result:
            track_event('user_bind', user_id=user_id, metadata={'version': ver, 'via_token': True})
            logger.info(f"[API] ✓ Bind success: user_id={user_id}, ver={ver}, token_id={token_info['token_id']}")
            return jsonify({"success": True, "user_id": user_id, "message": "SEGA account bound successfully."})
        else:
            return jsonify({"error": "Authentication failed", "message": "Invalid SEGA ID or password."}), 401

    except Exception as e:
        logger.error(f"[API] ✗ Bind error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/api/v2/users/<user_id>/bind", methods=["PUT"])
@csrf.exempt
@require_dev_token
@require_user_permission
def api_rebind_user(user_id):
    """
    换绑 SEGA 账号 API（更新密码/版本/Aime）

    需要 Bearer Token 认证并拥有该用户的访问权限

    请求体 (JSON / form-data):
    - sega_id: 必需，SEGA ID（必须与现有一致）
    - password: 必需，新密码
    - ver: 服务器版本 jp/intl（可选，保持现有）
    - aime: Aime卡选择（可选，保持现有）
    """
    try:
        token_info = request.token_info
        data = request.form.to_dict() or request.get_json(force=True, silent=True) or {}

        sega_id = data.get('sega_id', '')
        password = data.get('password', '')

        if not sega_id:
            return jsonify({"error": "Missing parameter", "message": "Parameter 'sega_id' is required"}), 400
        if not password:
            return jsonify({"error": "Missing parameter", "message": "Parameter 'password' is required"}), 400

        user_data = USERS.get(user_id, {})
        has_account = all(key in user_data for key in ['sega_id', 'sega_pwd', 'version'])
        if not has_account:
            return jsonify({"error": "Not bound", "message": "User has no SEGA account linked. Use POST to bind first."}), 404

        if sega_id != user_data.get('sega_id'):
            return jsonify({"error": "Forbidden", "message": "Cannot change SEGA ID. Provide the existing SEGA ID."}), 403

        ver = data.get('ver', user_data.get('version', 'jp')).strip().lower()
        aime = data.get('aime', str(user_data.get('aime', 0)))
        language = user_data.get('language', 'en')
        timezone_int = user_data.get('timezone', 9)

        if ver not in ('jp', 'intl'):
            return jsonify({"error": "Invalid parameter", "message": "Parameter 'ver' must be jp or intl"}), 400

        try:
            aime_int = int(aime)
        except (ValueError, TypeError):
            aime_int = user_data.get('aime', 0)

        result = asyncio.run(process_sega_credentials(user_id, sega_id, password, ver, language, timezone_int, aime_int, True))
        if result == "MAINTENANCE":
            return jsonify({"error": "Maintenance", "message": "The official website is under maintenance. Please try again later."}), 503
        elif result:
            track_event('user_rebind', user_id=user_id, metadata={'version': ver, 'via_token': True})
            logger.info(f"[API] ✓ Rebind success: user_id={user_id}, ver={ver}, token_id={token_info['token_id']}")
            return jsonify({"success": True, "user_id": user_id, "message": "SEGA account rebound successfully."})
        else:
            return jsonify({"error": "Authentication failed", "message": "Invalid SEGA ID or password."}), 401

    except Exception as e:
        logger.error(f"[API] ✗ Rebind error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/api/v2/users/<user_id>/tasks", methods=["POST"])
@app.route("/api/v1/users/<user_id>/tasks", methods=["POST"])
@csrf.exempt
@require_dev_token
@require_user_permission
def api_sync_user_data(user_id):
    """
    触发用户数据同步 API (RESTful)

    需要 Bearer Token 认证并拥有该用户的访问权限

    将用户加入更新队列，异步执行数据同步
    """
    try:
        # 检查用户是否已绑定账号
        if 'sega_id' not in USERS[user_id] or 'sega_pwd' not in USERS[user_id]:
            return jsonify({
                "error": "Account not bound",
                "message": f"User {user_id} has not bound a SEGA account"
            }), 400

        # 创建模拟事件对象用于更新任务
        class MockEvent:
            def __init__(self, user_id):
                self.source = type('obj', (object,), {'user_id': user_id})()
                self.reply_token = None  # API 调用不需要回复

        mock_event = MockEvent(user_id)

        # 生成任务ID
        task_id = f"api_sync_{secrets.token_hex(8)}"

        # 将更新任务加入队列
        try:
            webtask_queue.put_nowait((async_maimai_update_task, (mock_event,), task_id))

            # 记录 API 访问日志
            token_info = request.token_info
            logger.info(f"[API] ✓ Sync triggered: user_id={user_id}, task_id={task_id}, token_id={token_info['token_id']}, note={token_info['note']}")

            return jsonify({
                "success": True,
                "message": "Sync task queued successfully",
                "user_id": user_id,
                "task_id": task_id,
                "queue_size": webtask_queue.qsize()
            }), 202  # 202 Accepted 更适合异步操作

        except queue.Full:
            return jsonify({
                "error": "Queue full",
                "message": "Sync queue is full, please try again later",
                "queue_size": webtask_queue.qsize()
            }), 503

    except Exception as e:
        logger.error(f"[API] ✗ Sync user error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ==================== Permission Management APIs (RESTful) ====================

@app.route("/api/v2/users/<user_id>/permissions", methods=["POST"])
@app.route("/api/v1/users/<user_id>/permissions", methods=["POST"])
@csrf.exempt
@require_dev_token
def api_request_user_permission(user_id):
    """
    请求访问用户的权限 API (RESTful)

    需要 Bearer Token 认证

    类似好友请求机制，token 发送权限请求后，需要用户同意才能获取访问权限

    请求体 (JSON):
    - requester_name: 可选，请求者名称（用于在通知中显示）

    返回:
    - success: 是否成功发送请求
    - request_id: 请求ID（用于后续接受/拒绝操作）
    - message: 状态信息
    """
    try:
        # 获取 JSON 数据
        data = request.form.to_dict() or request.get_json(force=True, silent=True) or {}
        requester_name = data.get('requester_name', '')

        # 获取 token 信息
        token_info = request.token_info
        token_id = token_info['token_id']

        # 如果没有提供 requester_name，使用 token 的 note
        if not requester_name:
            requester_name = token_info.get('note', token_id)

        # 记录 API 访问日志
        logger.info(f"[API] Request permission: target_user_id={user_id}, token_id={token_id}, note={token_info['note']}")

        # 发送权限请求
        result = send_perm_request(token_id, user_id, requester_name)

        if result['success']:
            # 通过 LINE 推送权限请求通知
            try:
                perm_requests = get_pending_perm_requests(user_id)
                perm_msg = generate_perm_request_message(perm_requests, user_id)
                if perm_msg:
                    smart_push(user_id, [perm_msg], configuration)
            except Exception as e:
                logger.warning(f"[API] ⚠ Failed to push permission request notification: user_id={user_id}, error={e}")

            return jsonify({
                "success": True,
                "request_id": result['request_id'],
                "user_id": user_id,
                "message": result['message']
            }), 201  # 201 Created for new permission request

        else:
            # 根据错误类型返回不同的 HTTP 状态码
            status_code = 404 if result['error'] == "User not found" else 400
            return jsonify({
                "error": result['error'],
                "message": result['message']
            }), status_code

    except Exception as e:
        logger.error(f"[API] ✗ Request permission error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v2/users/<user_id>/permissions/requests", methods=["GET"])
@app.route("/api/v1/users/<user_id>/permissions/requests", methods=["GET"])
@csrf.exempt
@require_dev_token
@require_owner_permission
def api_get_user_permission_requests(user_id):
    """
    获取用户的待处理权限请求列表 API (RESTful)

    需要 Bearer Token 认证（该 token 必须是用户的所有者）

    返回:
    - requests: 权限请求列表，包含 request_id, token_id, requester_name, timestamp
    """
    try:
        # 获取待处理的权限请求
        requests = get_pending_perm_requests(user_id)

        # 记录 API 访问日志
        token_info = request.token_info
        logger.info(f"[API] Get permission requests: user_id={user_id}, token_id={token_info['token_id']}, note={token_info['note']}")

        return jsonify({
            "success": True,
            "user_id": user_id,
            "count": len(requests),
            "requests": requests
        })

    except Exception as e:
        logger.error(f"[API] ✗ Get permission requests error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v1/users/<user_id>/permissions/requests/<request_id>", methods=["PATCH"])
@app.route("/api/v2/users/<user_id>/permissions/requests/<request_id>", methods=["PATCH"])
@csrf.exempt
@require_dev_token
@require_owner_permission
def api_manage_user_permission(user_id, request_id):
    """
    管理用户权限请求 API (RESTful)

    需要 Bearer Token 认证（该 token 必须是用户的所有者 token）

    请求体 (JSON):
    - action: 必需，操作类型 ("accept" 或 "reject")

    返回:
    - success: 是否成功处理
    - token_id: 被授权的 token ID (仅在接受时返回)
    - message: 状态信息
    """
    try:
        # 获取 JSON 数据
        data = request.form.to_dict() or request.get_json(force=True, silent=True) or {}
        action = data.get('action', '')

        if action not in ['accept', 'reject']:
            return jsonify({
                "error": "Invalid parameter",
                "message": "Parameter 'action' must be 'accept' or 'reject'"
            }), 400

        # 记录 API 访问日志
        token_info = request.token_info
        logger.info(f"[API] Manage permission: action={action}, request_id={request_id}, user_id={user_id}, token_id={token_info['token_id']}, note={token_info['note']}")

        # 根据action执行相应操作
        if action == 'accept':
            result = accept_perm_request(user_id, request_id)
            if result['success']:
                return jsonify({
                    "success": True,
                    "user_id": user_id,
                    "token_id": result['token_id'],
                    "token_note": result['token_note'],
                    "message": result['message']
                })
        else:  # reject
            result = reject_perm_request(user_id, request_id)
            if result['success']:
                return jsonify({
                    "success": True,
                    "user_id": user_id,
                    "token_id": result['token_id'],
                    "token_note": result['token_note'],
                    "message": result['message']
                })

        # 处理错误
        status_code = 404 if result['error'] in ["User not found", "Request not found", "Invalid token"] else 400
        return jsonify({
            "error": result['error'],
            "message": result['message']
        }), status_code

    except Exception as e:
        logger.error(f"[API] ✗ Manage permission error: user_id={user_id}, request_id={request_id}, action={action}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v1/users/<user_id>/permissions/self", methods=["DELETE"])
@app.route("/api/v2/users/<user_id>/permissions/self", methods=["DELETE"])
@csrf.exempt
@require_dev_token
def api_revoke_own_permission(user_id):
    """
    放弃自己对某用户的访问权限（自撤销）

    需要 Bearer Token 认证，只能撤销已授权（allowed_users）的权限，
    不能撤销 owner（创建者）权限。
    """
    try:
        if user_id not in USERS:
            return jsonify({"error": "User not found", "message": f"User {user_id} does not exist"}), 404

        token_info = request.token_info
        token_id = token_info['token_id']

        if USERS[user_id].get('registered_via_token') == token_id:
            return jsonify({"error": "Forbidden", "message": "Owner permission cannot be self-revoked"}), 403

        dev_tokens = load_dev_tokens()
        allowed_users = dev_tokens.get(token_id, {}).get('allowed_users', [])
        if user_id not in allowed_users:
            return jsonify({"error": "Permission not found", "message": f"Token does not have granted permission for user {user_id}"}), 404

        allowed_users.remove(user_id)
        dev_tokens[token_id]['allowed_users'] = allowed_users
        save_dev_tokens(dev_tokens)

        logger.info(f"[API] Self-revoke permission: token_id={token_id}, user_id={user_id}")
        return jsonify({"success": True, "user_id": user_id, "message": "Permission revoked"})

    except Exception as e:
        logger.error(f"[API] ✗ Self-revoke permission error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/api/v1/users/<user_id>/permissions/<token_id>", methods=["DELETE"])
@app.route("/api/v2/users/<user_id>/permissions/<token_id>", methods=["DELETE"])
@csrf.exempt
@require_dev_token
@require_owner_permission
def api_revoke_user_permission(user_id, token_id):
    """
    撤销已授予的权限 API (RESTful)

    需要 Bearer Token 认证（该 token 必须是用户的所有者）

    返回:
    - success: 是否成功撤销
    - message: 状态信息
    """
    try:
        # 记录 API 访问日志
        token_info = request.token_info
        logger.info(f"[API] Revoke permission: target_token_id={token_id}, user_id={user_id}, token_id={token_info['token_id']}, note={token_info['note']}")

        # 加载 dev tokens
        dev_tokens = load_dev_tokens()

        if token_id not in dev_tokens:
            return jsonify({
                "error": "Token not found",
                "message": f"Token {token_id} does not exist"
            }), 404

        # 从 allowed_users 列表中移除该用户
        allowed_users = dev_tokens[token_id].get('allowed_users', [])
        if user_id in allowed_users:
            allowed_users.remove(user_id)
            dev_tokens[token_id]['allowed_users'] = allowed_users
            save_dev_tokens(dev_tokens)

            return jsonify({
                "success": True,
                "user_id": user_id,
                "token_id": token_id,
                "message": f"Permission revoked for token {token_id}"
            })
        else:
            return jsonify({
                "error": "Permission not found",
                "message": f"Token {token_id} does not have permission to access user {user_id}"
            }), 404

    except Exception as e:
        logger.error(f"[API] ✗ Revoke permission error: user_id={user_id}, target_token_id={token_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ==================== Task Status API (RESTful) ====================

@app.route("/api/v1/tasks/<task_id>", methods=["GET"])
@app.route("/api/v2/tasks/<task_id>", methods=["GET"])
@csrf.exempt
@require_dev_token
def api_get_task(task_id):
    """
    查询任务状态 API (RESTful)

    需要 Bearer Token 认证

    返回指定任务的状态信息（running, queued, completed 或 not_found）
    """
    try:
        with task_tracking_lock:
            # 检查任务是否在运行中
            for task in task_tracking['running']:
                if task.get('id') == task_id:
                    return jsonify({
                        "success": True,
                        "task_id": task_id,
                        "status": "running",
                        "start_time": task.get('start_time'),
                        "task_type": task.get('type', 'unknown')
                    })

            # 检查任务是否在队列中
            for task in task_tracking['queued']:
                if task.get('id') == task_id:
                    return jsonify({
                        "success": True,
                        "task_id": task_id,
                        "status": "queued",
                        "queued_time": task.get('queued_time'),
                        "task_type": task.get('type', 'unknown'),
                        "queue_position": task_tracking['queued'].index(task) + 1
                    })

            # 检查任务是否已完成
            for task in task_tracking['completed']:
                if task.get('id') == task_id:
                    return jsonify({
                        "success": True,
                        "task_id": task_id,
                        "status": "completed",
                        "start_time": task.get('start_time'),
                        "end_time": task.get('end_time'),
                        "duration": task.get('duration'),
                        "task_type": task.get('type', 'unknown'),
                        "result": task.get('result', 'success')
                    })

        # 任务不存在
        return jsonify({
            "success": False,
            "task_id": task_id,
            "status": "not_found",
            "message": "Task not found or expired"
        }), 404

    except Exception as e:
        logger.error(f"[API] ✗ Get task status error: task_id={task_id}, error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ==================== Song Search API (RESTful) ====================

@app.route("/api/v2/songs/search", methods=["GET"])
@csrf.exempt
@require_dev_token
def api_v2_search_songs():
    """
    搜索歌曲 API

    需要 Bearer Token 认证

    参数:
    - q: 可选，搜索关键词，如果不提供或使用 __empty__ 则搜索空字符串
    - ver: 可选，服务器版本 (jp/intl)，默认为 jp
    - max_results: 可选，最大结果数，默认为 6

    返回匹配歌曲的 id 和基本信息，调用方可使用 id 进一步查询 info 或 record 图片
    """
    try:
        query = request.args.get('q', '')
        ver = request.args.get('ver', 'jp')
        max_results = request.args.get('max_results', MAX_SEARCH_RESULTS, type=int)

        if query == '__empty__':
            query = ''

        if ver not in ['jp', 'intl']:
            return jsonify({
                "error": "Invalid parameter",
                "message": "Parameter 'ver' must be 'jp' or 'intl'"
            }), 400

        token_info = request.token_info
        logger.info(f"[API] Search songs: query='{query}', token_id={token_info['token_id']}, note={token_info['note']}")

        songs, _ = read_dxdata(ver)
        matching_songs = find_matching_songs(query, songs, max_results=max_results)

        if not matching_songs:
            return jsonify({
                "success": True,
                "count": 0,
                "songs": [],
                "message": "No songs found"
            })

        if len(matching_songs) > max_results:
            return jsonify({
                "error": "Too many results",
                "message": f"Found {len(matching_songs)} songs, please refine your search (max: {max_results})",
                "count": len(matching_songs)
            }), 400

        # 只返回 id 和基本信息
        result = []
        for song in matching_songs:
            result.append({
                "id": song.get("id"),
                "title": song.get("title"),
                "artist": song.get("artist"),
                "type": song.get("type"),
                "version": song.get("version"),
            })

        return jsonify({
            "success": True,
            "count": len(result),
            "query": query,
            "ver": ver,
            "songs": result
        })

    except Exception as e:
        logger.error(f"[API] ✗ Search songs error: query='{query}', error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/v1/versions", methods=["GET"])
@app.route("/api/v2/versions", methods=["GET"])
@csrf.exempt
@require_dev_token
def api_get_versions():
    """
    获取版本信息 API

    需要 Bearer Token 认证

    返回 maimai DX 的版本信息

    示例:
    curl -H "Authorization: Bearer <your_token>" https://your-domain.com/api/v1/versions
    """
    try:
        # 记录 API 访问日志
        token_info = request.token_info
        logger.info(f"[API] Get versions: token_id={token_info['token_id']}, note={token_info['note']}")

        _, versions = read_dxdata()

        return jsonify({
            "success": True,
            "versions": versions
        })

    except Exception as e:
        logger.error(f"[API] ✗ Get versions error: error={e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ==================== API v2 ====================

@app.route("/api/v2/dxdata", methods=["GET"])
@csrf.exempt
@require_dev_token
def api_v2_dxdata():
    """
    下载 dxdata.json（已应用 override）

    参数:
    - ver: jp / intl (默认 jp)

    返回: application/json
    """
    ver = request.args.get("ver", "jp").strip().lower()
    if ver not in ("jp", "intl"):
        return jsonify({"error": "Invalid ver, use jp or intl"}), 400
    songs, versions = read_dxdata(ver)
    return jsonify({"songs": songs, "versions": versions})

def _send_image_response(buf):
    """根据 format 参数返回图片（png 或 base64 JSON）"""
    fmt = request.args.get('format', 'png').strip().lower()
    if fmt == 'base64':
        img_data = b64mod.b64encode(buf.getvalue()).decode()
        buf.close()
        return jsonify({"success": True, "format": "base64", "image": img_data})
    return send_file(buf, mimetype="image/png")


@app.route("/api/v2/songs/<song_id>/image", methods=["GET"])
@csrf.exempt
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

        token_info = request.token_info
        logger.info(f"[API] Song info generated: song_id={song_id}, ver={ver}, token_id={token_info['token_id']}")
        track_event('image_gen', user_id=None, metadata={'command': 'song-info', 'song_id': song_id, 'ver': ver})
        return _send_image_response(buf)

    except Exception as e:
        logger.error(f"[API] ✗ Song info error: song_id={song_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/api/v2/users/<user_id>/songs/<song_id>/image", methods=["GET"])
@csrf.exempt
@require_dev_token
def api_v2_song_record(user_id, song_id):
    """
    生成用户歌曲记录图片 API

    需要 Bearer Token 认证

    返回: image/png（包含用户在该歌曲各难度的游玩记录）
    """
    try:
        token_info = request.token_info
        has_permission, error_response = check_user_permission(user_id, token_info['token_id'])
        if not has_permission:
            return error_response

        if user_id not in USERS:
            return jsonify({"error": "User not found"}), 404
        if "personal_info" not in USERS[user_id]:
            return jsonify({"error": "User info not found, please sync first"}), 404

        ver = USERS[user_id].get("version", "jp")
        songs, _ = read_dxdata(ver)
        matching_song = None
        for song in songs:
            if song.get('id') == song_id:
                matching_song = song
                break

        if not matching_song:
            return jsonify({"error": "Song not found"}), 404

        song_record = read_record(user_id)
        if not song_record:
            return jsonify({"error": "No records found, please sync first"}), 404

        played_data = []
        for rcd in song_record:
            if rcd['cover_name'] == matching_song['cover_name'] and rcd['type'] == matching_song['type']:
                played_data.append(rcd)

        if not played_data:
            return jsonify({"error": "No record for this song"}), 404

        user_tz = get_user_timezone(user_id)
        song_img = song_info_generate(matching_song, played_data, timezone_offset=user_tz, ver=ver, bg_filter=_get_user_bg_filter(user_id))

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


@app.route("/api/v2/users/<user_id>/image", methods=["GET"])
@csrf.exempt
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

        has_permission, error_response = check_user_permission(user_id, token_info['token_id'])
        if not has_permission:
            return error_response

        if user_id not in USERS:
            return jsonify({"error": "User not found"}), 404

        if "personal_info" not in USERS[user_id]:
            return jsonify({"error": "User info not found, please sync first"}), 404

        command = request.args.get('command', 'b50').strip().lower()
        parts = re.split(r"[ \n]", command, 1)
        first_word = parts[0]
        rest_text = parts[1] if len(parts) > 1 else ""

        ver = USERS[user_id].get("version", "jp")

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
        song_record = read_record(user_id, recent, recent_type)
        if not song_record:
            return jsonify({"error": "No records found, please sync first"}), 404

        up_songs, down_songs, details = select_records(song_record, record_type, rest_text, ver)
        if not up_songs and not down_songs:
            return jsonify({"error": "No matching records for this command"}), 404

        display_type = "未だ知らず" if record_type == "unknown" else record_type
        record_img = generate_records_picture(up_songs, down_songs, display_type.upper(), ver, details)
        user_info = USERS[user_id].get('personal_info')
        profile_img = generate_profile(user_info, user_id=user_id)
        user_tz = get_user_timezone(user_id)
        img = compose_images([profile_img, record_img], spacing=0, border_width=0, timezone_offset=user_tz, bg_filter=_get_user_bg_filter(user_id))
        del profile_img, record_img
        gc.collect(0)

        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        del img
        gc.collect(0)

        logger.info(f"[API] v2 Image generated: user_id={user_id}, command={command}, token_id={token_info['token_id']}")
        track_event('image_gen', user_id=user_id, metadata={'command': _classify_image_command(command)})
        return _send_image_response(buf)

    except Exception as e:
        logger.error(f"[API] ✗ v2 Generate image error: user_id={user_id}, error={e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/api/v2/users/<user_id>/plate", methods=["GET"])
@csrf.exempt
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
        has_permission, error_response = check_user_permission(user_id, token_info['token_id'])
        if not has_permission:
            return error_response

        if user_id not in USERS:
            return jsonify({"error": "User not found"}), 404
        if "personal_info" not in USERS[user_id]:
            return jsonify({"error": "User info not found, please sync first"}), 404

        title = request.args.get('title', '').strip()
        if not title:
            return jsonify({"error": "title parameter is required"}), 400
        if not (len(title) == 2 or len(title) == 3):
            return jsonify({"error": "Invalid title length, must be 2 or 3 characters"}), 400

        ver = USERS[user_id].get("version", "jp")
        song_record = read_record(user_id)
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

        user_info = USERS[user_id].get('personal_info')
        profile_img = generate_profile(user_info, user_id=user_id)
        user_tz = get_user_timezone(user_id)
        img = compose_images([profile_img, plate_img], spacing=0, border_width=0, timezone_offset=user_tz, bg_filter=_get_user_bg_filter(user_id))
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


@app.route("/api/v2/users/<user_id>/achievement", methods=["GET"])
@csrf.exempt
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
        has_permission, error_response = check_user_permission(user_id, token_info['token_id'])
        if not has_permission:
            return error_response

        if user_id not in USERS:
            return jsonify({"error": "User not found"}), 404
        if "personal_info" not in USERS[user_id]:
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

        ver = USERS[user_id].get("version", "jp")
        target_type, target_icons = rank_mapping[rank] if rank else (None, None)

        song_record = read_record(user_id)
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

        user_info = USERS[user_id].get('personal_info')
        profile_img = generate_profile(user_info, scale=1.5, user_id=user_id)
        user_tz = get_user_timezone(user_id)
        img = compose_images([profile_img, record_img], spacing=0, border_width=0, timezone_offset=user_tz, bg_filter=_get_user_bg_filter(user_id))
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


if __name__ == "__main__":
    # ==================== 系统启动自检 ====================
    # 在启动 worker 线程之前执行系统自检
    logger.info("=" * 60)
    logger.info("[System] → Starting JiETNG Maimai DX LINE Bot...")
    logger.info("=" * 60)

    try:
        # 读取用户数据
        logger.info("[System] → Loading user list...")
        load_user()

        # 加载 tip/ad 数据
        logger.info("[System] → Loading tip/ad data...")
        load_tip_ad_data()

        system_check_results = run_system_check()

        # 如果有关键问题，显示警告
        if system_check_results["overall_status"] == "WARNING":
            logger.info("[System] ⚠ System check found some issues")
            logger.info("[System] → Check logs for details")
        else:
            logger.info("[System] ✓ System check passed")

    except Exception as e:
        logger.info(f"[System] ⚠ System check failed: error={e}")
        logger.info("[System] → Continuing startup anyway...")

    # 启动 worker 线程
    for i in range(MAX_CONCURRENT_IMAGE_TASKS):
        threading.Thread(target=image_worker, daemon=True, name=f"ImageWorker-{i+1}").start()

    for i in range(WEB_MAX_CONCURRENT_TASKS):
        threading.Thread(target=webtask_worker, daemon=True, name=f"WebTaskWorker-{i+1}").start()

    logger.info(f"[System] ✓ Workers started: image={MAX_CONCURRENT_IMAGE_TASKS}, web={WEB_MAX_CONCURRENT_TASKS}")

    # 启动定期清理线程
    _start_periodic_cleanup()

    # 启动内存管理器
    memory_manager.start()
    logger.info("[System] ✓ Memory manager started")

    # 注册清理函数（在内存管理器的清理循环中调用）
    def custom_cleanup():
        """自定义清理函数"""
        try:
            # 清理用户昵称缓存
            cleaned_nicknames = cleanup_user_caches(user_manager_module)

            # 清理频率限制追踪数据
            cleaned_rate_limits = cleanup_rate_limiter_tracking(rate_limiter_module)

            # 清理未绑定的用户（没有 sega_id 或 sega_pwd）
            cleanup_result = clean_unbound_users()
            cleaned_unbound_users = cleanup_result.get('deleted_count', 0)

            # 刷新 dev tokens 缓存到磁盘
            flush_dev_tokens()

            logger.info(f"[System] ✓ Custom cleanup completed: nicknames={cleaned_nicknames}, rate_limits={cleaned_rate_limits}, unbound_users={cleaned_unbound_users}")
        except Exception as e:
            logger.error(f"[System] ✗ Custom cleanup error: error={e}", exc_info=True)

    # 覆盖内存管理器的cleanup方法，加入自定义清理
    original_cleanup = memory_manager.cleanup
    def enhanced_cleanup():
        stats = original_cleanup()
        custom_cleanup()
        return stats
    memory_manager.cleanup = enhanced_cleanup

    try:
        app.run(host=HOST, port=PORT)

    finally:
        write_user(True)
        save_dev_tokens(force=True)

        # 停止内存管理器
        memory_manager.stop()
        logger.info("[System] Memory manager stopped")
