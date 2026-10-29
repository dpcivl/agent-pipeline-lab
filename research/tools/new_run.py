"""Create an isolated worktree for one pipeline run.

The worktree contains only what the agents need (sparse checkout): the service code,
tests, agent definitions, hooks, plans, and the spec of the current feature. Research
documents and other features' specs are left out so they cannot influence the agents.

Usage:
  uv run python research/tools/new_run.py F1 auto 1 [--base <commit-or-tag>]

Modes: auto (no human), human (human at H1-H4), default (human approves the plan only).
Writes research/runs/<feature>/<mode>/r<rep>/run.json with the base commit and config hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_ROOT = REPO.parent / f"{REPO.name}-runs"
MODES = ("auto", "human", "default")
# Files whose content must be identical across runs being compared.
CONFIG_PATHS = (
    "CLAUDE.md",
    "pyproject.toml",
    "uv.lock",
    ".claude",
    "research/hooks",
    "src/shortlink/main.py",
    "src/shortlink/config.py",
    "tests/conftest.py",
)


def git(*args: str, cwd: Path = REPO) -> str:
    result = subprocess.run(["git", *args], check=False, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def sparse_patterns(feature: str) -> list[str]:
    return [
        "/CLAUDE.md",
        "/pyproject.toml",
        "/uv.lock",
        "/.python-version",
        "/.gitignore",
        "/CHANGELOG.md",
        "/src/",
        "/tests/",
        "/.claude/",
        "/research/hooks/",
        "/docs/plans/",
        "/docs/service.md",
        "/docs/features/README.md",
        f"/docs/features/{feature}.md",
    ]


def config_hashes(base: str) -> dict[str, str]:
    """sha256 of each tracked config file at the base commit."""
    listing = git("ls-tree", "-r", "--name-only", base, "--", *CONFIG_PATHS)
    hashes = {}
    for path in sorted(listing.splitlines()):
        blob = subprocess.run(
            ["git", "show", f"{base}:{path}"], check=False, cwd=REPO, capture_output=True
        )
        hashes[path] = hashlib.sha256(blob.stdout).hexdigest()
    return hashes


def claude_version() -> str:
    exe = shutil.which("claude")
    if not exe:
        candidates = sorted(
            Path.home().glob("AppData/Local/Claude-Data/*/claude-code/*/*/claude.exe")
        )
        exe = str(candidates[-1]) if candidates else None
    if not exe:
        return "unknown"
    out = subprocess.run([exe, "--version"], check=False, capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("feature", help="feature id, e.g. F1")
    ap.add_argument("mode", choices=MODES)
    ap.add_argument("rep", type=int, help="repetition number, e.g. 1")
    ap.add_argument("--base", default="HEAD", help="commit or tag to start from")
    ap.add_argument("--runs-root", default=str(DEFAULT_RUNS_ROOT))
    ap.add_argument("--allow-missing-spec", action="store_true", help="for tooling tests only")
    ap.add_argument("--no-sync", action="store_true", help="skip uv sync in the worktree")
    args = ap.parse_args()

    if not re.fullmatch(r"F\d+", args.feature):
        sys.exit("feature must look like F1")
    name = f"{args.feature}-{args.mode}-r{args.rep}"
    branch = f"run/{name}"
    worktree = Path(args.runs_root) / name
    run_dir = REPO / "research" / "runs" / args.feature / args.mode / f"r{args.rep}"
    if worktree.exists() or (run_dir / "run.json").exists():
        sys.exit(f"run already exists: {worktree} or {run_dir / 'run.json'}")

    base = git("rev-parse", "--verify", f"{args.base}^{{commit}}")
    spec = f"docs/features/{args.feature}.md"
    has_spec = (
        subprocess.run(
            ["git", "cat-file", "-e", f"{base}:{spec}"], check=False, cwd=REPO
        ).returncode
        == 0
    )
    if not has_spec and not args.allow_missing_spec:
        sys.exit(f"{spec} is not in the base commit {base[:8]}")

    worktree.parent.mkdir(parents=True, exist_ok=True)
    git("worktree", "add", "--no-checkout", "-b", branch, str(worktree), base)
    git("sparse-checkout", "set", "--no-cone", *sparse_patterns(args.feature), cwd=worktree)
    git("checkout", branch, cwd=worktree)
    (worktree / "research" / "logs").mkdir(parents=True, exist_ok=True)
    if not args.no_sync:
        subprocess.run(["uv", "sync", "--frozen", "-q"], cwd=worktree, check=True)

    run_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "name": name,
        "feature": args.feature,
        "mode": args.mode,
        "rep": args.rep,
        "base_commit": base,
        "branch": branch,
        "worktree": worktree.name,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "claude_code_version": claude_version(),
        "config_hashes": config_hashes(base),
    }
    (run_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    print(f"worktree: {worktree}")
    print(f"branch:   {branch} (from {base[:8]})")
    print(f"record:   {run_dir / 'run.json'}")
    print("next:")
    print(f"  1. open Claude Code in {worktree} and run: /run-feature {args.feature} {args.mode}")
    print(f"  2. uv run python research/tools/collect.py --worktree {worktree} --out {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
