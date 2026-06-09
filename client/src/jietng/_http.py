"""HTTP 底层 / Shared HTTP helpers for sync & async clients."""
from __future__ import annotations

from typing import Any, Mapping, Optional, Tuple

import httpx

from . import __version__
from .exceptions import APIError, from_response


DEFAULT_BASE_URL = "https://jietng-endpoint.matsuk1.com/api/v2"
DEFAULT_TIMEOUT = 30.0


def _build_headers(token: str, extra: Optional[Mapping[str, str]] = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": f"jietng-py-sdk/{__version__}",
        "Accept": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


def _parse_json_safe(resp: httpx.Response) -> Any:
    """尽量返回 JSON；失败返回原始 bytes 或文本字符串。"""
    ctype = (resp.headers.get("content-type") or "").lower()
    if "application/json" in ctype:
        try:
            return resp.json()
        except Exception:
            return resp.text
    if ctype.startswith(("image/", "application/octet-stream", "application/xml")):
        return resp.content
    if "text/" in ctype:
        return resp.text
    # 兜底：尝试 JSON，否则原始字节
    try:
        return resp.json()
    except Exception:
        return resp.content


def _check_response(resp: httpx.Response) -> Any:
    """成功 → 返回解析后的内容；失败 → 抛对应 APIError 子类。"""
    payload = _parse_json_safe(resp)
    if 200 <= resp.status_code < 300:
        return payload
    raise from_response(resp.status_code, payload)


def _binary_response(resp: httpx.Response) -> bytes:
    """专给图片/导出文件用：成功返回 bytes，失败仍抛对应异常。"""
    if 200 <= resp.status_code < 300:
        return resp.content
    payload = _parse_json_safe(resp)
    raise from_response(resp.status_code, payload)


def _attachment_filename(resp: httpx.Response) -> Optional[str]:
    """从 Content-Disposition 头里解析 filename / filename* (RFC 6266)。"""
    cd = resp.headers.get("content-disposition", "")
    if not cd:
        return None
    # filename*=UTF-8''XXX 优先（CJK 安全）
    for part in cd.split(";"):
        part = part.strip()
        if part.lower().startswith("filename*=utf-8''"):
            from urllib.parse import unquote
            return unquote(part.split("''", 1)[1])
    for part in cd.split(";"):
        part = part.strip()
        if part.lower().startswith("filename="):
            value = part[len("filename="):].strip('"')
            return value
    return None
