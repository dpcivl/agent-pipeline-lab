"""Regression tests for the run-isolation hooks (research/hooks).

The layout mirrors the real one: run worktrees sit next to the research repository, in
a folder whose name starts with the repository's name (agent-pipeline-lab-runs). An
earlier version matched the repository path as a plain substring and blocked every
absolute path inside the run (F1-auto-r1, 2026-10-29).

Run: uv run pytest research/infra_tests -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOKS))
from runscope import git_violation, mentions_research


@pytest.fixture
def layout(tmp_path: Path) -> dict[str, Path]:
    research = tmp_path / "dev" / "agent-pipeline-lab"
    (research / "research" / "tools").mkdir(parents=True)
    (research / "research" / "eval" / "F1").mkdir(parents=True)
    run = tmp_path / "dev" / "agent-pipeline-lab-runs" / "F1-auto-r1"
    (run / "docs" / "features").mkdir(parents=True)
    (run / "docs" / "features" / "F1.md").write_text("spec", encoding="utf-8")
    gitdir = (research / ".git" / "worktrees" / "F1-auto-r1").as_posix()
    (run / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    return {"research": research, "run": run}


def run_hook(script: str, project: Path, payload: dict) -> int:
    env = {"CLAUDE_PROJECT_DIR": str(project), "PYTHONIOENCODING": "utf-8", "SYSTEMROOT": ""}
    import os

    env = {**os.environ, **env}
    proc = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(payload).encode("utf-8"),
        env=env,
        capture_output=True,
        check=False,
    )
    return proc.returncode


def test_absolute_path_inside_run_is_not_research(layout):
    run = layout["run"]
    inside = (run / "docs" / "features" / "F1.md").as_posix()
    assert mentions_research(inside, run) is None
    assert mentions_research(str(run / "docs" / "features" / "F1.md"), run) is None


@pytest.mark.parametrize(
    "suffix",
    ["", "/docs/00-pipeline-design.md", "/research/runs", "\\README.md"],
)
def test_research_repository_paths_are_caught(layout, suffix):
    research, run = layout["research"], layout["run"]
    assert mentions_research(research.as_posix() + suffix.replace("\\", "/"), run)
    assert mentions_research(str(research) + suffix, run)


def test_git_bash_drive_form_is_caught(layout):
    research, run = layout["research"], layout["run"]
    posix = research.as_posix()
    if posix[1:3] == ":/":  # Windows: C:/Users/... -> /c/Users/...
        bash_form = f"/{posix[0].lower()}/{posix[3:]}"
        assert mentions_research(f"ls {bash_form}/research", run)


def test_eval_marker_is_caught(layout):
    assert mentions_research("cat research/eval/F1/README.md", layout["run"])


def test_guard_read_allows_absolute_path_inside_run(layout):
    run = layout["run"]
    payload = {"tool_name": "Read", "tool_input": {"file_path": str(run / "docs/features/F1.md")}}
    assert run_hook("guard_read.py", run, payload) == 0


def test_guard_read_blocks_research_repository(layout):
    run, research = layout["run"], layout["research"]
    payload = {"tool_name": "Read", "tool_input": {"file_path": str(research / "README.md")}}
    assert run_hook("guard_read.py", run, payload) == 2


def test_guard_read_allows_glob_and_grep_inside_run(layout):
    run = layout["run"]
    glob = {"tool_name": "Glob", "tool_input": {"pattern": "**/*.md", "path": str(run)}}
    grep = {"tool_name": "Grep", "tool_input": {"pattern": "AC-1", "path": str(run / "docs")}}
    assert run_hook("guard_read.py", run, glob) == 0
    assert run_hook("guard_read.py", run, grep) == 0


def test_guard_bash_allows_commands_with_absolute_paths_inside_run(layout):
    run = layout["run"]
    command = f'cat "{(run / "docs/features/F1.md").as_posix()}" && uv run pytest -q'
    payload = {"agent_type": "tester", "tool_input": {"command": command}}
    assert run_hook("guard_bash.py", run, payload) == 0


def test_guard_bash_blocks_research_path_and_other_refs(layout):
    run, research = layout["run"], layout["research"]
    for command in (f"cat {research.as_posix()}/README.md", "git log --all", "git show main:x"):
        payload = {"agent_type": "reviewer", "tool_input": {"command": command}}
        assert run_hook("guard_bash.py", run, payload) == 2, command


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("git log --oneline", False),
        ("git diff abc123..HEAD -- src/shortlink/main.py", False),
        ("git add -A --sparse && git commit -m 'wip(F1): 3 push fix'", False),
        ("git branch --show-current", False),
        ("git log --all", True),
        ("git branch", True),
        ("git show main:research/eval/F1/README.md", True),
        ("git diff main...HEAD", True),
        ("git log run/F1-human-r1", True),
        ("git stash list", True),
    ],
)
def test_git_violation(command, blocked):
    assert (git_violation(command) is not None) == blocked
