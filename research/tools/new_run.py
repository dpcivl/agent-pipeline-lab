"""Create an isolated worktree for one pipeline run.

The run branch starts from a **parentless snapshot commit** that holds only what the
agents need: service code, tests, agent definitions, hooks, plans, and the specs of the
current and earlier features. Because the snapshot has no parent, `git log` inside the
run shows no research history (design docs, hidden evaluation tests, other runs).
Access to other refs and to the research repository is blocked separately by
research/hooks/guard_bash.py and guard_read.py.

Usage:
  uv run python research/tools/new_run.py F1 auto 1 [--base <commit-or-tag>]
  uv run python research/tools/new_run.py P2 auto 1   (measurement stage, no feature spec)

Modes: auto (no human), human (human at H1-H4), default (human approves the plan only).
Writes research/runs/<feature>/<mode>/r<rep>/run.json with the base and snapshot commits
and config hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_ROOT = REPO.parent / f"{REPO.name}-runs"
MODES = ("auto", "human", "default")
# Everything the agents may see. Research documents, tools, runs and hidden evaluation
# tests are deliberately absent.
AGENT_PATHS = (
    "CLAUDE.md",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    ".gitignore",
    "CHANGELOG.md",
    "src",
    "tests",
    ".claude",
    "research/hooks",
    "docs/plans",
    "docs/service.md",
    "docs/features/README.md",
)
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


def git(*args: str, cwd: Path = REPO, env: dict | None = None, stdin: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        cwd=cwd,
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def spec_paths(feature: str) -> list[str]:
    """Specs of this feature and all earlier ones (later features stay hidden)."""
    if not feature.startswith("F"):
        return []
    n = int(feature[1:])
    return [f"docs/features/F{k}.md" for k in range(1, n + 1)]


def snapshot_commit(base: str, paths: list[str], message: str) -> str:
    """A parentless commit whose tree holds only `paths` as they are at `base`."""
    entries = git("ls-tree", "-r", "--full-tree", base, "--", *paths)
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmp) / "index")}
        git("read-tree", "--empty", env=env)
        git("update-index", "--index-info", env=env, stdin=entries + "\n")
        tree = git("write-tree", env=env)
    return git("commit-tree", tree, "-m", message)


def config_hashes(commit: str) -> dict[str, str]:
    """sha256 of each tracked config file at the given commit."""
    listing = git("ls-tree", "-r", "--name-only", commit, "--", *CONFIG_PATHS)
    hashes = {}
    for path in sorted(listing.splitlines()):
        blob = subprocess.run(
            ["git", "show", f"{commit}:{path}"], check=False, cwd=REPO, capture_output=True
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
    out = subprocess.run(
        [exe, "--version"], check=False, capture_output=True, text=True, encoding="utf-8"
    )
    return out.stdout.strip() or "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("feature", help="feature id (F1, F2, ...) or measurement stage (P2)")
    ap.add_argument("mode", choices=MODES)
    ap.add_argument("rep", type=int, help="repetition number, e.g. 1")
    ap.add_argument("--base", default="HEAD", help="commit or tag to take the files from")
    ap.add_argument("--runs-root", default=str(DEFAULT_RUNS_ROOT))
    ap.add_argument("--allow-missing-spec", action="store_true", help="for tooling tests only")
    ap.add_argument("--no-sync", action="store_true", help="skip uv sync in the worktree")
    args = ap.parse_args()

    if not re.fullmatch(r"[FP]\d+", args.feature):
        sys.exit("feature must look like F1 (feature) or P2 (measurement stage)")
    measurement = args.feature.startswith("P")
    name = f"{args.feature}-{args.mode}-r{args.rep}"
    branch = f"run/{name}"
    worktree = Path(args.runs_root) / name
    run_dir = REPO / "research" / "runs" / args.feature / args.mode / f"r{args.rep}"
    if worktree.exists() or (run_dir / "run.json").exists():
        sys.exit(f"run already exists: {worktree} or {run_dir / 'run.json'}")

    base = git("rev-parse", "--verify", f"{args.base}^{{commit}}")
    specs = spec_paths(args.feature)
    present = set(git("ls-tree", "-r", "--name-only", base, "--", *specs).splitlines())
    missing = [s for s in specs if s not in present]
    if missing and not (measurement or args.allow_missing_spec):
        sys.exit(f"missing in base commit {base[:8]}: {', '.join(missing)}")

    snapshot = snapshot_commit(base, [*AGENT_PATHS, *specs], f"Base snapshot for {name}")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git("worktree", "add", "-b", branch, str(worktree), snapshot)
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
        "snapshot_commit": snapshot,
        "branch": branch,
        "worktree": worktree.name,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "claude_code_version": claude_version(),
        "config_hashes": config_hashes(snapshot),
    }
    (run_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    print(f"worktree: {worktree}")
    print(f"branch:   {branch} (snapshot {snapshot[:8]} of {base[:8]}, no research history)")
    print(f"record:   {run_dir / 'run.json'}")
    print("next:")
    command = "/measure-baseline" if measurement else f"/run-feature {args.feature} {args.mode}"
    print(f"  1. open Claude Code in {worktree} (auto permission mode) and run: {command}")
    print(f"  2. uv run python research/tools/collect.py --worktree {worktree} --out {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
