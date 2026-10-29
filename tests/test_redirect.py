"""GET /{code} (AC-10, 11, 12, 14) and the Location header encoding (D-4)."""

from __future__ import annotations

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from shortlink.main import create_app


def create(client, url: str) -> str:
    response = client.post("/links", json={"url": url})
    assert response.status_code == 201
    return response.json()["code"]


def test_existing_code_redirects_with_302_and_location(client):
    """AC-10"""
    url = "https://example.com/path?q=1"
    code = create(client, url)

    response = client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == url


def test_unknown_code_returns_404(client):
    """AC-11"""
    response = client.get("/zzzzzzz", follow_redirects=False)

    assert response.status_code == 404


def test_same_url_twice_gives_different_codes_that_both_redirect(client):
    """AC-12"""
    url = "https://example.com/same"
    first = create(client, url)
    second = create(client, url)

    assert first != second
    for code in (first, second):
        response = client.get(f"/{code}", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == url


def test_redirect_survives_creating_the_app_again_with_the_same_db(settings, client):
    """AC-14"""
    url = "https://example.com/persisted?x=1"
    code = create(client, url)

    new_app = create_app(settings)
    with TestClient(new_app) as new_client:
        response = new_client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/path?q=1",
        "http://example.com",
        "HTTPS://Example.com/Mixed/Case?Key=Value",
        "https://example.com/a%20b/%EA%B2%BD?x=%7e",
        'https://example.com/a<b>c?q="x"&r=1#frag',
        "https://example.com/a|b{c}d^e`f\\g",
    ],
)
def test_ascii_location_is_the_stored_url_character_for_character(client, url):
    """D-4: ASCII URL은 Location이 원문과 글자 그대로 같다."""
    code = create(client, url)

    response = client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/경로",
        "https://example.com/path?q=한글&r=1",
        "https://example.com/日本語#섹션",
    ],
)
def test_non_ascii_url_redirects_with_percent_encoded_location(client, url):
    """D-4: 한글 경로 URL도 500이 아니라 302, Location은 UTF-8 퍼센트 인코딩 값."""
    code = create(client, url)

    response = client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 302
    expected = quote(url, safe="".join(chr(c) for c in range(0x21, 0x7F)))
    assert response.headers["location"] == expected
    assert response.headers["location"].isascii()


def test_korean_path_location_value(client):
    """D-4: 구체적인 값 확인."""
    code = create(client, "https://example.com/경로")

    response = client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/%EA%B2%BD%EB%A1%9C"


def test_redirect_response_has_nosniff_header(client):
    """D-10"""
    code = create(client, "https://example.com/path")

    response = client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["x-content-type-options"] == "nosniff"
