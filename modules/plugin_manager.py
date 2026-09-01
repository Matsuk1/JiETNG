"""Local plugin loading for lightweight user-defined bot commands."""

from __future__ import annotations

import importlib.util
import inspect
import logging
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from linebot.v3.messaging import TextMessage

from modules.commands.command_router import Command, CommandContext, Exact, Matcher, Prefix, Regex

logger = logging.getLogger(__name__)

PluginHandler = Callable[..., Any]
SessionHandler = Callable[..., Any]
SessionScope = str

_sessions: dict[tuple[str, str], "PluginSession"] = {}
_sessions_lock = threading.Lock()


@dataclass(slots=True)
class PluginCommandRegistry:
    before_core: list[Command] = field(default_factory=list)
    after_core: list[Command] = field(default_factory=list)

    def add(self, command: Command, *, before_core: bool = False) -> None:
        target = self.before_core if before_core else self.after_core
        target.append(command)


class PluginAPI:
    """Small API exposed to local plugin modules."""

    def __init__(self, plugin_name: str, registry: PluginCommandRegistry):
        self.plugin_name = plugin_name
        self._registry = registry

    def text(self, value: str) -> TextMessage:
        return TextMessage(text=str(value))

    def command(
        self,
        matcher: str | Matcher,
        handler: PluginHandler,
        *,
        name: str | None = None,
        before_core: bool = False,
        mention_queryable: bool = False,
        self_only: bool = False,
        rate_limit_key: str | None = None,
        addition: bool = True,
    ) -> Command:
        command = Command(
            _coerce_matcher(matcher),
            _wrap_handler(handler, self),
            mention_queryable=mention_queryable,
            self_only=self_only,
            rate_limit_key=rate_limit_key,
            addition=addition,
            name=name or f"plugin:{self.plugin_name}",
        )
        self._registry.add(command, before_core=before_core)
        return command

    def exact(self, *keywords: str, **options) -> Command:
        return self.command(Exact(*keywords), **options)

    def prefix(self, *prefixes: str, **options) -> Command:
        return self.command(Prefix(*prefixes), **options)

    def regex(self, pattern: str | re.Pattern[str], flags=0, **options) -> Command:
        return self.command(Regex(pattern, flags), **options)

    def start_session(
        self,
        ctx: CommandContext,
        handler: SessionHandler,
        *,
        state: dict[str, Any] | None = None,
        ttl: int = 1800,
        scope: SessionScope = "chat",
    ) -> "PluginSession":
        session = PluginSession(
            key=_session_key(ctx, scope),
            plugin_name=self.plugin_name,
            handler=_wrap_session_handler(handler, self),
            api=self,
            state=dict(state or {}),
            ttl=max(1, int(ttl)),
            expires_at=time.monotonic() + max(1, int(ttl)),
        )
        with _sessions_lock:
            _sessions[session.key] = session
        return session

    def get_session(
        self,
        ctx: CommandContext,
        *,
        scope: SessionScope = "chat",
    ) -> "PluginSession | None":
        return get_plugin_session(ctx, scope=scope, plugin_name=self.plugin_name)

    def end_session(self, ctx: CommandContext, *, scope: SessionScope = "chat") -> None:
        key = _session_key(ctx, scope)
        with _sessions_lock:
            session = _sessions.get(key)
            if session and session.plugin_name == self.plugin_name:
                _sessions.pop(key, None)


@dataclass(slots=True)
class PluginSession:
    key: tuple[str, str]
    plugin_name: str
    handler: Callable[[CommandContext, "PluginSession"], Any]
    api: PluginAPI
    state: dict[str, Any]
    ttl: int
    expires_at: float
    ended: bool = False

    def touch(self, ttl: int | None = None) -> None:
        if ttl is not None:
            self.ttl = max(1, int(ttl))
        self.expires_at = time.monotonic() + self.ttl

    def end(self) -> None:
        self.ended = True
        with _sessions_lock:
            _sessions.pop(self.key, None)


def _coerce_matcher(matcher: str | Matcher) -> Matcher:
    if isinstance(matcher, Matcher):
        return matcher
    if isinstance(matcher, str):
        return Exact(matcher)
    raise TypeError("Plugin command matcher must be a string or Matcher instance")


def _wrap_handler(handler: PluginHandler, api: PluginAPI) -> Callable[[Any], Any]:
    signature = inspect.signature(handler)
    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    accepts_api = len(positional) >= 2 or any(
        parameter.kind == parameter.VAR_POSITIONAL
        for parameter in signature.parameters.values()
    )

    def run(ctx):
        try:
            return handler(ctx, api) if accepts_api else handler(ctx)
        except Exception:
            logger.exception("[Plugin] command failed: plugin=%s", api.plugin_name)
            return TextMessage(text="插件命令执行失败，请稍后再试。")

    return run


