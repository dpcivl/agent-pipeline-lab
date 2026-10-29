"""Check every file git would publish for personal data before committing.

Scans tracked and staged text files (what a push would publish) with the same
rules as sanitize.find_leaks. Exits 1 and lists the files if anything is found,
so it can gate a commit:

  uv run python research/tools/check_public.py && git commit ...
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sanitize import find_leaks

REPO = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {".md", ".py", ".json", ".jsonl", ".csv", ".html", ".css", ".js", ".toml", ".txt"}


def published_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    return [REPO / line for line in out.splitlines() if Path(line).suffix in TEXT_SUFFIXES]


def main() -> int:
    found = []
    for path in published_files():
        if not path.exists():
            continue
        leaks = find_leaks(path.read_text(encoding="utf-8", errors="replace"))
        if leaks:
            found.append((path.relative_to(REPO).as_posix(), leaks))
    for rel, leaks in found:
        print(f"{rel}: {', '.join(sorted(set(leaks)))}")
    print(f"checked {len(published_files())} files, {len(found)} with personal data")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
