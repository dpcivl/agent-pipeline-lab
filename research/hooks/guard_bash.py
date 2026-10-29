"""Claude Code PreToolUse hook (Bash): block `git push` during experiments.

`git push` is blocked when either holds:
- the command runs inside a subagent (the hook input has `agent_type`), or
- the session runs in an experiment worktree. Worktrees made by
  research/tools/new_run.py are sparse and have no research/tools/ folder.

The research session in the main repository can push. A blocked call exits with
code 2, Claude Code shows the stderr message to the agent, and the block is
recorded under research/logs/events/.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eventlog import read_payload, write_event

# `git push`, also with options before the subcommand (git -C dir push, git -c k=v push).
GIT_PUSH_RE = re.compile(r"(?:^|[;&|(\s])git(?:\s+-{1,2}\S+(?:\s+(?!push\b)\S+)?)*\s+push\b")


def is_run_worktree(project: Path) -> bool:
    return not (project / "research" / "tools").is_dir()


def main() -> int:
    payload = read_payload()
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

    try:
        write_event(
            project,
            {
                "hook_event_name": "GuardBlocked",
                "agent_type": agent_type,
                "agent_id": payload.get("agent_id"),
                "tool_name": payload.get("tool_name"),
                "tool_input": payload.get("tool_input"),
                "reason": reason,
            },
        )
    except OSError:
        pass  # logging must not weaken the block
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
