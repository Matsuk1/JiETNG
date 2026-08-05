"""Discover language plugins shipped with the application."""

from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Iterator


def iter_language_plugins() -> Iterator[ModuleType]:
    """Yield modules that expose a LANGUAGE plugin declaration."""
    prefix = f"{__name__}."
    for module_info in sorted(iter_modules(__path__), key=lambda item: item.name):
        if module_info.name.startswith("_"):
            continue
        module = import_module(prefix + module_info.name)
        if hasattr(module, "LANGUAGE"):
            yield module
