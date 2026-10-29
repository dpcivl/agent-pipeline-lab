"""Claude Code PreToolUse hook: keep each subagent inside its write area.

Write areas follow docs/00-pipeline-design.md section 7.3. Rules apply only inside
subagents; the main session is not restricted here. Subagents of the types listed
below are limited to their write areas, and every subagent is blocked from writing
outside the project folder.

A blocked call exits with code 2; Claude Code shows the stderr message to the
agent. Every block is also recorded under research/logs/events/.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eventlog import write_event

WRITE_AREAS = {
    "implementer": ("src/shortlink/", "pyproject.toml", "uv.lock"),
    "test-writer": ("tests/",),
    "doc-keeper": ("docs/service.md", "CHANGELOG.md"),
    "tester": (),
    "reviewer": (),
    "qa": (),
    "security": (),
}


def log_block(project: Path, payload: dict, reason: str) -> None:
    write_event(
        project,
        {
            "hook_event_name": "GuardBlocked",
            "agent_type": payload.get("agent_type"),
            "agent_id": payload.get("agent_id"),
            "tool_name": payload.get("tool_name"),
            "tool_input": payload.get("tool_input"),
            "reason": reason,
        },
    )


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    agent_type = payload.get("agent_type")
    if not agent_type:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()
    tool_input = payload.get("tool_input") or {}
    raw_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not raw_path:
        return 0
    target = Path(raw_path)
    if not target.is_absolute():
        target = project / target
    target = target.resolve()

    try:
        rel = target.relative_to(project).as_posix()
    except ValueError:
        reason = f"blocked: {raw_path} is outside the project folder"
        log_block(project, payload, reason)
        print(reason, file=sys.stderr)
        return 2

    if agent_type not in WRITE_AREAS:
        return 0
    allowed = WRITE_AREAS[agent_type]
    if any(rel == a or (a.endswith("/") and rel.startswith(a)) for a in allowed):
        return 0
    areas = ", ".join(allowed) if allowed else "none (read-only role)"
    reason = f"blocked: {agent_type} may not write {rel}. Allowed write area: {areas}"
    log_block(project, payload, reason)
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
