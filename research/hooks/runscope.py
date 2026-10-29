"""Shared rules for keeping experiment runs away from research material.

An experiment run happens in a worktree made by research/tools/new_run.py. Such a
worktree has no research/tools/ folder, and its `.git` file points back to the research
repository. Inside a run, agents must not reach the research repository (design docs,
hidden evaluation tests, other runs) through paths or other git refs.
"""

from __future__ import annotations

import re
from pathlib import Path

# Any mention of these in a command or path is research material.
FORBIDDEN_MARKERS = ("research/eval", "agent-pipeline-lab-eval", ".git/worktrees")

# git subcommands that list or switch to other refs, or read raw objects.
FORBIDDEN_GIT_SUBCOMMANDS = {
    "tag", "for-each-ref", "reflog", "worktree", "remote", "fetch", "pull", "ls-remote",
    "switch", "stash", "show-ref", "cat-file", "replace", "notes", "bundle", "fsck",
}  # fmt: skip
# Arguments that name refs other than the run's own HEAD.
REF_ARG_RE = re.compile(
    r"^(?:--all|--branches|--remotes|--tags|--glob(?:=.*)?|--exclude(?:=.*)?|main|master|origin)$"
    r"|^(?:main|master|origin|refs|run|baseline-[^ ]*)(?:[:/~^]|\.\.)"
    r"|\.\.\.?(?:main|master|origin)\b"
    r"|@\{"
)
SEGMENT_SPLIT_RE = re.compile(r"[;&|\n()`]|\$\(")


def is_run_worktree(project: Path) -> bool:
    return not (project / "research" / "tools").is_dir()


def normalize(text: str) -> str:
    """Lowercase, forward slashes, and Git Bash drive form (/c/...) as c:/..."""
    text = text.replace("\\\\", "/").replace("\\", "/").lower()
    return re.sub(r"(?<![a-z0-9])/([a-z])/", r"\1:/", text)


def research_root(project: Path) -> str | None:
    """The research repository this run worktree belongs to (from its .git file)."""
    git_file = project / ".git"
    if not git_file.is_file():
        return None
    line = git_file.read_text(encoding="utf-8", errors="replace").strip()
    if not line.startswith("gitdir:"):
        return None
    gitdir = normalize(line.split(":", 1)[1].strip())
    marker = "/.git/worktrees/"
    return gitdir.split(marker, 1)[0] if marker in gitdir else None


def mentions_research(text: str, project: Path) -> str | None:
    norm = normalize(text)
    for marker in FORBIDDEN_MARKERS:
        if marker in norm:
            return marker
    root = research_root(project)
    # The root must end at a path boundary: run folders live next to the research
    # repository (".../agent-pipeline-lab-runs/..."), so a plain substring test would
    # wrongly match every absolute path inside the run itself.
    if root and re.search(re.escape(root) + r"(?![a-z0-9._-])", norm):
        return "the research repository path"
    return None


def git_violation(command: str) -> str | None:
    """Reason a command reaches other refs, or None."""
    for segment in SEGMENT_SPLIT_RE.split(command):
        tokens = segment.split()
        for i, tok in enumerate(tokens):
            if tok.rsplit("/", 1)[-1].lower() not in ("git", "git.exe"):
                continue
            j = i + 1
            while j < len(tokens) and tokens[j].startswith("-"):
                j += 2 if tokens[j] in ("-C", "-c", "--git-dir", "--work-tree") else 1
            if j >= len(tokens):
                break
            sub, rest = tokens[j], [t.strip("'\"") for t in tokens[j + 1 :]]
            if sub in FORBIDDEN_GIT_SUBCOMMANDS:
                return f"git {sub}"
            if sub == "branch" and rest != ["--show-current"]:
                return "git branch (only `git branch --show-current` is allowed)"
            if sub == "checkout" and rest and not rest[0].startswith("-"):
                return "git checkout of another ref (use `git checkout -- <file>`)"
            for arg in rest:
                if REF_ARG_RE.search(arg):
                    return f"git {sub} {arg}"
            break
    return None


def path_outside(path_text: str, project: Path) -> bool:
    candidate = Path(path_text)
    if not candidate.is_absolute():
        candidate = project / candidate
    try:
        candidate.resolve().relative_to(project.resolve())
    except ValueError:
        return True
    return False
