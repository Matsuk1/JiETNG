"""Command matching primitives shared by the bot dispatcher."""

import re
from dataclasses import dataclass
from typing import Any, Callable, Literal


MatchResult = str | re.Match[str]
QueueLane = Literal["sync", "image", "web"]


class Matcher:
    __slots__ = ()

    def match(self, text: str) -> MatchResult | None:
        raise NotImplementedError


class Exact(Matcher):
    __slots__ = ("keywords", "case_sensitive")

    def __init__(self, *keywords: str, case_sensitive=False):
        self.case_sensitive = case_sensitive
        self.keywords = frozenset(
            keywords if case_sensitive else map(str.lower, keywords)
        )

    def match(self, text):
        candidate = text if self.case_sensitive else text.lower()
        return text if candidate in self.keywords else None


class Prefix(Matcher):
    __slots__ = ("prefixes", "case_sensitive")

    def __init__(self, *prefixes: str, case_sensitive=False):
        self.case_sensitive = case_sensitive
        self.prefixes = tuple(prefixes if case_sensitive else map(str.lower, prefixes))

    def match(self, text):
        candidate = text if self.case_sensitive else text.lower()
        return text if candidate.startswith(self.prefixes) else None


class Regex(Matcher):
    __slots__ = ("pattern",)

    def __init__(self, pattern: str | re.Pattern[str], flags=0):
        self.pattern = (
            re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        )

    def match(self, text):
        return self.pattern.match(text)


class FirstWord(Matcher):
    __slots__ = ("keywords",)
    _separator = re.compile(r"[ \n]")

    def __init__(self, *keywords: str):
        self.keywords = frozenset(map(str.lower, keywords))

    def match(self, text):
        first_word = self._separator.split(text.lower(), 1)[0]
        return text if first_word in self.keywords else None


QUEUE_SYNC: QueueLane = "sync"
QUEUE_IMAGE: QueueLane = "image"
QUEUE_WEB: QueueLane = "web"
QUEUE_LANES = frozenset((QUEUE_SYNC, QUEUE_IMAGE, QUEUE_WEB))


@dataclass(frozen=True, slots=True)
class Command:
    matcher: Matcher
    handler: Callable[..., Any]
    queue: QueueLane = QUEUE_SYNC
    self_only: bool = False
    mention_queryable: bool = False
    addition: bool = True
    rate_limit_key: str | None = None
    name: str = ""

    def __post_init__(self):
        if self.queue not in QUEUE_LANES:
            raise ValueError(f"Unsupported command queue: {self.queue}")

    def try_match(self, text):
        return self.matcher.match(text)


@dataclass(slots=True)
class CommandContext:
    event: Any
    text: str
    user_id: str
    source_type: str
    reply_token: str
    mentioned_user_id: str | None
    has_other_mention: bool
    id_use: str
    mai_ver: str
    mai_ver_use: str
    match: Any = None

    @property
    def is_mention(self):
        return self.id_use != self.user_id
