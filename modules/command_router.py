"""命令路由 / Command Router

把散落在 main.py 的 6 个分发表（WEB_TASK_ROUTES / IMAGE_TASK_ROUTES /
RANK_COMMANDS / COMMAND_MAP / SPECIAL_RULES / 内联 if-block）统一到
一个 COMMANDS 列表 + 一次扫描派发。

- Matcher: 匹配方式（Exact / Prefix / Suffix / Regex / FirstWord）
- Command: matcher + handler + 元数据（queue / mention 策略 / rate_limit / …）
- CommandContext: 单次请求上下文，handler 通过它拿 user_id / id_use / match 等
- 实际 dispatch loop 与业务函数（smart_reply / queues / …）留在 main.py，
  本模块只提供数据结构和匹配原语。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional


# ============================================================
# Matchers
# ============================================================

class Matcher:
    """匹配成功返回 truthy 值（赋给 ctx.match，handler 可复用）；失败返回 None。"""
    def match(self, text: str):  # pragma: no cover - 抽象方法
        raise NotImplementedError


class Exact(Matcher):
    """精确匹配；默认大小写不敏感。"""
    __slots__ = ("_keywords", "_case_sensitive")

    def __init__(self, *keywords: str, case_sensitive: bool = False):
        self._case_sensitive = case_sensitive
        self._keywords = tuple(keywords) if case_sensitive else tuple(k.lower() for k in keywords)

    def match(self, text: str):
        s = text if self._case_sensitive else text.lower()
        return text if s in self._keywords else None


class Prefix(Matcher):
    """前缀匹配；默认大小写不敏感。"""
    __slots__ = ("_prefixes", "_case_sensitive")

    def __init__(self, *prefixes: str, case_sensitive: bool = False):
        self._case_sensitive = case_sensitive
        self._prefixes = tuple(prefixes) if case_sensitive else tuple(p.lower() for p in prefixes)

    def match(self, text: str):
        s = text if self._case_sensitive else text.lower()
        for p in self._prefixes:
            if s.startswith(p):
                return text
        return None


class Suffix(Matcher):
    """后缀匹配；区分大小写（日中文后缀常用）。"""
    __slots__ = ("_suffixes",)

    def __init__(self, *suffixes: str):
        self._suffixes = tuple(suffixes)

    def match(self, text: str):
        for s in self._suffixes:
            if text.endswith(s):
                return text
        return None


class Regex(Matcher):
    """正则匹配，返回 Match 对象（handler 可用 ctx.match.group(N) 取分组）。"""
    __slots__ = ("_pattern",)

    def __init__(self, pattern, flags: int = 0):
        self._pattern = pattern if hasattr(pattern, "match") else re.compile(pattern, flags)

    def match(self, text: str):
        return self._pattern.match(text)


class FirstWord(Matcher):
    """按第一个 token（空格/换行分隔，小写）匹配——b 系列命令用。"""
    __slots__ = ("_keywords",)
    _SPLIT = re.compile(r"[ \n]")

    def __init__(self, *keywords: str):
        self._keywords = tuple(k.lower() for k in keywords)

    def match(self, text: str):
        first = self._SPLIT.split(text.lower(), 1)[0]
        return text if first in self._keywords else None


# ============================================================
# Queue lanes
# ============================================================

QUEUE_SYNC = "sync"     # 主线程同步执行
QUEUE_IMAGE = "image"   # 图片 worker（CPU 重，限并发）
QUEUE_WEB = "web"       # web worker（要联网，限速）


# ============================================================
# Command
# ============================================================

@dataclass
class Command:
    """一条命令。

    Args:
        matcher: 匹配规则
        handler:
          - QUEUE_SYNC / QUEUE_IMAGE: 签名 (ctx) -> Optional[Message]；
            dispatcher 负责 smart_reply
          - QUEUE_WEB: 签名 (event) -> None；handler 自己负责 reply
        queue: 执行通道
        self_only: True 时，@ 别人会被拒绝（cannot_do_for_others）
        mention_queryable: True 时，被 @ 的用户成为查询目标。若该用户未注册，
          dispatcher 会回 mention_error。默认 False（mention 被忽略）。
        addition: smart_reply 是否附加 tip/ad（仅 SYNC/IMAGE 生效）
        rate_limit_key: 设置则做频率限制（仅 IMAGE/WEB 推荐）
        name: 日志 / task tracking 显示用名
    """
    matcher: Matcher
    handler: Callable
    queue: str = QUEUE_SYNC
    self_only: bool = False
    mention_queryable: bool = False
    addition: bool = True
    rate_limit_key: Optional[str] = None
    name: str = ""

    def try_match(self, text: str):
        return self.matcher.match(text)


# ============================================================
# Context
# ============================================================

@dataclass
class CommandContext:
    """单次消息派发的上下文。"""
    event: Any
    text: str                 # 已清洗（去 mention、归一空白）后的消息正文
    user_id: str
    source_type: str          # "user" / "group" / "room"
    reply_token: str
    mentioned_user_id: Optional[str]  # 已注册的被 @ 用户 id；未注册或未 @ 则 None
    has_other_mention: bool   # 是否 @ 了非 bot 用户（不论是否注册）
    id_use: str               # mentioned_user_id 优先，否则等于 user_id
    mai_ver: str              # 发起者版本
    mai_ver_use: str          # 目标用户版本（mention 或自己）
    match: Any = None         # 由 Matcher.match 返回（str 或 re.Match）

    @property
    def is_mention(self) -> bool:
        return self.id_use != self.user_id
