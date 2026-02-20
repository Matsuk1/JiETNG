"""
通知管理模块

在内存中存储系统错误通知，供 admin panel 查看。
支持 Web Push 推送到已订阅的设备。
"""

import json
import logging
import threading
from datetime import datetime

from modules.config_loader import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CONTACT

logger = logging.getLogger(__name__)

# ===== 内存通知列表 =====
_notifications = []
_notif_lock = threading.Lock()
MAX_NOTIFICATIONS = 100

# ===== Push 订阅存储 =====
PUSH_SUBS_FILE = './data/push_subscriptions.json'
_subscriptions = {}   # endpoint -> subscription dict
_subs_lock = threading.Lock()


def _load_subscriptions():
    global _subscriptions
    try:
        with open(PUSH_SUBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _subscriptions = data if isinstance(data, dict) else {}
    except FileNotFoundError:
        _subscriptions = {}
    except Exception as e:
        logger.error(f"[Push] Failed to load subscriptions: {e}")
        _subscriptions = {}


def _save_subscriptions():
    try:
        with open(PUSH_SUBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_subscriptions, f)
    except Exception as e:
        logger.error(f"[Push] Failed to save subscriptions: {e}")


_load_subscriptions()


def add_push_subscription(subscription: dict):
    """添加或更新一个 push 订阅"""
    endpoint = subscription.get('endpoint')
    if not endpoint:
        return
    with _subs_lock:
        _subscriptions[endpoint] = subscription
        _save_subscriptions()


def remove_push_subscription(endpoint: str):
    """删除一个 push 订阅"""
    with _subs_lock:
        _subscriptions.pop(endpoint, None)
        _save_subscriptions()


def _send_push(title: str, body: str):
    """向所有订阅设备发送 Web Push 通知"""
    if not _subscriptions:
        return

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning("[Push] pywebpush not installed, skipping push notification")
        return

    with _subs_lock:
        subs = list(_subscriptions.items())

    stale = []
    payload = json.dumps({'title': title, 'body': body})

    for endpoint, sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={'sub': VAPID_CONTACT}
            )
        except Exception as e:
            err_str = str(e)
            # 410 Gone / 404 = 订阅已失效，清理
            if '410' in err_str or '404' in err_str:
                stale.append(endpoint)
            else:
                logger.error(f"[Push] Failed to send to {endpoint[:40]}...: {e}")

    if stale:
        with _subs_lock:
            for ep in stale:
                _subscriptions.pop(ep, None)
            _save_subscriptions()


def record_notification(title: str, details: str, user_id: str = None, context: dict = None):
    """
    记录一条系统通知并推送到所有已订阅设备

    Args:
        title: 通知标题
        details: 详细信息（错误堆栈等）
        user_id: 触发错误的用户ID
        context: 附加上下文信息
    """
    with _notif_lock:
        _notifications.insert(0, {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'title': title,
            'details': details,
            'user_id': user_id or 'Unknown',
            'context': context or {}
        })
        if len(_notifications) > MAX_NOTIFICATIONS:
            _notifications.pop()

    # 在后台线程发送 push，不阻塞主流程
    first_line = details.splitlines()[0] if details else ''
    body = f"{user_id or 'Unknown'}\n{first_line}" if first_line else (user_id or 'Unknown')
    threading.Thread(target=_send_push, args=(title, body), daemon=True).start()


def get_notifications():
    """获取所有通知（最新在前）"""
    with _notif_lock:
        return list(_notifications)


def clear_notifications():
    """清空所有通知"""
    with _notif_lock:
        _notifications.clear()


def get_notification_count():
    """获取通知数量"""
    with _notif_lock:
        return len(_notifications)
