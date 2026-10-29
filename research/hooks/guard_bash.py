"""Claude Code PreToolUse hook (Bash): keep experiments away from git push and research data.

Blocked:
- `git push` inside any subagent, and anywhere in an experiment run worktree.
- Inside an experiment run worktree (main session and subagents):
  - git commands that list or reach other refs (`--all`, `main`, other `run/` branches,
    tags, `git branch`, `git stash`, raw object reads, ...); see runscope.py
  - any command that mentions the research repository path or the hidden evaluation tests

The research session in the main repository is not restricted (except push from its
subagents). A blocked call exits with code 2, Claude Code shows the stderr message to
the agent, and the block is recorded under research/logs/events/.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eventlog import read_payload, write_event
from runscope import git_violation, is_run_worktree, mentions_research

# `git push`, also with options before the subcommand (git -C dir push, git -c k=v push).
GIT_PUSH_RE = re.compile(r"(?:^|[;&|(\s])git(?:\s+-{1,2}\S+(?:\s+(?!push\b)\S+)?)*\s+push\b")


def reason_for(command: str, project: Path, agent_type: str | None) -> str | None:
    in_run = is_run_worktree(project)
    if GIT_PUSH_RE.search(command):
        if agent_type:
            return f"blocked: subagents may not run git push ({agent_type})"
        if in_run:
            return "blocked: git push is not allowed in an experiment run worktree"
    if not in_run:
        return None
    marker = mentions_research(command, project)
    if marker:
        return f"blocked: this run may not access {marker}; work only inside this project"
    violation = git_violation(command)
    if violation:
        return (
            f"blocked: {violation} reaches other branches or history; use only this branch (HEAD)"
        )
    return None


def main() -> int:
    payload = read_payload()
    command = (payload.get("tool_input") or {}).get("command") or ""
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()
    agent_type = payload.get("agent_type")
    reason = reason_for(command, project, agent_type)
    if not reason:
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
