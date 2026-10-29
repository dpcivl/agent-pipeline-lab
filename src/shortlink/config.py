"""Application settings.

FIXED CONTRACT (see docs/00-pipeline-design.md section 7.2):
- Keep the class name `Settings`, its existing fields, their environment variable
  names, and `Settings.from_env()`.
- Adding new fields is allowed. Renaming or removing existing ones is not.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_DB_PATH = "shortlink.db"
DEFAULT_BASE_URL = "http://localhost:8000"


@dataclass(frozen=True)
class Settings:
    db_path: str = DEFAULT_DB_PATH  # env: SHORTLINK_DB_PATH
    base_url: str = DEFAULT_BASE_URL  # env: SHORTLINK_BASE_URL (no trailing slash)

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            db_path=os.environ.get("SHORTLINK_DB_PATH", DEFAULT_DB_PATH),
            base_url=os.environ.get("SHORTLINK_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        )
