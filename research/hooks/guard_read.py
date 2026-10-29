"""Claude Code PreToolUse hook (Read, Glob, Grep): no reading outside an experiment run.

Inside an experiment run worktree, the main session and subagents may read only files
inside the project folder, and never the research repository or the hidden evaluation
tests. The research session is not restricted. A blocked call exits with code 2 and is
recorded under research/logs/events/.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eventlog import read_payload, write_event
from runscope import is_run_worktree, mentions_research, path_outside

PATH_KEYS = ("file_path", "path", "notebook_path")


def main() -> int:
    payload = read_payload()
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()
    if not is_run_worktree(project):
        return 0
    tool_input = payload.get("tool_input") or {}
    reason = None
    for key in PATH_KEYS:
        value = tool_input.get(key)
        if not isinstance(value, str) or not value:
            continue
        marker = mentions_research(value, project)
        if marker:
            reason = f"blocked: this run may not read {marker}"
        elif path_outside(value, project):
            reason = f"blocked: {value} is outside this project; read only inside it"
        if reason:
            break
    pattern = tool_input.get("pattern")
    if not reason and isinstance(pattern, str):
        marker = mentions_research(pattern, project)
        if marker:
            reason = f"blocked: this run may not read {marker}"
        elif Path(pattern).is_absolute() and path_outside(pattern.split("*", 1)[0] or "/", project):
            reason = f"blocked: {pattern} is outside this project; read only inside it"
    if not reason:
        return 0
    try:
        write_event(
            project,
            {
                "hook_event_name": "GuardBlocked",
                "agent_type": payload.get("agent_type"),
                "agent_id": payload.get("agent_id"),
                "tool_name": payload.get("tool_name"),
                "tool_input": tool_input,
                "reason": reason,
            },
        )
    except OSError:
        pass
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
