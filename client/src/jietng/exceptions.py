"""异常类型 / Exception hierarchy.

All API failures raise a subclass of :class:`jietngError`. Use specific
subclasses (``NotFoundError``, ``RateLimitedError`` …) to handle expected
failure modes; fall back to ``APIError`` for the generic case.
"""
from __future__ import annotations

from typing import Any, Optional


class jietngError(Exception):
    """SDK 基类异常。所有错误最终都是它或其子类。"""


class APIError(jietngError):
    """HTTP API 返回了非 2xx。

    Attributes:
        status_code: HTTP 状态码
        error: 服务器返回的 ``error`` 字段（若有）
        message: 服务器返回的 ``message`` 字段（若有）
        payload: 完整的响应 JSON（若服务器返回的是 JSON），方便排查
    """

    def __init__(
        self,
        status_code: int,
        *,
        error: Optional[str] = None,
        message: Optional[str] = None,
        payload: Any = None,
    ):
        self.status_code = status_code
        self.error = error
        self.message = message
        self.payload = payload
        head = f"[{status_code}]"
        if error:
            head += f" {error}"
        if message:
            head += f": {message}"
        super().__init__(head)


class AuthenticationError(APIError):
    """401 - token 缺失 / 无效 / 已撤销。"""


class PermissionDeniedError(APIError):
    """403 - 当前 token 对该用户没有访问权限。"""


class NotFoundError(APIError):
    """404 - 用户 / 任务 / 资源不存在。"""


class ValidationError(APIError):
    """400/413/415/422 - 请求、图片或识别结果不合法。"""


class RateLimitedError(APIError):
    """429 - 频率限制触发。"""


class ServerError(APIError):
    """500 - 服务器内部错误。"""


class QueueFullError(APIError):
    """503 - 服务端任务队列已满，请稍后再试。"""


# status_code → 异常类
_STATUS_MAP = {
    400: ValidationError,
    413: ValidationError,
    415: ValidationError,
    422: ValidationError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    429: RateLimitedError,
    500: ServerError,
    503: QueueFullError,
}


def from_response(status_code: int, payload: Any) -> APIError:
    """根据 HTTP 状态码 + payload 构造对应异常实例。"""
    cls = _STATUS_MAP.get(status_code, APIError)
    error = None
    message = None
    if isinstance(payload, dict):
        error = payload.get("error")
        message = payload.get("message")
    return cls(status_code, error=error, message=message, payload=payload)
