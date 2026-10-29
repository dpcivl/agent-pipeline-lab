"""Remove personal and environment details from text before it is published.

Replaces home-directory paths, the OS user name, e-mail addresses, and
token-like secrets with placeholders. Used by collect.py on every message
written to the public part of a run folder.
"""

from __future__ import annotations

import getpass
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_RE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-ant-[A-Za-z0-9_-]{10,}"
    r"|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b"
)
# Placeholder e-mail addresses that are safe to keep.
SAFE_EMAILS = {"noreply@anthropic.com"}


@lru_cache(maxsize=1)
def _user_names() -> tuple[str, ...]:
    names = {Path.home().name}
    for getter in (getpass.getuser, lambda: os.environ.get("USERNAME", "")):
        try:
            name = getter()
        except (OSError, KeyError, ImportError):
            name = ""
        if name:
            names.add(name)
    return tuple(sorted((n for n in names if len(n) >= 3), key=len, reverse=True))


@lru_cache(maxsize=1)
def _git_emails() -> tuple[str, ...]:
    try:
        out = subprocess.run(
            ["git", "config", "--get-all", "user.email"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
    except OSError:
        return ()
    return tuple(e.strip() for e in out.splitlines() if e.strip())


def _home_patterns() -> list[re.Pattern[str]]:
    patterns = []
    for name in _user_names():
        n = re.escape(name)
        # C:\Users\name, C:\Users\name (JSON-escaped), C:/Users/name, /c/Users/name, /home/name
        patterns.append(re.compile(rf"[A-Za-z]:(?:\\|\|/)Users(?:\\|\|/){n}", re.IGNORECASE))
        patterns.append(re.compile(rf"/[a-z]/Users/{n}", re.IGNORECASE))
        patterns.append(re.compile(rf"/(?:home|Users)/{n}"))
    return patterns


def sanitize(text: str) -> str:
    if not text:
        return text
    for pattern in _home_patterns():
        text = pattern.sub("<HOME>", text)
    for email in _git_emails():
        text = text.replace(email, "<EMAIL>")
    text = EMAIL_RE.sub(lambda m: m.group(0) if m.group(0) in SAFE_EMAILS else "<EMAIL>", text)
    text = SECRET_RE.sub("<SECRET>", text)
    for name in _user_names():
        # Remaining standalone occurrences such as project slugs (C--Users-name-...).
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", "<USER>", text)
    return text


def find_leaks(text: str) -> list[str]:
    """Return personal values still present in text (used as a final check)."""
    leaks = []
    for name in _user_names():
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", text):
            leaks.append(f"user name: {name}")
    for email in EMAIL_RE.findall(text):
        if email not in SAFE_EMAILS:
            leaks.append(f"email: {email}")
    if SECRET_RE.search(text):
        leaks.append("secret-like token")
    return leaks


if __name__ == "__main__":
    import sys

    sys.stdout.write(sanitize(sys.stdin.read()))
