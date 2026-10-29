"""POST /links (AC-1 ~ AC-9, AC-13, AC-15)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import pytest

from shortlink.validation import (
    MSG_EMPTY,
    MSG_INVALID_ENCODING,
    MSG_NO_HOST,
    MSG_SCHEME,
    MSG_TOO_LONG,
)

CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{7}$")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def url_of_length(length: int) -> str:
    prefix = "https://example.com/"
    return prefix + "a" * (length - len(prefix))


def test_create_returns_201_and_four_fields(client):
    """AC-1"""
    response = client.post("/links", json={"url": "https://example.com/path?q=1"})

    assert response.status_code == 201
    assert set(response.json()) == {"code", "short_url", "url", "created_at"}


def test_code_is_seven_alphanumeric_chars_and_short_url_uses_base_url(client, settings):
    """AC-2"""
    body = client.post("/links", json={"url": "https://example.com/path?q=1"}).json()

    assert CODE_PATTERN.fullmatch(body["code"])
    assert body["short_url"] == settings.base_url + "/" + body["code"]


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/path?q=1",
        "https://Example.COM/CamelCase/Path?Key=Value&other=A%20B",
        "https://example.com/a%2Fb%7e?x=%E2%9C%93#Fragment",
        "HTTPS://example.com/upper-scheme",
        "https://example.com/경로?q=한글",
        'https://example.com/<b>"quote"</b>',
    ],
)
def test_response_url_is_exactly_the_request_url(client, url):
    """AC-3"""
    response = client.post("/links", json={"url": url})

    assert response.status_code == 201
    assert response.json()["url"] == url


def test_http_url_is_accepted(client):
    """AC-4"""
    response = client.post("/links", json={"url": "http://example.com"})

    assert response.status_code == 201
    assert response.json()["url"] == "http://example.com"


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "javascript:alert(1)",
        "data:text/html,hi",
        "mailto:a@example.com",
    ],
)
def test_non_http_scheme_is_rejected(client, url):
    """AC-5"""
    response = client.post("/links", json={"url": url})

    assert response.status_code == 422
    assert response.json() == {"detail": MSG_SCHEME}


@pytest.mark.parametrize(
    ("payload", "detail"),
    [
        ({}, None),
        ({"other": "https://example.com"}, None),
        ({"url": 123}, None),
        ({"url": None}, None),
        ({"url": ["https://example.com"]}, None),
        ({"url": True}, None),
        ({"url": ""}, MSG_EMPTY),
    ],
    ids=["missing", "wrong-field", "number", "null", "list", "bool", "empty"],
)
def test_missing_non_string_or_empty_url_is_rejected(client, payload, detail):
    """AC-6"""
    response = client.post("/links", json=payload)

    assert response.status_code == 422
    if detail is not None:
        assert response.json() == {"detail": detail}


@pytest.mark.parametrize(
    "content",
    ["not json", '["https://example.com"]', '"https://example.com"', "null"],
    ids=["malformed", "array", "string", "null"],
)
def test_malformed_or_non_object_body_is_rejected(client, count_links, content):
    """AC-6 (계획 3.3: JSON 형식 오류, 본문이 객체가 아님)"""
    response = client.post("/links", content=content, headers={"Content-Type": "application/json"})

    assert response.status_code == 422
    assert count_links() == 0


def test_url_without_host_is_rejected(client):
    """AC-7"""
    response = client.post("/links", json={"url": "https://"})

    assert response.status_code == 422
    assert response.json() == {"detail": MSG_NO_HOST}


def test_url_of_2048_chars_is_created(client):
    """AC-8 (경계값 통과)"""
    url = url_of_length(2048)
    assert len(url) == 2048

    response = client.post("/links", json={"url": url})

    assert response.status_code == 201
    assert response.json()["url"] == url


def test_url_of_2049_chars_is_rejected(client):
    """AC-8 (경계값 초과)"""
    url = url_of_length(2049)
    assert len(url) == 2049

    response = client.post("/links", json={"url": url})

    assert response.status_code == 422
    assert response.json() == {"detail": MSG_TOO_LONG}


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/ with-space",
        " https://example.com",
        "https://example.com\n",
        "https://example.com/\r\nX-Injected: 1",
    ],
    ids=["inner-space", "leading-space", "trailing-newline", "crlf"],
)
def test_whitespace_or_control_chars_are_rejected(client, count_links, url):
    """D-2: 공백과 제어 문자가 든 URL은 정규화 없이 422로 거절한다."""
    response = client.post("/links", json={"url": url})

    assert response.status_code == 422
    assert count_links() == 0


def test_uppercase_scheme_is_accepted_and_kept(client):
    """D-1: 스킴은 대소문자를 구분하지 않고, 저장은 원문 그대로."""
    response = client.post("/links", json={"url": "HTTPS://example.com/X"})

    assert response.status_code == 201
    assert response.json()["url"] == "HTTPS://example.com/X"


@pytest.mark.parametrize(
    "payload",
    [
        {"url": "ftp://example.com"},
        {"url": "javascript:alert(1)"},
        {"url": "data:text/html,hi"},
        {"url": "mailto:a@example.com"},
        {"url": "https://"},
        {"url": ""},
        {"url": 123},
        {},
        {"url": "https://example.com/" + "a" * 2100},
    ],
    ids=[
        "ftp",
        "javascript",
        "data",
        "mailto",
        "no-host",
        "empty",
        "number",
        "missing",
        "too-long",
    ],
)
def test_rejected_requests_store_nothing(client, count_links, payload):
    """AC-9"""
    assert count_links() == 0

    response = client.post("/links", json=payload)

    assert response.status_code == 422
    assert count_links() == 0


def test_accepted_request_is_stored(client, count_links):
    """AC-9 대조군: 거절과 달리 성공한 요청은 한 행을 저장한다."""
    client.post("/links", json={"url": "https://example.com"})

    assert count_links() == 1


def test_100_consecutive_creations_give_distinct_codes(client):
    """AC-13"""
    codes = [
        client.post("/links", json={"url": "https://example.com"}).json()["code"]
        for _ in range(100)
    ]

    assert len(codes) == 100
    assert len(set(codes)) == 100


def test_created_at_is_utc_iso8601_within_a_minute_of_request(client):
    """AC-15"""
    before = datetime.now(UTC)
    response = client.post("/links", json={"url": "https://example.com"})
    after = datetime.now(UTC)

    created_at = response.json()["created_at"]
    assert TIMESTAMP_PATTERN.fullmatch(created_at)

    parsed = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    assert abs(parsed - before) < timedelta(minutes=1)
    assert abs(parsed - after) < timedelta(minutes=1)
    # 초 단위 절사를 감안해 1초 여유를 둔다.
    assert before - timedelta(seconds=1) <= parsed <= after + timedelta(seconds=1)


@pytest.mark.parametrize(
    "escape",
    [r"\ud800", r"\udc80", r"\udbff\u0041"],
    ids=["high", "low", "bad-pair"],
)
def test_unpaired_surrogate_in_json_is_rejected_with_422(client, count_links, escape):
    """D-9: JSON의 짝 없는 서로게이트 이스케이프는 500이 아니라 422로 거절한다."""
    response = client.post(
        "/links",
        content='{"url": "https://e.com/' + escape + '"}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": MSG_INVALID_ENCODING}
    assert count_links() == 0


def test_valid_surrogate_pair_in_json_is_accepted(client):
    """D-9 대조군: 짝이 맞는 이스케이프(U+1F600)는 정상 문자다."""
    response = client.post(
        "/links",
        content=r'{"url": "https://e.com/\ud83d\ude00"}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 201
    assert response.json()["url"] == "https://e.com/\U0001f600"


def test_json_response_has_nosniff_header(client):
    """D-10"""
    created = client.post("/links", json={"url": "https://example.com"})
    rejected = client.post("/links", json={"url": "ftp://example.com"})

    assert created.status_code == 201
    assert created.headers["x-content-type-options"] == "nosniff"
    assert rejected.status_code == 422
    assert rejected.headers["x-content-type-options"] == "nosniff"
