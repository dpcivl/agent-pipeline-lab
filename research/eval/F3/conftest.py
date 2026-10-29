# EVAL-CANARY-F3-a35abd6a9f5f3b84
"""Fixtures for the hidden F3 acceptance suite.

The suite talks to the app only through the fixed contract
(`create_app`, `Settings`) and the public HTTP interface. Helpers live in
`f3_support.py`.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from f3_support import (
    BASE_URL,
    GENEROUS_RATE_LIMIT,
    KEY_A,
    REGISTERED_KEYS,
    RecordingTestClient,
    utc_z,
)
from fastapi import FastAPI

from shortlink.config import Settings
from shortlink.main import create_app

# ----------------------------------------------------------------------- fixtures


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "eval.db")


@pytest.fixture
def app_factory(db_path: str) -> Callable[..., FastAPI]:
    """Build an app on this test's db_path with two registered keys by default."""

    def build(
        api_keys: tuple[str, ...] = REGISTERED_KEYS,
        rate_limit_per_minute: int = GENEROUS_RATE_LIMIT,
        path: str | None = None,
    ) -> FastAPI:
        settings = Settings(
            db_path=path or db_path,
            base_url=BASE_URL,
            api_keys=api_keys,
            rate_limit_per_minute=rate_limit_per_minute,
        )
        return create_app(settings)

    return build


@pytest.fixture
def make_client(app_factory) -> Iterator[Callable[..., RecordingTestClient]]:
    """Build an open RecordingTestClient (no redirect following).

    Pass `app=` to share one app between clients, `client_host=` to choose the
    client IP; other keyword arguments go to `app_factory`.
    """
    with ExitStack() as stack:

        def build(app: FastAPI | None = None, client_host: str = "testclient", **kwargs):
            app = app or app_factory(**kwargs)
            client = RecordingTestClient(app, follow_redirects=False, client=(client_host, 50000))
            return stack.enter_context(client)

        yield build


@pytest.fixture
def client(make_client) -> RecordingTestClient:
    """Client on an app with KEY_A and KEY_B registered and a generous rate limit."""
    return make_client()


@pytest.fixture
def limited_app(app_factory) -> FastAPI:
    """App with KEY_A and KEY_B registered and rate_limit_per_minute=3."""
    return app_factory(rate_limit_per_minute=3)


# ------------------------------------------------------------- expiry (shared)


@pytest.fixture(scope="session")
def expiry_world(tmp_path_factory) -> Iterator[SimpleNamespace]:
    """One app with links that expire a few seconds after creation.

    Records the pre-expiry observations, then sleeps once until just past the
    expiry so every expiry test in the suite shares a single short wait.
    Links (all owned by KEY_A): `expiring` (expires in 2-3 s), `future`
    (expires 2099), `forever` (no expiry).
    """
    db = str(tmp_path_factory.mktemp("f3_expiry") / "eval.db")
    settings = Settings(
        db_path=db,
        base_url=BASE_URL,
        api_keys=REGISTERED_KEYS,
        rate_limit_per_minute=GENEROUS_RATE_LIMIT,
    )
    with RecordingTestClient(create_app(settings), follow_redirects=False) as client:
        headers = {"X-API-Key": KEY_A}
        future_at = "2099-12-31T00:00:00Z"
        forever = client.post(
            "/links",
            json={"url": "https://example.com/f3/forever", "alias": "f3-forever"},
            headers=headers,
        )
        future = client.post(
            "/links",
            json={
                "url": "https://example.com/f3/future",
                "alias": "f3-future",
                "expires_at": future_at,
            },
            headers=headers,
        )
        deadline = int(time.time()) + 3  # 2 to 3 seconds from now
        expires_at = utc_z(datetime.fromtimestamp(deadline, UTC))
        expiring = client.post(
            "/links",
            json={
                "url": "https://example.com/f3/expiring",
                "alias": "f3-expiring",
                "expires_at": expires_at,
            },
            headers=headers,
        )
        before_redirect = client.get("/f3-expiring")
        before_stats = client.get("/links/f3-expiring/stats")
        before_future_stats = client.get("/links/f3-future/stats")
        finished_before_deadline = time.time() < deadline

        time.sleep(max(0.0, deadline - time.time()) + 0.6)

        yield SimpleNamespace(
            client=client,
            expires_at=expires_at,
            future_at=future_at,
            forever=forever,
            future=future,
            expiring=expiring,
            before_redirect=before_redirect,
            before_stats=before_stats,
            before_future_stats=before_future_stats,
            finished_before_deadline=finished_before_deadline,
        )
