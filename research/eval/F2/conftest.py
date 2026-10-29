# EVAL-CANARY-F2-13315d954563022c
"""Fixtures for the hidden F2 acceptance suite.

The suite talks to the app only through the fixed contract
(`create_app`, `Settings`) and the public HTTP interface. It does not import
anything from the F1 suite.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shortlink.config import Settings
from shortlink.main import create_app

BASE_URL = "http://testserver"

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}
HIDDEN_TEXT_TAGS = {"script", "style", "template"}


# --------------------------------------------------------------------------- HTML


class Node:
    """A minimal DOM node built from `html.parser` events."""

    def __init__(self, tag: str, attrs: dict[str, str | None], parent: Node | None):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[Node | str] = []

    def get(self, name: str) -> str | None:
        return self.attrs.get(name)

    def iter(self, tag: str | None = None) -> Iterator[Node]:
        """Yield descendant elements (not self), optionally filtered by tag."""
        for child in self.children:
            if isinstance(child, Node):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.iter(tag)

    def ancestors(self) -> Iterator[Node]:
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def strings(self) -> Iterator[str]:
        """Yield text pieces that would be rendered (skips script/style)."""
        for child in self.children:
            if isinstance(child, str):
                yield child
            elif child.tag not in HIDDEN_TEXT_TAGS:
                yield from child.strings()

    def text(self) -> str:
        return "".join(self.strings())

    def raw_text(self) -> str:
        """All direct and nested character data, including script/style content."""
        parts = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.raw_text())
        return "".join(parts)

    def chunks(self) -> list[str]:
        """Non-empty, whitespace-collapsed text pieces."""
        result = []
        for piece in self.strings():
            collapsed = " ".join(piece.split())
            if collapsed:
                result.append(collapsed)
        return result


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _parse_html(source: str) -> Node:
    builder = _TreeBuilder()
    builder.feed(source)
    builder.close()
    return builder.root


# ------------------------------------------------------------------------- SQLite


def _table_counts(db_path: str) -> dict[str, int]:
    """Row count of every table in the SQLite file, without assuming names."""
    if not Path(db_path).exists():
        return {}
    con = sqlite3.connect(db_path)
    try:
        names = [
            row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        ]
        counts = {}
        for name in names:
            quoted = '"' + name.replace('"', '""') + '"'
            counts[name] = con.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
        return counts
    finally:
        con.close()


# ----------------------------------------------------------------------- fixtures


@pytest.fixture
def db_path(tmp_path) -> str:
    """A fresh temporary SQLite path for each test."""
    return str(tmp_path / "eval_f2.db")


@pytest.fixture
def settings(db_path: str) -> Settings:
    return Settings(db_path=db_path, base_url=BASE_URL)


@pytest.fixture
def app_factory(db_path: str) -> Callable[..., FastAPI]:
    """Build a new app; defaults to this test's db_path and base_url.

    Each call creates an independent app on the same db_path, so calling it
    again simulates a restart (AC-20).
    """

    def build(path: str | None = None, base_url: str = BASE_URL) -> FastAPI:
        return create_app(Settings(db_path=path or db_path, base_url=base_url))

    return build


@pytest.fixture
def make_client(app_factory: Callable[..., FastAPI]) -> Iterator[Callable[..., TestClient]]:
    """Build a new app and an open TestClient (no redirect following).

    Every call builds a fresh app on the same db_path. Clients are closed at
    teardown.
    """
    with ExitStack() as stack:

        def build(path: str | None = None, base_url: str = BASE_URL) -> TestClient:
            app = app_factory(path, base_url)
            client = TestClient(app, follow_redirects=False)
            return stack.enter_context(client)

        yield build


@pytest.fixture
def client(make_client: Callable[..., TestClient]) -> TestClient:
    return make_client()


@pytest.fixture
def table_counts(db_path: str) -> Callable[[], dict[str, int]]:
    """Return a function that snapshots row counts of every table at db_path."""
    return lambda: _table_counts(db_path)


@pytest.fixture
def parse_html() -> Callable[[str], Node]:
    """Return a function that parses HTML into a minimal tree."""
    return _parse_html
