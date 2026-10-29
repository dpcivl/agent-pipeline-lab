"""LinkRepository: storage round trip, code collision retry, timestamp format."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from shortlink.db import init_schema
from shortlink.repository import Link, LinkRepository, format_timestamp


@pytest.fixture
def db_path(settings) -> str:
    init_schema(settings.db_path)
    return settings.db_path


def fixed_codes(*codes: str):
    """Code factory that returns `codes` in order and records how often it was called."""
    remaining = list(codes)
    calls: list[str] = []

    def factory() -> str:
        code = remaining.pop(0)
        calls.append(code)
        return code

    factory.calls = calls  # type: ignore[attr-defined]
    return factory


def test_create_then_get_returns_the_stored_link(db_path):
    repository = LinkRepository(db_path)
    before = datetime.now(UTC).replace(microsecond=0)

    link = repository.create("https://example.com/Path?Q=1")
    found = repository.get(link.code)

    assert isinstance(link, Link)
    assert found == link
    assert found.url == "https://example.com/Path?Q=1"
    assert len(link.code) == 7 and link.code.isalnum()
    assert link.created_at.tzinfo is not None
    assert link.created_at.utcoffset() == timedelta(0)
    assert before <= link.created_at <= datetime.now(UTC)


def test_get_unknown_code_returns_none(db_path):
    assert LinkRepository(db_path).get("zzzzzzz") is None


def test_same_url_twice_makes_two_rows_with_different_codes(db_path):
    repository = LinkRepository(db_path)

    first = repository.create("https://example.com/same")
    second = repository.create("https://example.com/same")

    assert first.code != second.code
    assert repository.get(first.code).url == repository.get(second.code).url


def test_links_survive_a_new_repository_on_the_same_file(db_path):
    link = LinkRepository(db_path).create("https://example.com/persist")

    assert LinkRepository(db_path).get(link.code) == link


def test_collision_is_retried_with_a_new_code(db_path):
    repository = LinkRepository(
        db_path, code_factory=fixed_codes("AAAAAAA", "AAAAAAA", "AAAAAAA", "BBBBBBB")
    )

    first = repository.create("https://example.com/first")
    second = repository.create("https://example.com/second")

    assert first.code == "AAAAAAA"
    assert second.code == "BBBBBBB"
    assert repository.get("AAAAAAA").url == "https://example.com/first"
    assert repository.get("BBBBBBB").url == "https://example.com/second"


def test_persistent_collision_raises_runtime_error_and_keeps_existing_row(db_path):
    first_factory = fixed_codes("AAAAAAA")
    LinkRepository(db_path, code_factory=first_factory).create("https://example.com/first")

    def always_collides() -> str:
        calls.append(1)
        return "AAAAAAA"

    calls: list[int] = []
    repository = LinkRepository(db_path, code_factory=always_collides)

    with pytest.raises(RuntimeError):
        repository.create("https://example.com/second")

    assert len(calls) == LinkRepository.MAX_ATTEMPTS
    assert repository.get("AAAAAAA").url == "https://example.com/first"


def test_collision_resolved_on_the_last_attempt_still_succeeds(db_path):
    max_attempts = LinkRepository.MAX_ATTEMPTS
    LinkRepository(db_path, code_factory=fixed_codes("AAAAAAA")).create("https://example.com/a")
    colliding = ["AAAAAAA"] * (max_attempts - 1)
    repository = LinkRepository(db_path, code_factory=fixed_codes(*colliding, "CCCCCCC"))

    link = repository.create("https://example.com/b")

    assert link.code == "CCCCCCC"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime(2026, 10, 29, 1, 23, 45, tzinfo=UTC), "2026-10-29T01:23:45Z"),
        (datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC), "2026-01-02T03:04:05Z"),
    ],
)
def test_format_timestamp_is_utc_iso8601_with_z(value, expected):
    """D-8"""
    assert format_timestamp(value) == expected
