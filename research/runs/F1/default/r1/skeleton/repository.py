"""Persistence of links in SQLite."""

from __future__ import annotations

from dataclasses import dataclass

MAX_CODE_ATTEMPTS = 10


@dataclass(frozen=True)
class Link:
    code: str
    url: str
    created_at: str  # UTC, 'YYYY-MM-DDTHH:MM:SSZ'


class LinkRepository:
    """Stores and looks up links in the SQLite file at ``db_path``."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def create(self, url: str) -> Link:
        """Store ``url`` under a new random code and return the stored link.

        Regenerates the code when it collides with an existing one, up to
        ``MAX_CODE_ATTEMPTS`` times, then raises ``RuntimeError``.
        """
        raise NotImplementedError

    def get(self, code: str) -> Link | None:
        """Return the link stored under ``code``, or ``None`` if there is none."""
        raise NotImplementedError
