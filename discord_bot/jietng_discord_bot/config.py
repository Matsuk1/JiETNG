from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


DEFAULT_BASE_URL = "https://jietng-endpoint.matsuk1.com/api/v2"


@dataclass(frozen=True)
class BotConfig:
    discord_token: str
    jietng_token: str
    jietng_base_url: str
    guild_id: Optional[int]
    db_path: Path


def _optional_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("JIETNG_DISCORD_GUILD_ID must be an integer") from exc


def load_config() -> BotConfig:
    discord_token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    jietng_token = os.getenv("JIETNG_API_TOKEN", "").strip()
    if not discord_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required")
    if not jietng_token:
        raise RuntimeError("JIETNG_API_TOKEN is required")

    db_path = Path(os.getenv("JIETNG_DISCORD_DB", "data/bot.sqlite3")).expanduser()
    return BotConfig(
        discord_token=discord_token,
        jietng_token=jietng_token,
        jietng_base_url=os.getenv("JIETNG_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/"),
        guild_id=_optional_int(os.getenv("JIETNG_DISCORD_GUILD_ID")),
        db_path=db_path,
    )
