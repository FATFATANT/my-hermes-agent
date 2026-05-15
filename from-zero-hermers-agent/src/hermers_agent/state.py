from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermers_agent.llm import Message


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SessionSummary:
    id: str
    title: str
    updated_at: str
    message_count: int
    preview: str = ""


class SessionStore:
    """Tiny SQLite session store for the learning implementation."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def create_session(self, title: str) -> str:
        session_id = uuid.uuid4().hex
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, title, now, now),
            )
        return session_id

    def append_messages(self, session_id: str, messages: list[Message]) -> None:
        if not messages:
            return

        now = utc_now()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            position = int(row[0])
            for message in messages:
                conn.execute(
                    """
                    INSERT INTO messages
                        (session_id, position, role, content, message_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        position,
                        str(message.get("role", "")),
                        _message_content(message),
                        json.dumps(message),
                        now,
                    ),
                )
                position += 1
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )

    def get_messages(self, session_id: str) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT message_json
                FROM messages
                WHERE session_id = ?
                ORDER BY position ASC
                """,
                (session_id,),
            ).fetchall()
        # row[0]就是取message_json这个字段
        return [json.loads(row[0]) for row in rows]

    def list_sessions(self, limit: int = 10) -> list[SessionSummary]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT s.id, s.title, s.updated_at, COUNT(m.id) AS message_count
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            SessionSummary(
                id=str(row[0]),
                title=str(row[1]),
                updated_at=str(row[2]),
                message_count=int(row[3]),
            )
            for row in rows
        ]

    def search_sessions(self, query: str, limit: int = 10) -> list[SessionSummary]:
        pattern = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    s.id,
                    s.title,
                    s.updated_at,
                    COUNT(m_all.id) AS message_count,
                    COALESCE(MIN(m_match.content), '') AS preview
                FROM sessions s
                LEFT JOIN messages m_all ON m_all.session_id = s.id
                LEFT JOIN messages m_match
                    ON m_match.session_id = s.id
                    AND m_match.content LIKE ?
                WHERE s.title LIKE ? OR m_match.id IS NOT NULL
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()
        return [
            SessionSummary(
                id=str(row[0]),
                title=str(row[1]),
                updated_at=str(row[2]),
                message_count=int(row[3]),
                preview=str(row[4]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            # 会话元信息表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            # 会话消息表，position是这条消息在会话中的顺序
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_session_position
                ON messages(session_id, position)
                """
            )


def _message_content(message: dict[str, Any]) -> str:
    content = message.get("content")
    if content is None:
        return ""
    return str(content)
