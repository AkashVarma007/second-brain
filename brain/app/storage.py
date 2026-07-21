"""SQLite persistence for notes and tasks. No HTTP and no AI live here."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app.models import NoteOut, TaskOut

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    priority TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(db_path: Path | str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect(db_path)) as conn, conn:
        conn.executescript(SCHEMA)


def save_note(db_path: Path | str, text: str) -> NoteOut:
    created_at = _now()
    with closing(_connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO notes (text, created_at) VALUES (?, ?)", (text, created_at)
        )
    return NoteOut(id=cursor.lastrowid, text=text, created_at=created_at)


def save_task(db_path: Path | str, title: str, priority: str) -> TaskOut:
    created_at = _now()
    with closing(_connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, priority, created_at) VALUES (?, ?, ?)",
            (title, priority, created_at),
        )
    return TaskOut(id=cursor.lastrowid, title=title, priority=priority, created_at=created_at)


def list_notes(db_path: Path | str) -> list[NoteOut]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT id, text, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
    return [NoteOut(**dict(row)) for row in rows]


def list_tasks(db_path: Path | str) -> list[TaskOut]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT id, title, priority, created_at FROM tasks ORDER BY id DESC"
        ).fetchall()
    return [TaskOut(**dict(row)) for row in rows]
