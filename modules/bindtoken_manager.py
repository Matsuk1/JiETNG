"""
Token管理模块

生成和验证SEGA账户绑定的临时Token
"""

import base64
import hmac
import hashlib
import time
from modules.config_loader import BIND_TOKEN_KEY

# Token有效期 (秒)
TOKEN_EXPIRE_SECONDS = 120
PERM_TOKEN_EXPIRE_SECONDS = 600  # 权限管理 Token 有效期：10 分钟


def generate_bind_token(user_id: str) -> str:
    """
    生成绑定Token

    Args:
        user_id: 用户ID

    Returns:
        Base64编码的签名Token字符串
    """
    timestamp = str(int(time.time()))
    raw = f"{user_id}.{timestamp}".encode('utf-8')

    signature = hmac.new(BIND_TOKEN_KEY, raw, hashlib.sha256).digest()

    token = base64.urlsafe_b64encode(raw + b"." + signature).decode('utf-8')
    return token


def get_user_id_from_token(token: str) -> str:
    """
    验证Token并提取用户ID

    Args:
        token: Base64编码的Token字符串

    Returns:
        用户ID

    Raises:
        ValueError: Token无效、签名错误或已过期
    """
    try:
        decoded = base64.urlsafe_b64decode(token.encode('utf-8'))

        parts = decoded.split(b".", 2)
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        user_id_bytes, timestamp_bytes, signature = parts
        raw = user_id_bytes + b"." + timestamp_bytes

        # 验证签名
        expected_signature = hmac.new(BIND_TOKEN_KEY, raw, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")

        # 验证时效
        timestamp = int(timestamp_bytes.decode('utf-8'))
        now = int(time.time())
        if abs(now - timestamp) > TOKEN_EXPIRE_SECONDS:
            raise ValueError("Token expired")

        return user_id_bytes.decode('utf-8')

    except Exception as e:
        raise ValueError("Invalid token") from e


def generate_perm_token(user_id: str) -> str:
    """
    生成权限管理 Token（10 分钟有效）

    格式与 bind token 相同，但在 payload 中加入 "perm." 前缀以区分。
    """
    timestamp = str(int(time.time()))
    raw = f"perm.{user_id}.{timestamp}".encode('utf-8')
    signature = hmac.new(BIND_TOKEN_KEY, raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + b"." + signature).decode('utf-8')


def get_user_id_from_perm_token(token: str) -> str:
    """
    验证权限管理 Token 并提取用户ID

    Raises:
        ValueError: Token 无效、签名错误或已过期
    """
    try:
        decoded = base64.urlsafe_b64decode(token.encode('utf-8'))
        # payload 格式：perm.<user_id>.<timestamp>.<signature>
        # 由于 user_id 中可能含 '.'，只从末尾切出 signature，再从前缀后切 timestamp
        # 结构：b"perm." + user_id + b"." + timestamp + b"." + signature
        # 反向：最后 32 字节为 signature（sha256 digest）
        if len(decoded) < 34:
            raise ValueError("Invalid token format")
        signature = decoded[-32:]
        payload = decoded[:-33]  # 去掉最后的 "." + signature
        raw = decoded[:-33]      # 用于签名验证的原始数据（不含 "." + sig）
        raw_full = decoded[:-32 - 1]  # = payload（去掉末尾的 "." 分隔符）
        # 重新拆：raw = perm.<user_id>.<timestamp>，signature 在末尾
        raw_bytes = decoded[:-33]  # 去掉末尾 b"." + 32字节签名
        sig_bytes  = decoded[-32:]

        expected = hmac.new(BIND_TOKEN_KEY, raw_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(sig_bytes, expected):
            raise ValueError("Invalid token signature")

        parts = raw_bytes.decode('utf-8').split('.')
        # parts = ["perm", *user_id_parts, timestamp]
        if len(parts) < 3 or parts[0] != "perm":
            raise ValueError("Invalid perm token format")

        timestamp = int(parts[-1])
        user_id = '.'.join(parts[1:-1])  # user_id 本身可能含 '.'

        if abs(int(time.time()) - timestamp) > PERM_TOKEN_EXPIRE_SECONDS:
            raise ValueError("Token expired")

        return user_id

    except Exception as e:
        raise ValueError("Invalid perm token") from e
