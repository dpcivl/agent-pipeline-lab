"""Score the result of one run.

Runs the hidden evaluation tests (kept outside the repository) against a run's
worktree, then collects static metrics from the same worktree:

  eval      hidden acceptance tests: passed / failed / errors, failed test ids
  own_tests the run's own tests: counts and line coverage of src/shortlink
  ruff      lint findings by rule
  radon     cyclomatic complexity (average, max)
  bandit    security findings by severity
  size      lines of code in src/ and tests/

Usage:
  uv run python research/tools/score.py --worktree <path> --eval-dir <path> --out <score.json>

The evaluation tests import only shortlink.main.create_app and shortlink.config.Settings
and talk to the app over HTTP, so they work with any internal structure.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, check=False, cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )


def junit_counts(path: Path) -> dict:
    if not path.exists():
        return {"error": "no junit report"}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = {
        k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")
    }
    total["passed"] = total["tests"] - total["failures"] - total["errors"] - total["skipped"]
    failed = []
    for case in root.iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(f"{case.get('classname')}::{case.get('name')}")
    total["failed_ids"] = failed
    total["pass_rate"] = round(total["passed"] / total["tests"], 4) if total["tests"] else None
    return total


def eval_tests(worktree: Path, eval_dir: Path, tmp: Path) -> dict:
    target = tmp / "eval_tests"
    shutil.copytree(eval_dir, target)
    junit = tmp / "eval-junit.xml"
    proc = run(
        [
            "uv",
            "run",
            "--frozen",
            "pytest",
            str(target),
            "-q",
            "-p",
            "no:cacheprovider",
            "--rootdir",
            str(target),
            f"--junitxml={junit}",
        ],
        worktree,
    )
    result = junit_counts(junit)
    result["exit_code"] = proc.returncode
    return result


def own_tests(worktree: Path, tmp: Path) -> dict:
    junit = tmp / "own-junit.xml"
    cov = tmp / "coverage.json"
    proc = run(
        [
            "uv",
            "run",
            "--frozen",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--cov=shortlink",
            f"--cov-report=json:{cov}",
            f"--junitxml={junit}",
        ],
        worktree,
    )
    result = junit_counts(junit)
    result["exit_code"] = proc.returncode
    if cov.exists():
        data = json.loads(cov.read_text(encoding="utf-8"))
        result["coverage_percent"] = round(data["totals"]["percent_covered"], 2)
    return result


def ruff(worktree: Path) -> dict:
    proc = run(
        ["uv", "run", "--frozen", "ruff", "check", "src", "tests", "--output-format", "json"],
        worktree,
    )
    try:
        items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return {"error": proc.stderr.strip()[:500]}
    return {"count": len(items), "by_rule": dict(Counter(i["code"] for i in items).most_common())}


def radon(worktree: Path) -> dict:
    proc = run(["uv", "run", "--frozen", "radon", "cc", "src", "-j"], worktree)
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"error": proc.stderr.strip()[:500]}
    scores = [
        b["complexity"] for blocks in data.values() if isinstance(blocks, list) for b in blocks
    ]
    if not scores:
        return {"blocks": 0}
    return {
        "blocks": len(scores),
        "average": round(sum(scores) / len(scores), 2),
        "max": max(scores),
    }


def bandit(worktree: Path) -> dict:
    proc = run(["uv", "run", "--frozen", "bandit", "-r", "src", "-f", "json", "-q"], worktree)
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"error": proc.stderr.strip()[:500]}
    results = data.get("results", [])
    return {
        "count": len(results),
        "by_severity": dict(Counter(r["issue_severity"] for r in results)),
        "tests": sorted({r["test_id"] for r in results}),
    }


def size(worktree: Path) -> dict:
    def lines(folder: str) -> int:
        return sum(
            len(p.read_text(encoding="utf-8").splitlines())
            for p in (worktree / folder).rglob("*.py")
        )

    return {"src_lines": lines("src"), "test_lines": lines("tests")}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--eval-dir", help="hidden evaluation tests for this feature")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    worktree = Path(args.worktree).resolve()
    with tempfile.TemporaryDirectory(prefix="score-") as tmp_name:
        tmp = Path(tmp_name)
        result = {
            "eval": eval_tests(worktree, Path(args.eval_dir).resolve(), tmp)
            if args.eval_dir
            else None,
            "own_tests": own_tests(worktree, tmp),
            "ruff": ruff(worktree),
            "radon": radon(worktree),
            "bandit": bandit(worktree),
            "size": size(worktree),
        }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ev = result["eval"]
    print(f"eval: {ev['passed']}/{ev['tests']} passed" if ev and "tests" in ev else "eval: skipped")
    print(
        f"own tests: {result['own_tests'].get('passed')}/{result['own_tests'].get('tests')}, "
        f"coverage {result['own_tests'].get('coverage_percent')}%"
    )
    print(
        f"ruff {result['ruff'].get('count')}, bandit {result['bandit'].get('count')}, "
        f"radon avg {result['radon'].get('average')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
