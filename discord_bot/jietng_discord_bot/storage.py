from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional


LinkMode = Literal["link", "bind"]
LINK_MODES = frozenset({"link", "bind"})


@dataclass(frozen=True, slots=True)
class LinkRecord:
    jietng_user_id: str
    mode: LinkMode


class LinkStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_links (
                    discord_user_id TEXT PRIMARY KEY,
                    jietng_user_id TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'link',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(user_links)").fetchall()
            }
            if "mode" not in columns:
                conn.execute("ALTER TABLE user_links ADD COLUMN mode TEXT NOT NULL DEFAULT 'link'")
                conn.execute(
                    """
                    UPDATE user_links
                    SET mode = CASE
                        WHEN jietng_user_id = 'discord_' || discord_user_id THEN 'bind'
                        ELSE 'link'
                    END
                    """
                )

    def set_link(
        self,
        discord_user_id: int,
        jietng_user_id: str,
        mode: LinkMode = "link",
    ) -> None:
        jietng_user_id = jietng_user_id.strip()
        if not jietng_user_id:
            raise ValueError("jietng_user_id must not be empty")
        if mode not in LINK_MODES:
            raise ValueError("mode must be 'link' or 'bind'")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_links(discord_user_id, jietng_user_id, mode, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(discord_user_id) DO UPDATE SET
                    jietng_user_id = excluded.jietng_user_id,
                    mode = excluded.mode,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (str(discord_user_id), jietng_user_id, mode),
            )

    def get_record(self, discord_user_id: int) -> Optional[LinkRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT jietng_user_id, mode FROM user_links WHERE discord_user_id = ?",
                (str(discord_user_id),),
            ).fetchone()
        return LinkRecord(row[0], row[1]) if row else None

    def get_link(self, discord_user_id: int) -> Optional[str]:
        record = self.get_record(discord_user_id)
        return record.jietng_user_id if record else None

    def delete_link(self, discord_user_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM user_links WHERE discord_user_id = ?",
                (str(discord_user_id),),
            )
        return cur.rowcount > 0
