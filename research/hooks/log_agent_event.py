"""Claude Code hook: record every received event under research/logs/events/.

Registered in .claude/settings.json for UserPromptSubmit, PreToolUse/PostToolUse
(Agent, SendMessage), SubagentStart, and SubagentStop. Each event is its own file
(see eventlog.py) because parallel subagents fire hooks at the same time. The log
is private (git-ignored); collect.py uses transcripts as the source of truth and
these events as a timing cross-check. The hook never blocks: it always exits 0.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eventlog import write_event


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {"unparsed": True}
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    write_event(project, payload)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - a logging hook must never break the session
        print(f"log_agent_event: {exc}", file=sys.stderr)
    sys.exit(0)
