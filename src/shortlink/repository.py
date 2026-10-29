"""Link storage."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime

from shortlink.codes import generate_code
from shortlink.db import connect

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True)
class Link:
    code: str
    url: str
    created_at: datetime  # timezone-aware, UTC, second precision


def format_timestamp(value: datetime) -> str:
    """Format a UTC datetime as ISO 8601 with a Z suffix, e.g. "2026-10-29T01:23:45Z"."""
    return value.astimezone(UTC).strftime(TIMESTAMP_FORMAT)


def _parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, TIMESTAMP_FORMAT).replace(tzinfo=UTC)


class LinkRepository:
    """Stores links in the SQLite file at `db_path`. Opens one connection per call."""

    MAX_ATTEMPTS = 10

    def __init__(self, db_path: str, code_factory: Callable[[], str] = generate_code) -> None:
        self.db_path = db_path
        self.code_factory = code_factory

    def create(self, url: str) -> Link:
        """Save `url` under a new code and return the stored Link.

        `url` must already be validated. On a code collision (PRIMARY KEY conflict) a new
        code is drawn, up to MAX_ATTEMPTS times; after that RuntimeError is raised.
        Every call makes a new code, even for a URL that is already stored.
        """
        created_at = datetime.now(UTC).replace(microsecond=0)
        stored_at = format_timestamp(created_at)
        with closing(connect(self.db_path)) as conn:
            for _ in range(self.MAX_ATTEMPTS):
                code = self.code_factory()
                try:
                    with conn:
                        conn.execute(
                            "INSERT INTO links (code, url, created_at) VALUES (?, ?, ?)",
                            (code, url, stored_at),
                        )
                except sqlite3.IntegrityError:
                    continue
                return Link(code=code, url=url, created_at=created_at)
        raise RuntimeError(f"could not find an unused code in {self.MAX_ATTEMPTS} attempts")

    def get(self, code: str) -> Link | None:
        """Return the Link for `code`, or None if there is none."""
        with closing(connect(self.db_path)) as conn:
            row = conn.execute(
                "SELECT code, url, created_at FROM links WHERE code = ?", (code,)
            ).fetchone()
        if row is None:
            return None
        return Link(code=row[0], url=row[1], created_at=_parse_timestamp(row[2]))
