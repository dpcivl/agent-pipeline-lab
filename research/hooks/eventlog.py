"""Shared event writer for the research hooks.

Hooks run as separate processes, often in parallel (several subagents at once).
Appending to one shared file from many processes interleaves lines on Windows, so
each event is written to its own file:

  research/logs/events/<UTC timestamp>-<pid>-<random>.json

Read them in order with read_events(). The folder is private (git-ignored).
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path


def events_dir(project: Path) -> Path:
    return project / "research" / "logs" / "events"


def write_event(project: Path, payload: dict) -> Path:
    now = datetime.now(UTC)
    payload = {**payload, "received_at": now.isoformat(timespec="milliseconds")}
    folder = events_dir(project)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{os.getpid()}-{secrets.token_hex(3)}.json"
    path = folder / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)  # the event file appears complete or not at all
    return path


def read_events(project: Path) -> list[dict]:
    events = []
    for path in sorted(events_dir(project).glob("*.json")):
        try:
            events.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return events
