"""SQLite connection and schema management (standard library sqlite3, no ORM)."""

from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    code       TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def connect(db_path: str) -> sqlite3.Connection:
    """Open a new connection to the SQLite file at ``db_path``.

    Callers own the connection and must close it. Connections are not shared
    between requests.
    """
    raise NotImplementedError


def init_schema(db_path: str) -> None:
    """Create the ``links`` table at ``db_path`` if it does not exist yet."""
    raise NotImplementedError
