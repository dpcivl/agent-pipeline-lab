"""Promote one run's result to main as a single feature commit.

Squash-merges the run branch (run/<feature>-<mode>-r<rep>) into main, so main gets
exactly one commit per feature while the run branch keeps every checkpoint commit.
Then tags the new commit baseline-F<n+1>, the common starting point for the next
feature's runs. Run this in the research repository on a clean main branch.

Usage:
  uv run python research/tools/promote.py F1 auto 1 [--trailer "Co-Authored-By: ..."]

Nothing is pushed. Writes research/runs/<feature>/<mode>/r<rep>/promoted.json.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("feature", help="feature id, e.g. F1")
    ap.add_argument("mode", choices=("auto", "human", "default"))
    ap.add_argument("rep", type=int)
    ap.add_argument("--trailer", action="append", default=[], help="extra commit trailer line")
    ap.add_argument("--no-tag", action="store_true", help="do not tag the next baseline")
    ap.add_argument(
        "--allow-unfinished",
        action="store_true",
        help="promote a run whose last commit is not a feature commit",
    )
    args = ap.parse_args()

    match = re.fullmatch(r"F(\d+)", args.feature)
    if not match:
        sys.exit("feature must look like F1")
    branch = f"run/{args.feature}-{args.mode}-r{args.rep}"
    next_tag = f"baseline-F{int(match.group(1)) + 1}"

    if git("branch", "--show-current") != "main":
        sys.exit("switch to main first")
    if git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("main has uncommitted changes; commit or stash them first")
    if not git("rev-parse", "--verify", "--quiet", branch, check=False):
        sys.exit(f"branch not found: {branch}")
    if not args.no_tag and git("tag", "--list", next_tag):
        sys.exit(f"tag {next_tag} already exists")

    base = git("merge-base", "main", branch)
    subjects = git("log", "--format=%s", f"{base}..{branch}").splitlines()
    if not subjects:
        sys.exit(f"{branch} has no commits after {base[:8]}")
    final_subject = subjects[0]
    final_body = git("log", "-1", "--format=%b", branch)
    if not final_subject.startswith(f"{args.feature}:") and not args.allow_unfinished:
        sys.exit(f"last commit of {branch} is not a feature commit: {final_subject!r}")
    checkpoints = sum(1 for s in subjects if s.startswith("wip("))

    merge = subprocess.run(
        ["git", "merge", "--squash", branch], cwd=REPO, capture_output=True, text=True, check=False
    )
    if merge.returncode != 0:
        subprocess.run(["git", "reset", "--merge"], cwd=REPO, check=False)
        sys.exit(f"squash merge failed, main restored:\n{merge.stdout}{merge.stderr}")

    run_rel = f"research/runs/{args.feature}/{args.mode}/r{args.rep}"
    message = (
        "\n".join(
            [
                final_subject,
                "",
                f"Squash of {branch}: {len(subjects)} commits ({checkpoints} checkpoints).",
                f"Run record: {run_rel}/",
                "",
                final_body.strip(),
                "",
                *args.trailer,
            ]
        ).strip()
        + "\n"
    )
    commit = subprocess.run(
        ["git", "commit", "-q", "-F", "-"],
        cwd=REPO,
        input=message,
        text=True,
        capture_output=True,
        check=False,
    )
    if commit.returncode != 0:
        subprocess.run(["git", "reset", "--merge"], cwd=REPO, check=False)
        sys.exit(f"commit failed, main restored:\n{commit.stderr}")
    head = git("rev-parse", "HEAD")

    if not args.no_tag:
        git(
            "tag",
            "-a",
            next_tag,
            "-m",
            f"Starting point for {next_tag.removeprefix('baseline-')} runs ({args.feature} from {branch})",
        )

    run_dir = REPO / run_rel
    run_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "branch": branch,
        "base_commit": base,
        "main_commit": head,
        "commits_on_branch": len(subjects),
        "checkpoints": checkpoints,
        "tag": None if args.no_tag else next_tag,
        "promoted_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (run_dir / "promoted.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"main {head[:8]}: {final_subject}")
    print(f"squashed {len(subjects)} commits ({checkpoints} checkpoints) from {branch}")
    if not args.no_tag:
        print(f"tagged {next_tag}")
    print("not pushed; push main and tags when ready: git push && git push --tags")
    return 0


if __name__ == "__main__":
    sys.exit(main())
