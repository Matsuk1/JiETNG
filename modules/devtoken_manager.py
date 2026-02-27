"""
开发者 Token 管理模块
Developer Token Management Module

使用内存缓存，避免每次验证都读写磁盘
"""

import json
import os
import secrets
import logging
from datetime import datetime

# 从配置加载文件路径
from modules.config_loader import DEV_TOKENS_FILE

logger = logging.getLogger(__name__)

# 内存缓存
_dev_tokens = None
_dirty = False


def load_dev_tokens():
    """加载开发者 tokens 到内存缓存（仅在未加载时读取）"""
    global _dev_tokens, _dirty
    if _dev_tokens is None:
        if not os.path.exists(DEV_TOKENS_FILE):
            _dev_tokens = {}
        else:
            try:
                with open(DEV_TOKENS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                _dev_tokens = data if isinstance(data, dict) else {}
            except Exception as e:
                logger.error(f"[DevToken] ✗ Failed to load tokens: {e}", exc_info=True)
                _dev_tokens = {}
        _dirty = False
    return _dev_tokens


def save_dev_tokens(tokens=None, force=False):
    """保存开发者 tokens 到磁盘

    Args:
        tokens: 要保存的 tokens 字典（如果为 None 则保存内存缓存）
        force: 强制写入，忽略脏标记
    """
    global _dev_tokens, _dirty

    if tokens is not None:
        _dev_tokens = tokens
        _dirty = True

    # 从未加载过，不写入（避免用 null 覆盖磁盘上的有效数据）
    if _dev_tokens is None:
        return True

    if not force and not _dirty:
        return True

    try:
        dir_path = os.path.dirname(os.path.abspath(DEV_TOKENS_FILE))
        os.makedirs(dir_path, exist_ok=True)
        with open(DEV_TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_dev_tokens, f, ensure_ascii=False, indent=2)
        _dirty = False
        logger.info(f"[DevToken] Saved {len(_dev_tokens)} tokens to {DEV_TOKENS_FILE}")
        return True
    except Exception as e:
        logger.error(f"[DevToken] ✗ Failed to save tokens: {e}", exc_info=True)
        return False


def _mark_dirty():
    """标记数据已修改"""
    global _dirty
    _dirty = True


def flush_dev_tokens():
    """将内存中的修改写入磁盘（供定期任务或关机时调用）"""
    save_dev_tokens(force=True)


def generate_dev_token():
    """生成一个安全的随机 token"""
    return secrets.token_urlsafe(32)

def create_dev_token(note, created_by):
    """
    创建新的开发者 token

    Args:
        note: Token 备注说明
        created_by: 创建者的 user_id

    Returns:
        dict: 包含 token_id 和 token 的字典，失败返回 None
    """
    tokens = load_dev_tokens()

    # 生成唯一的 token_id
    token_id = f"jt_{secrets.token_hex(8)}"
    while token_id in tokens:
        token_id = f"jt_{secrets.token_hex(8)}"

    # 生成实际的 token
    token = generate_dev_token()

    # 创建 token 数据
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tokens[token_id] = {
        "token": token,
        "note": note,
        "created_at": created_at,
        "created_by": created_by,
        "last_used": None,
        "revoked": False,
        "allowed_users": []
    }

    _mark_dirty()
    if save_dev_tokens(force=True):
        return {
            "token_id": token_id,
            "token": token,
            "note": note,
            "created_at": created_at
        }
    return None

def list_dev_tokens():
    """
    获取所有 token 列表

    Returns:
        list: Token 信息列表
    """
    tokens = load_dev_tokens()
    result = []

    for token_id, data in tokens.items():
        result.append({
            "token_id": token_id,
            "note": data.get("note", ""),
            "created_at": data.get("created_at", ""),
            "created_by": data.get("created_by", ""),
            "last_used": data.get("last_used", "Never"),
            "revoked": data.get("revoked", False),
            "token_preview": data.get("token", "")[:8] + "..." if data.get("token") else ""
        })

    return result

def revoke_dev_token(token_id):
    """
    撤销指定的 token

    Args:
        token_id: Token ID

    Returns:
        bool: 是否成功
    """
    tokens = load_dev_tokens()

    if token_id not in tokens:
        return False

    tokens[token_id]["revoked"] = True
    _mark_dirty()
    return save_dev_tokens(force=True)

def verify_dev_token(token):
    """
    验证 token 是否有效

    Args:
        token: 实际的 token 字符串

    Returns:
        dict: Token 信息，如果无效返回 None
    """
    tokens = load_dev_tokens()

    for token_id, data in tokens.items():
        if data.get("token") == token and not data.get("revoked", False):
            # 更新最后使用时间（仅内存，延迟写入）
            data["last_used"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            _mark_dirty()

            return {
                "token_id": token_id,
                "note": data.get("note", ""),
                "created_by": data.get("created_by", "")
            }

    return None

def get_token_info(token_id=None, token=None):
    """
    获取 token 详细信息

    Args:
        token_id: Token ID（可选）
        token: 实际的 token 字符串（可选）

    Returns:
        dict: Token 详细信息，如果不存在返回 None
    """
    tokens = load_dev_tokens()

    if token_id and token_id in tokens:
        data = tokens[token_id]
        return {
            "token_id": token_id,
            "token": data.get("token", ""),
            "note": data.get("note", ""),
            "created_at": data.get("created_at", ""),
            "created_by": data.get("created_by", ""),
            "last_used": data.get("last_used", "Never"),
            "revoked": data.get("revoked", False)
        }

    if token:
        for tid, data in tokens.items():
            if data.get("token") == token:
                return {
                    "token_id": tid,
                    "token": data.get("token", ""),
                    "note": data.get("note", ""),
                    "created_at": data.get("created_at", ""),
                    "created_by": data.get("created_by", ""),
                    "last_used": data.get("last_used", "Never"),
                    "revoked": data.get("revoked", False)
                }

    return None
