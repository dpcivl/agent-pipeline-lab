"""Claude Code hook: append every received event to research/logs/agent-events.jsonl.

Registered in .claude/settings.json for UserPromptSubmit, PreToolUse/PostToolUse
(Agent, SendMessage), SubagentStart, and SubagentStop. The log is private
(git-ignored); collect.py uses transcripts as the source of truth and this log
as a timing cross-check. The hook never blocks: it always exits 0.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {"unparsed": True}
    payload["received_at"] = datetime.now(UTC).isoformat(timespec="milliseconds")
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    log_dir = project / "research" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "agent-events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - a logging hook must never break the session
        print(f"log_agent_event: {exc}", file=sys.stderr)
    sys.exit(0)
