"""SQLite access (standard library sqlite3, no ORM).

Schema:
    CREATE TABLE IF NOT EXISTS links (
        code       TEXT PRIMARY KEY,
        url        TEXT NOT NULL,
        created_at TEXT NOT NULL   -- UTC, "YYYY-MM-DDTHH:MM:SSZ"
    )
"""

from __future__ import annotations

import sqlite3
from contextlib import closing


def connect(db_path: str) -> sqlite3.Connection:
    """Open a new connection to `db_path`. The caller must close it."""
    return sqlite3.connect(db_path)


def init_schema(db_path: str) -> None:
    """Create the `links` table if it does not exist. Safe to call repeatedly."""
    # `with conn` commits the transaction; closing() releases the connection.
    with closing(connect(db_path)) as conn, conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS links ("
            "code TEXT PRIMARY KEY, "
            "url TEXT NOT NULL, "
            "created_at TEXT NOT NULL)"
        )
