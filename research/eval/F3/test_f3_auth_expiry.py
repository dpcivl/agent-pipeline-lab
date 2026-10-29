# EVAL-CANARY-F3-a35abd6a9f5f3b84
"""Hidden acceptance tests for F3 API keys and expiry (AC-1 to AC-7)."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime

import pytest
from f3_support import (
    BASE_URL,
    KEY_A,
    KEY_B,
    KEY_UNKNOWN,
    assert_no_key_leak,
    is_html,
    parse_html,
    squash,
    utc_z,
)

# UTC ISO 8601: date, "T", time, optional fraction, and a UTC designator.
UTC_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")


def instant(value) -> datetime:
    """Parse a UTC ISO 8601 string from a response into an aware datetime."""
    assert isinstance(value, str), value
    assert UTC_ISO_RE.fullmatch(value), value
    return datetime.fromisoformat(value)


def create(client, body: dict, key: str | None = None):
    headers = {"X-API-Key": key} if key is not None else {}
    return client.post("/links", json=body, headers=headers)


def assert_not_stored(client, alias: str) -> None:
    assert client.get(f"/{alias}").status_code == 404
    assert client.get(f"/links/{alias}/stats").status_code == 404


UNREGISTERED_KEYS = [
    pytest.param(KEY_UNKNOWN, id="unknown"),
    pytest.param(KEY_A[:-1], id="prefix-of-registered"),
    pytest.param(KEY_A + "0", id="registered-plus-suffix"),
    pytest.param(KEY_A.upper(), id="registered-upper"),
    pytest.param(KEY_A.lower(), id="registered-lower"),
    pytest.param(f"{KEY_A},{KEY_B}", id="both-joined"),
]


# ---------------------------------------------------------------- AC-1


@pytest.mark.parametrize("key", [KEY_A, KEY_B], ids=["key-a", "key-b"])
def test_hidden_ac01_create_with_registered_key_returns_201(client, key):
    url = "https://example.com/f3/with-key"
    response = create(client, {"url": url}, key)
    assert response.status_code == 201
    body = response.json()
    assert body["url"] == url
    assert body["short_url"] == f"{BASE_URL}/{body['code']}"
    redirect = client.get(f"/{body['code']}")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == url


def test_hidden_ac01_create_with_registered_key_and_alias(client):
    response = create(client, {"url": "https://example.com/f3/alias", "alias": "f3-keyed"}, KEY_A)
    assert response.status_code == 201
    assert response.json()["code"] == "f3-keyed"
    assert client.get("/f3-keyed").status_code == 302


def test_hidden_ac01_create_without_key_still_returns_201(client):
    url = "https://example.com/f3/no-key"
    response = create(client, {"url": url})
    assert response.status_code == 201
    redirect = client.get(f"/{response.json()['code']}")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == url


def test_hidden_ac01_create_without_key_when_no_keys_registered(make_client):
    client = make_client(api_keys=())
    assert create(client, {"url": "https://example.com/f3/open"}).status_code == 201


# ---------------------------------------------------------------- AC-2


@pytest.mark.parametrize("key", UNREGISTERED_KEYS)
def test_hidden_ac02_unregistered_key_rejected_and_not_stored(client, key):
    alias = "f3-unregistered"
    response = create(client, {"url": "https://example.com/f3/x", "alias": alias}, key)
    assert response.status_code == 401
    assert_not_stored(client, alias)
    # The alias is still free, so nothing was reserved by the rejected request.
    assert (
        create(client, {"url": "https://example.com/f3/y", "alias": alias}, KEY_A).status_code
        == 201
    )


def test_hidden_ac02_any_key_rejected_when_no_keys_registered(make_client):
    client = make_client(api_keys=())
    alias = "f3-nokeys"
    response = create(client, {"url": "https://example.com/f3/x", "alias": alias}, KEY_A)
    assert response.status_code == 401
    assert_not_stored(client, alias)


def test_hidden_ac02_only_configured_keys_are_registered(make_client):
    client = make_client(api_keys=(KEY_B,))
    assert create(client, {"url": "https://example.com/f3/a"}, KEY_A).status_code == 401
    assert create(client, {"url": "https://example.com/f3/b"}, KEY_B).status_code == 201


# ---------------------------------------------------------------- AC-3


def test_hidden_ac03_api_and_screens_never_show_key(client):
    url = "https://example.com/f3/secret-check"
    keyed = {"X-API-Key": KEY_A}
    created = client.post("/links", json={"url": url, "alias": "f3-secret"}, headers=keyed)
    assert created.status_code == 201
    client.post(
        "/links",
        json={"url": "https://example.com/f3/expiring-later", "expires_at": "2099-01-01T00:00:00Z"},
        headers={"X-API-Key": KEY_B},
    )
    client.post("/links", json={"url": "ftp://bad"}, headers=keyed)  # 422 with a key
    client.post("/links", json={"url": url, "alias": "f3-secret"}, headers=keyed)  # 409
    assert client.get("/").status_code == 200
    assert client.post("/", data={"url": url}).status_code == 200
    assert client.get("/f3-secret").status_code == 302
    assert client.get("/links/f3-secret/stats").status_code == 200
    assert client.get("/stats/f3-secret").status_code == 200
    assert client.delete("/links/f3-secret", headers={"X-API-Key": KEY_B}).status_code == 403
    assert client.delete("/links/Zz9Zz9Z", headers=keyed).status_code == 404
    assert client.delete("/links/f3-secret", headers=keyed).status_code == 204
    assert client.get("/f3-secret").status_code == 404
    assert client.get("/stats/f3-secret").status_code == 404
    assert_no_key_leak(client)


def test_hidden_ac03_expired_page_and_stats_never_show_key(expiry_world):
    client = expiry_world.client
    assert client.get("/f3-expiring").status_code == 410
    assert client.get("/links/f3-expiring/stats").status_code == 200
    assert client.get("/stats/f3-expiring").status_code == 200
    assert_no_key_leak(client)


# ---------------------------------------------------------------- AC-4


def test_hidden_ac04_future_expiry_returns_201_with_same_instant(expiry_world):
    response = expiry_world.expiring
    assert response.status_code == 201, response.text
    assert instant(response.json()["expires_at"]) == instant(expiry_world.expires_at)


def test_hidden_ac04_far_future_expiry_returns_same_instant(expiry_world):
    response = expiry_world.future
    assert response.status_code == 201, response.text
    assert instant(response.json()["expires_at"]) == instant(expiry_world.future_at)
    redirect = expiry_world.client.get("/f3-future")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == "https://example.com/f3/future"


def test_hidden_ac04_redirects_before_expiry(expiry_world):
    assert expiry_world.finished_before_deadline, "setup was too slow to observe pre-expiry state"
    response = expiry_world.before_redirect
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/f3/expiring"


def test_hidden_ac04_expiry_without_api_key(client):
    at = "2099-06-30T12:34:56Z"
    response = create(client, {"url": "https://example.com/f3/anon-exp", "expires_at": at})
    assert response.status_code == 201
    assert instant(response.json()["expires_at"]) == instant(at)
    assert client.get(f"/{response.json()['code']}").status_code == 302


@pytest.mark.parametrize("key", [None, KEY_A], ids=["no-key", "key-a"])
def test_hidden_ac04_create_without_expiry_has_null_expires_at(client, key):
    response = create(client, {"url": "https://example.com/f3/no-expiry"}, key)
    assert response.status_code == 201
    body = response.json()
    assert "expires_at" in body
    assert body["expires_at"] is None


# ---------------------------------------------------------------- AC-5


@pytest.mark.parametrize(
    "offset",
    [
        pytest.param(-10 * 365 * 86400, id="years-ago"),
        pytest.param(-60, id="minute-ago"),
        pytest.param(0, id="now"),
    ],
)
def test_hidden_ac05_past_or_now_expiry_rejected(client, offset):
    at = utc_z(datetime.fromtimestamp(int(time.time()) + offset, UTC))
    response = create(client, {"url": "https://example.com/f3/past", "expires_at": at})
    assert response.status_code == 422


@pytest.mark.parametrize("key", [None, KEY_A], ids=["no-key", "key-a"])
def test_hidden_ac05_fixed_past_expiry_rejected(client, key):
    body = {"url": "https://example.com/f3/past", "expires_at": "2020-01-01T00:00:00Z"}
    assert create(client, body, key).status_code == 422


@pytest.mark.parametrize(
    "value",
    [
        "not-a-date",
        "tomorrow",
        "2099-13-01T00:00:00Z",
        "2099-02-30T00:00:00Z",
        "2099-12-31T25:00:00Z",
        "2099/12/31T00:00:00Z",
        "31/12/2099 00:00",
    ],
)
def test_hidden_ac05_malformed_expiry_rejected(client, value):
    response = create(client, {"url": "https://example.com/f3/bad", "expires_at": value})
    assert response.status_code == 422


# ---------------------------------------------------------------- AC-6


def test_hidden_ac06_expired_link_returns_410_page(expiry_world):
    response = expiry_world.client.get("/f3-expiring")
    assert response.status_code == 410
    assert is_html(response)
    assert "만료된 링크입니다" in squash(parse_html(response.text).text())


def test_hidden_ac06_expired_link_does_not_count_clicks(expiry_world):
    client = expiry_world.client
    # The only counted visit is the redirect made before expiry.
    expected = expiry_world.before_stats.json()["clicks"]
    assert client.get("/links/f3-expiring/stats").json()["clicks"] == expected
    for _ in range(3):
        assert client.get("/f3-expiring").status_code == 410
    assert client.get("/links/f3-expiring/stats").json()["clicks"] == expected


# ---------------------------------------------------------------- AC-7


def test_hidden_ac07_stats_not_expired_before_expiry(expiry_world):
    response = expiry_world.before_stats
    assert response.status_code == 200
    body = response.json()
    assert instant(body["expires_at"]) == instant(expiry_world.expires_at)
    assert body["expired"] is False


def test_hidden_ac07_stats_expired_after_expiry(expiry_world):
    response = expiry_world.client.get("/links/f3-expiring/stats")
    assert response.status_code == 200
    body = response.json()
    assert instant(body["expires_at"]) == instant(expiry_world.expires_at)
    assert body["expired"] is True
    assert body["url"] == "https://example.com/f3/expiring"


def test_hidden_ac07_future_expiry_stays_not_expired(expiry_world):
    for response in (
        expiry_world.before_future_stats,
        expiry_world.client.get("/links/f3-future/stats"),
    ):
        assert response.status_code == 200
        body = response.json()
        assert instant(body["expires_at"]) == instant(expiry_world.future_at)
        assert body["expired"] is False


@pytest.mark.parametrize("key", [None, KEY_A], ids=["no-key", "key-a"])
def test_hidden_ac07_no_expiry_stats_null_and_false(client, key):
    code = create(client, {"url": "https://example.com/f3/plain"}, key).json()["code"]
    body = client.get(f"/links/{code}/stats").json()
    assert "expires_at" in body
    assert body["expires_at"] is None
    assert body["expired"] is False


def test_hidden_ac07_stats_screen_still_visible_after_expiry(expiry_world):
    response = expiry_world.client.get("/stats/f3-expiring")
    assert response.status_code == 200
    assert is_html(response)
    assert "https://example.com/f3/expiring" in parse_html(response.text).text()