def _wrap_session_handler(
    handler: SessionHandler,
    api: PluginAPI,
) -> Callable[[CommandContext, PluginSession], Any]:
    signature = inspect.signature(handler)
    positional = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    has_varargs = any(
        parameter.kind == parameter.VAR_POSITIONAL
        for parameter in signature.parameters.values()
    )

    def run(ctx, session):
        if len(positional) >= 3 or has_varargs:
            return handler(ctx, session, api)
        if len(positional) >= 2:
            return handler(ctx, session)
        return handler(ctx)

    return run


def _source_id(ctx: CommandContext) -> str:
    if ctx.source_type == "group":
        value = getattr(ctx.event.source, "group_id", None)
    elif ctx.source_type == "room":
        value = getattr(ctx.event.source, "room_id", None)
    else:
        value = ctx.user_id
    return str(value or ctx.user_id)


def _session_key(ctx: CommandContext, scope: SessionScope) -> tuple[str, str]:
    if scope == "chat":
        return ("chat", _source_id(ctx))
    if scope == "user":
        return ("user", ctx.user_id)
    if scope in ("user_chat", "user-in-chat"):
        return ("user_chat", f"{_source_id(ctx)}:{ctx.user_id}")
    raise ValueError("Plugin session scope must be chat, user, or user_chat")


def _purge_expired_sessions(now: float | None = None) -> None:
    now = time.monotonic() if now is None else now
    with _sessions_lock:
        expired = [
            key for key, session in _sessions.items()
            if session.ended or session.expires_at <= now
        ]
        for key in expired:
            _sessions.pop(key, None)


def get_plugin_session(
    ctx: CommandContext,
    *,
    scope: SessionScope = "chat",
    plugin_name: str | None = None,
) -> PluginSession | None:
    _purge_expired_sessions()
    key = _session_key(ctx, scope)
    with _sessions_lock:
        session = _sessions.get(key)
    if session and (plugin_name is None or session.plugin_name == plugin_name):
        return session
    return None


def dispatch_plugin_session(ctx: CommandContext) -> Any:
    if ctx.text.startswith("/"):
        return None

    candidates = ("user_chat", "chat", "user")
    for scope in candidates:
        session = get_plugin_session(ctx, scope=scope)
        if session is None:
            continue
        try:
            reply = session.handler(ctx, session)
            if session.ended:
                session.end()
            else:
                session.touch()
            return reply
        except Exception:
            logger.exception(
                "[Plugin] session handler failed: plugin=%s scope=%s",
                session.plugin_name,
                scope,
            )
            session.end()
            return TextMessage(text="插件会话执行失败，已自动结束。")
    return None


def _plugin_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []

    files = [
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix == ".py"
        and not path.name.startswith("_")
    ]
    packages = [
        path / "__init__.py"
        for path in directory.iterdir()
        if path.is_dir()
        and not path.name.startswith("_")
        and (path / "__init__.py").is_file()
    ]
    return sorted([*files, *packages])


def _load_module(path: Path, module_name: str) -> ModuleType:
    kwargs = {}
    if path.name == "__init__.py":
        kwargs["submodule_search_locations"] = [str(path.parent)]
    spec = importlib.util.spec_from_file_location(module_name, path, **kwargs)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plugin from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def load_plugin_commands(config: dict[str, Any] | None) -> PluginCommandRegistry:
    registry = PluginCommandRegistry()
    config = config or {}
    if not config.get("enabled", True):
        logger.info("[Plugin] Local plugins disabled")
        return registry

    directories = config.get("directories") or ["./plugins"]
    for raw_directory in directories:
        directory = Path(str(raw_directory)).expanduser()
        if not directory.is_absolute():
            directory = Path(os.getcwd()) / directory
        for path in _plugin_files(directory):
            plugin_name = path.parent.name if path.name == "__init__.py" else path.stem
            try:
                module = _load_module(
                    path,
                    f"jietng_local_plugin_{plugin_name}_{abs(hash(str(path)))}",
                )
                if getattr(module, "ENABLED", True) is False:
                    logger.info("[Plugin] skipped disabled plugin: %s", plugin_name)
                    continue
                register = getattr(module, "register", None)
                if not callable(register):
                    logger.warning("[Plugin] missing register(api): %s", path)
                    continue
                before_count = len(registry.before_core)
                after_count = len(registry.after_core)
                register(PluginAPI(plugin_name, registry))
                logger.info(
                    "[Plugin] loaded %s: before_core=%s after_core=%s",
                    plugin_name,
                    len(registry.before_core) - before_count,
                    len(registry.after_core) - after_count,
                )
            except Exception:
                logger.exception("[Plugin] failed to load plugin: %s", path)
    return registry
