"""Claude Code PreToolUse hook (Bash): block `git push` during experiments.

`git push` is blocked when either holds:
- the command runs inside a subagent (the hook input has `agent_type`), or
- the session runs in an experiment worktree. Worktrees made by
  research/tools/new_run.py are sparse and have no research/tools/ folder.

The research session in the main repository can push. A blocked call exits with
code 2, Claude Code shows the stderr message to the agent, and the block is
appended to research/logs/agent-events.jsonl.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

# `git push`, also with options before the subcommand (git -C dir push, git -c k=v push).
GIT_PUSH_RE = re.compile(r"(?:^|[;&|(\s])git(?:\s+-{1,2}\S+(?:\s+(?!push\b)\S+)?)*\s+push\b")


def is_run_worktree(project: Path) -> bool:
    return not (project / "research" / "tools").is_dir()


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not GIT_PUSH_RE.search(command):
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()
    agent_type = payload.get("agent_type")
    if agent_type:
        reason = f"blocked: subagents may not run git push ({agent_type})"
    elif is_run_worktree(project):
        reason = "blocked: git push is not allowed in an experiment run worktree"
    else:
        return 0

    log_dir = project / "research" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "hook_event_name": "GuardBlocked",
        "received_at": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "agent_type": agent_type,
        "agent_id": payload.get("agent_id"),
        "tool_name": payload.get("tool_name"),
        "tool_input": payload.get("tool_input"),
        "reason": reason,
    }
    with (log_dir / "agent-events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
