from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class LinkStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
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
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def set_link(self, discord_user_id: int, jietng_user_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_links(discord_user_id, jietng_user_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(discord_user_id) DO UPDATE SET
                    jietng_user_id = excluded.jietng_user_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (str(discord_user_id), jietng_user_id),
            )

    def get_link(self, discord_user_id: int) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT jietng_user_id FROM user_links WHERE discord_user_id = ?",
                (str(discord_user_id),),
            ).fetchone()
        return row[0] if row else None

    def delete_link(self, discord_user_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM user_links WHERE discord_user_id = ?",
                (str(discord_user_id),),
            )
        return cur.rowcount > 0
