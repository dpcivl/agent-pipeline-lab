# EVAL-CANARY-F1-f9f5210e4f17e5fd
"""Hidden acceptance tests for F1 JSON API (AC-1 to AC-15)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

BASE_URL = "http://testserver"
CODE_RE = re.compile(r"^[A-Za-z0-9]{7}$")
# UTC ISO 8601: date, "T", time, optional fraction, and a UTC designator.
CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")

PREFIX = "https://example.com/"


def url_of_length(length: int) -> str:
    return PREFIX + "a" * (length - len(PREFIX))


def create(client: TestClient, url: str) -> dict:
    response = client.post("/links", json={"url": url})
    assert response.status_code == 201, response.text
    return response.json()


def different_code(code: str) -> str:
    """A 7-char code that differs from `code` in its last character."""
    return code[:-1] + ("a" if code[-1] != "a" else "b")


# Valid URLs that must come back character-for-character (no normalization).
VERBATIM_URLS = [
    "https://example.com/path?q=1",
    "https://example.com",
    "https://example.com/path/",
    "https://Example.COM/Path/To?Q=A&b=%2F#Frag",
    "http://example.com:8080/a/../b",
    "https://example.com/?q=hello%20world&x=",
]

INVALID_PAYLOADS = [
    pytest.param({}, id="missing"),
    pytest.param({"url": 123}, id="number"),
    pytest.param({"url": ""}, id="empty"),
    pytest.param({"url": "ftp://example.com"}, id="ftp"),
    pytest.param({"url": "javascript:alert(1)"}, id="javascript"),
    pytest.param({"url": "https://"}, id="no-host"),
    pytest.param({"url": url_of_length(2049)}, id="too-long"),
]


# ---------------------------------------------------------------- AC-1


def test_hidden_ac01_create_returns_201_with_fields(client):
    response = client.post("/links", json={"url": "https://example.com/path?q=1"})
    assert response.status_code == 201
    body = response.json()
    for field in ("code", "short_url", "url", "created_at"):
        assert field in body, field


# ---------------------------------------------------------------- AC-2


def test_hidden_ac02_code_is_seven_alphanumerics(client):
    for _ in range(20):
        code = create(client, "https://example.com/path?q=1")["code"]
        assert isinstance(code, str)
        assert CODE_RE.fullmatch(code), code


def test_hidden_ac02_short_url_is_base_url_slash_code(client):
    body = create(client, "https://example.com/path?q=1")
    assert body["short_url"] == f"{BASE_URL}/{body['code']}"


def test_hidden_ac02_short_url_follows_configured_base_url(make_client):
    other = make_client(base_url="https://sho.rt/")
    body = create(other, "https://example.com/path?q=1")
    assert body["short_url"] == f"https://sho.rt/{body['code']}"


# ---------------------------------------------------------------- AC-3


@pytest.mark.parametrize("url", VERBATIM_URLS)
def test_hidden_ac03_url_returned_verbatim(client, url):
    assert create(client, url)["url"] == url


# ---------------------------------------------------------------- AC-4


def test_hidden_ac04_http_url_is_accepted(client):
    body = create(client, "http://example.com/plain")
    assert body["url"] == "http://example.com/plain"


# ---------------------------------------------------------------- AC-5


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "javascript:alert(1)",
        "data:text/html,hi",
        "mailto:a@example.com",
        "file:///etc/passwd",
        "example.com/path",
    ],
)
def test_hidden_ac05_rejects_non_http_scheme(client, url):
    assert client.post("/links", json={"url": url}).status_code == 422


def test_hidden_ac05_rejects_javascript_scheme(client):
    assert client.post("/links", json={"url": "javascript:alert(1)"}).status_code == 422


# ---------------------------------------------------------------- AC-6


def test_hidden_ac06_rejects_missing_url_field(client):
    assert client.post("/links", json={}).status_code == 422


@pytest.mark.parametrize(
    "value",
    [123, 1.5, None, True, ["https://example.com"], {"href": "https://example.com"}],
    ids=["int", "float", "null", "bool", "list", "object"],
)
def test_hidden_ac06_rejects_non_string_url(client, value):
    assert client.post("/links", json={"url": value}).status_code == 422


def test_hidden_ac06_rejects_empty_string(client):
    assert client.post("/links", json={"url": ""}).status_code == 422


# ---------------------------------------------------------------- AC-7


@pytest.mark.parametrize("url", ["https://", "http://", "https:///path"])
def test_hidden_ac07_rejects_url_without_host(client, url):
    assert client.post("/links", json={"url": url}).status_code == 422


# ---------------------------------------------------------------- AC-8


def test_hidden_ac08_accepts_2048_chars(client):
    url = url_of_length(2048)
    assert len(url) == 2048
    body = create(client, url)
    assert body["url"] == url
    redirect = client.get(f"/{body['code']}")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == url


def test_hidden_ac08_rejects_2049_chars(client):
    url = url_of_length(2049)
    assert len(url) == 2049
    assert client.post("/links", json={"url": url}).status_code == 422


def test_hidden_ac08_rejects_much_longer_url(client):
    assert client.post("/links", json={"url": url_of_length(5000)}).status_code == 422


# ---------------------------------------------------------------- AC-9


def test_hidden_ac09_storage_is_observable_precondition(client, table_counts):
    """Sanity check: a valid creation adds rows, so the AC-9 checks are meaningful."""
    before = sum(table_counts().values())
    create(client, "https://example.com/stored")
    assert sum(table_counts().values()) > before


@pytest.mark.parametrize("payload", INVALID_PAYLOADS)
def test_hidden_ac09_rejected_request_stores_nothing(client, table_counts, payload):
    create(client, "https://example.com/existing")
    before = table_counts()
    response = client.post("/links", json=payload)
    assert response.status_code == 422
    assert table_counts() == before


def test_hidden_ac09_rejected_requests_leave_db_unchanged_from_empty(client, table_counts):
    before = table_counts()
    for param in INVALID_PAYLOADS:
        assert client.post("/links", json=param.values[0]).status_code == 422
    assert table_counts() == before
    url = "https://example.com/after-rejections"
    body = create(client, url)
    assert client.get(f"/{body['code']}").headers["location"] == url


# ---------------------------------------------------------------- AC-10


@pytest.mark.parametrize("url", VERBATIM_URLS)
def test_hidden_ac10_redirects_with_302_to_original(client, url):
    code = create(client, url)["code"]
    response = client.get(f"/{code}")
    assert response.status_code == 302
    assert response.headers["location"] == url


def test_hidden_ac10_redirects_http_url(client):
    code = create(client, "http://example.com/plain")["code"]
    response = client.get(f"/{code}")
    assert response.status_code == 302
    assert response.headers["location"] == "http://example.com/plain"


# ---------------------------------------------------------------- AC-11


@pytest.mark.parametrize("code", ["Zz9Zz9Z", "abc", "abcdefghij"])
def test_hidden_ac11_unknown_code_returns_404(client, code):
    assert client.get(f"/{code}").status_code == 404


def test_hidden_ac11_unknown_code_404_when_other_codes_exist(client):
    code = create(client, "https://example.com/one")["code"]
    assert client.get(f"/{different_code(code)}").status_code == 404


# ---------------------------------------------------------------- AC-12


def test_hidden_ac12_same_url_twice_gives_different_codes(client):
    url = "https://example.com/dup"
    first = create(client, url)
    second = create(client, url)
    assert first["code"] != second["code"]
    for body in (first, second):
        response = client.get(f"/{body['code']}")
        assert response.status_code == 302
        assert response.headers["location"] == url


# ---------------------------------------------------------------- AC-13


def test_hidden_ac13_hundred_codes_are_unique(client):
    codes = [create(client, "https://example.com/many")["code"] for _ in range(100)]
    assert all(CODE_RE.fullmatch(code) for code in codes)
    assert len(set(codes)) == 100


# ---------------------------------------------------------------- AC-14


def test_hidden_ac14_redirect_survives_new_app_on_same_db(app_factory):
    url = "https://example.com/persist?x=1"
    with TestClient(app_factory(), follow_redirects=False) as first:
        code = create(first, url)["code"]
    with TestClient(app_factory(), follow_redirects=False) as second:
        response = second.get(f"/{code}")
        assert response.status_code == 302
        assert response.headers["location"] == url


def test_hidden_ac14_new_app_still_returns_404_for_unknown(app_factory):
    with TestClient(app_factory(), follow_redirects=False) as first:
        code = create(first, "https://example.com/persist")["code"]
    with TestClient(app_factory(), follow_redirects=False) as second:
        assert second.get(f"/{different_code(code)}").status_code == 404


# ---------------------------------------------------------------- AC-15


def test_hidden_ac15_created_at_is_utc_iso8601_and_recent(client):
    started = datetime.now(UTC)
    body = create(client, "https://example.com/time")
    finished = datetime.now(UTC)

    created_at = body["created_at"]
    assert isinstance(created_at, str)
    assert CREATED_AT_RE.fullmatch(created_at), created_at

    parsed = datetime.fromisoformat(created_at)
    assert parsed.utcoffset() == timedelta(0)
    assert started - timedelta(minutes=1) <= parsed <= finished + timedelta(minutes=1)
