# EVAL-CANARY-F2-13315d954563022c
"""Hidden acceptance tests for F2 click statistics (AC-12 to AC-22)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

BASE_URL = "http://testserver"
RANDOM_SHORT_URL_RE = re.compile(r"^http://testserver/([A-Za-z0-9]{7})$")
# UTC ISO 8601 (the F1 created_at format): optional fraction, Z or +00:00.
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")
HOME_HREFS = {"/", f"{BASE_URL}/", BASE_URL}
NOT_YET = "아직 없음"
XSS_MARKER = "__f2xss"
# A standalone integer: not part of a date/time ("2026-10-29", "13:05") or a longer number.
NUMBER_RE = re.compile(r"(?<![\d.:/-])\d+(?![\d.:/-])")
SLACK = timedelta(seconds=1)


def create(client, url, alias=None) -> dict:
    payload = {"url": url}
    if alias is not None:
        payload["alias"] = alias
    response = client.post("/links", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def stats(client, code) -> dict:
    response = client.get(f"/links/{code}/stats")
    assert response.status_code == 200, f"/links/{code}/stats -> {response.status_code}"
    return response.json()


def click(client, code, times=1, url=None) -> None:
    for _ in range(times):
        response = client.get(f"/{code}")
        assert response.status_code == 302
        if url is not None:
            assert response.headers["location"] == url


def parse_ts(value: str) -> datetime:
    assert isinstance(value, str), value
    assert TIMESTAMP_RE.fullmatch(value), value
    parsed = datetime.fromisoformat(value)
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def is_clicks(value, expected: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value == expected


def is_html(response) -> bool:
    return response.headers.get("content-type", "").lower().startswith("text/html")


def squash(text: str) -> str:
    return " ".join(text.split())


def numbers_in(text: str) -> set[int]:
    return {int(n) for n in NUMBER_RE.findall(text)}


def stats_page(client, parse_html, code):
    response = client.get(f"/stats/{code}")
    assert response.status_code == 200, f"/stats/{code} -> {response.status_code}"
    assert is_html(response)
    return response, parse_html(response.text)


def assert_no_injected_markup(html: str, doc) -> None:
    assert f"<script>window.{XSS_MARKER}" not in html.lower()
    for script in doc.iter("script"):
        assert XSS_MARKER not in script.raw_text()
    for el in doc.iter():
        for name, value in el.attrs.items():
            if name.startswith("on"):
                assert XSS_MARKER not in (value or "")


def different_code(code: str) -> str:
    """A code of the same length that differs from `code` in its last character."""
    return code[:-1] + ("a" if code[-1] != "a" else "b")


# ---------------------------------------------------------------- AC-12


def test_hidden_ac12_new_link_stats(client):
    url = "https://example.com/new?q=1"
    started = datetime.now(UTC)
    body = create(client, url)
    response = client.get(f"/links/{body['code']}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == body["code"]
    assert data["url"] == url
    assert data["short_url"] == f"{BASE_URL}/{body['code']}"
    assert is_clicks(data["clicks"], 0), data["clicks"]
    assert "last_accessed_at" in data
    assert data["last_accessed_at"] is None
    created = parse_ts(data["created_at"])
    assert abs(created - parse_ts(body["created_at"])) <= SLACK
    assert started - timedelta(minutes=1) <= created <= datetime.now(UTC) + timedelta(minutes=1)


def test_hidden_ac12_new_alias_link_stats(client):
    url = "https://example.com/alias-new"
    create(client, url, "stat-alias")
    data = stats(client, "stat-alias")
    assert data["code"] == "stat-alias"
    assert data["url"] == url
    assert data["short_url"] == f"{BASE_URL}/stat-alias"
    assert is_clicks(data["clicks"], 0)
    assert data["last_accessed_at"] is None


def test_hidden_ac12_short_url_follows_configured_base_url(make_client):
    other = make_client(base_url="https://sho.rt/")
    body = create(other, "https://example.com/base")
    assert stats(other, body["code"])["short_url"] == f"https://sho.rt/{body['code']}"


def test_hidden_ac12_form_created_link_has_stats(client, parse_html):
    url = "https://example.com/from-form"
    response = client.post("/", data={"url": url})
    assert response.status_code == 200
    hrefs = [a.get("href") or "" for a in parse_html(response.text).iter("a")]
    codes = [m.group(1) for h in hrefs if (m := RANDOM_SHORT_URL_RE.fullmatch(h))]
    assert codes
    data = stats(client, codes[0])
    assert data["url"] == url
    assert is_clicks(data["clicks"], 0)
    assert data["last_accessed_at"] is None


# ---------------------------------------------------------------- AC-13


def test_hidden_ac13_three_redirects_count_three(client):
    url = "https://example.com/clicked"
    body = create(client, url)
    started = datetime.now(UTC)
    click(client, body["code"], 3, url)
    finished = datetime.now(UTC)
    data = stats(client, body["code"])
    assert is_clicks(data["clicks"], 3), data["clicks"]
    accessed = parse_ts(data["last_accessed_at"])
    assert started - timedelta(minutes=1) <= accessed <= finished + timedelta(minutes=1)
    assert accessed >= parse_ts(data["created_at"]) - SLACK


def test_hidden_ac13_each_redirect_adds_one(client):
    body = create(client, "https://example.com/step")
    for expected in range(1, 5):
        click(client, body["code"])
        data = stats(client, body["code"])
        assert is_clicks(data["clicks"], expected), (expected, data["clicks"])
        assert data["last_accessed_at"] is not None


def test_hidden_ac13_alias_redirects_are_counted(client):
    create(client, "https://example.com/alias-count", "count-me")
    click(client, "count-me", 3, "https://example.com/alias-count")
    data = stats(client, "count-me")
    assert is_clicks(data["clicks"], 3)
    parse_ts(data["last_accessed_at"])


def test_hidden_ac13_counts_are_per_link(client):
    a = create(client, "https://example.com/a")["code"]
    b = create(client, "https://example.com/b")["code"]
    c = create(client, "https://example.com/c", "third-link")["code"]
    click(client, a, 3)
    click(client, b, 1)
    assert is_clicks(stats(client, a)["clicks"], 3)
    assert is_clicks(stats(client, b)["clicks"], 1)
    untouched = stats(client, c)
    assert is_clicks(untouched["clicks"], 0)
    assert untouched["last_accessed_at"] is None


def test_hidden_ac13_case_variant_aliases_counted_separately(client):
    create(client, "https://example.com/upper", "Case-Link")
    create(client, "https://example.com/lower", "case-link")
    click(client, "Case-Link", 2, "https://example.com/upper")
    click(client, "case-link", 1, "https://example.com/lower")
    assert is_clicks(stats(client, "Case-Link")["clicks"], 2)
    assert is_clicks(stats(client, "case-link")["clicks"], 1)


def test_hidden_ac13_last_accessed_does_not_go_back(client):
    body = create(client, "https://example.com/again")
    click(client, body["code"])
    first = parse_ts(stats(client, body["code"])["last_accessed_at"])
    click(client, body["code"])
    second = parse_ts(stats(client, body["code"])["last_accessed_at"])
    assert second >= first


# ---------------------------------------------------------------- AC-14


def test_hidden_ac14_stats_api_does_not_count_on_new_link(client):
    body = create(client, "https://example.com/peek")
    for _ in range(5):
        assert is_clicks(stats(client, body["code"])["clicks"], 0)


def test_hidden_ac14_stats_api_does_not_count_after_clicks(client):
    body = create(client, "https://example.com/peek2")
    click(client, body["code"], 2)
    for _ in range(5):
        assert is_clicks(stats(client, body["code"])["clicks"], 2)
    click(client, body["code"])
    assert is_clicks(stats(client, body["code"])["clicks"], 3)


def test_hidden_ac14_stats_page_does_not_count(client):
    body = create(client, "https://example.com/peek3")
    for _ in range(3):
        assert client.get(f"/stats/{body['code']}").status_code == 200
    assert is_clicks(stats(client, body["code"])["clicks"], 0)


# ---------------------------------------------------------------- AC-15


def test_hidden_ac15_unknown_codes_do_not_count(client):
    random_code = create(client, "https://example.com/r")["code"]
    create(client, "https://example.com/alias", "My-Alias")
    unknown = [different_code(random_code), "my-alias", "MY-ALIAS", "My-Alia", "My-Alias2", "nope"]
    for code in unknown:
        assert client.get(f"/{code}").status_code == 404, code
    for code in (random_code, "My-Alias"):
        data = stats(client, code)
        assert is_clicks(data["clicks"], 0), (code, data["clicks"])
        assert data["last_accessed_at"] is None


def test_hidden_ac15_unknown_codes_do_not_change_existing_counts(client):
    code = create(client, "https://example.com/r2")["code"]
    click(client, code, 2)
    for _ in range(3):
        assert client.get(f"/{different_code(code)}").status_code == 404
    assert is_clicks(stats(client, code)["clicks"], 2)


# ---------------------------------------------------------------- AC-16


@pytest.mark.parametrize("code", ["Zz9Zz9Z", "no-such-alias", "abc"])
def test_hidden_ac16_unknown_code_stats_api_404(client, code):
    assert client.get(f"/links/{code}/stats").status_code == 404


def test_hidden_ac16_unknown_code_stats_api_404_when_others_exist(client):
    code = create(client, "https://example.com/exists")["code"]
    create(client, "https://example.com/exists2", "Known-Alias")
    assert client.get(f"/links/{different_code(code)}/stats").status_code == 404
    assert client.get("/links/known-alias/stats").status_code == 404


# ---------------------------------------------------------------- AC-17


def test_hidden_ac17_stats_page_for_new_link(client, parse_html):
    url = "https://example.com/stats-page?q=x"
    create(client, url, "page-alias")
    _, doc = stats_page(client, parse_html, "page-alias")
    text = squash(doc.text())
    assert url in doc.text()
    assert NOT_YET in text
    assert 0 in numbers_in(text), "click count 0 not shown"


def test_hidden_ac17_stats_page_after_clicks(client, parse_html):
    url = "https://example.com/stats-page-clicked"
    create(client, url, "clicked-alias")
    click(client, "clicked-alias", 5, url)
    _, doc = stats_page(client, parse_html, "clicked-alias")
    text = squash(doc.text())
    assert url in doc.text()
    assert 5 in numbers_in(text), "click count 5 not shown"
    assert NOT_YET not in text


def test_hidden_ac17_stats_page_for_random_code(client, parse_html):
    url = "https://example.com/random-stats"
    code = create(client, url)["code"]
    _, doc = stats_page(client, parse_html, code)
    assert url in doc.text()
    assert NOT_YET in squash(doc.text())


def test_hidden_ac17_stats_page_shows_short_url(client, parse_html):
    create(client, "https://example.com/short-shown", "shown-alias")
    _, doc = stats_page(client, parse_html, "shown-alias")
    short_url = f"{BASE_URL}/shown-alias"
    hrefs = [a.get("href") or "" for a in doc.iter("a")]
    assert short_url in doc.text() or short_url in hrefs


# ---------------------------------------------------------------- AC-18


@pytest.mark.parametrize("code", ["Zz9Zz9Z", "no-such-alias"])
def test_hidden_ac18_unknown_code_stats_page_404(client, parse_html, code):
    create(client, "https://example.com/other", "Some-Alias")
    response = client.get(f"/stats/{code}")
    assert response.status_code == 404
    assert is_html(response)
    doc = parse_html(response.text)
    assert "링크를 찾을 수 없습니다" in squash(doc.text())
    assert any((a.get("href") or "") in HOME_HREFS for a in doc.iter("a")), "no link to home"


def test_hidden_ac18_case_variant_stats_page_404(client):
    create(client, "https://example.com/other", "Some-Alias")
    response = client.get("/stats/some-alias")
    assert response.status_code == 404
    assert is_html(response)


# ---------------------------------------------------------------- AC-19


def stats_links(doc, code):
    targets = {f"/stats/{code}", f"{BASE_URL}/stats/{code}"}
    return [
        a for a in doc.iter("a") if (a.get("href") or "") in targets and "통계 보기" in a.text()
    ]


def test_hidden_ac19_result_page_links_to_stats(client, parse_html):
    url = "https://example.com/result-stats"
    response = client.post("/", data={"url": url})
    assert response.status_code == 200
    doc = parse_html(response.text)
    hrefs = [a.get("href") or "" for a in doc.iter("a")]
    codes = [m.group(1) for h in hrefs if (m := RANDOM_SHORT_URL_RE.fullmatch(h))]
    assert codes
    links = stats_links(doc, codes[0])
    assert links, '"통계 보기" link to /stats/{code} not found'
    target = client.get(links[0].get("href"))
    assert target.status_code == 200
    assert url in parse_html(target.text).text()


def test_hidden_ac19_result_page_links_to_alias_stats(client, parse_html):
    response = client.post("/", data={"url": "https://example.com/r", "alias": "result-alias"})
    assert response.status_code == 200
    assert stats_links(parse_html(response.text), "result-alias")


# ---------------------------------------------------------------- AC-20


def test_hidden_ac20_clicks_survive_new_app(app_factory):
    url = "https://example.com/persist"
    with TestClient(app_factory(), follow_redirects=False) as first:
        code = create(first, url)["code"]
        click(first, code, 2, url)
        before = stats(first, code)
    with TestClient(app_factory(), follow_redirects=False) as second:
        data = stats(second, code)
        assert is_clicks(data["clicks"], 2), data["clicks"]
        assert data["last_accessed_at"] is not None
        assert parse_ts(data["last_accessed_at"]) == parse_ts(before["last_accessed_at"])
        click(second, code, 1, url)
    with TestClient(app_factory(), follow_redirects=False) as third:
        assert is_clicks(stats(third, code)["clicks"], 3)


def test_hidden_ac20_alias_clicks_survive_new_app(app_factory, parse_html):
    url = "https://example.com/persist-alias"
    with TestClient(app_factory(), follow_redirects=False) as first:
        create(first, url, "kept-alias")
        click(first, "kept-alias", 4, url)
    with TestClient(app_factory(), follow_redirects=False) as second:
        assert is_clicks(stats(second, "kept-alias")["clicks"], 4)
        _, doc = stats_page(second, parse_html, "kept-alias")
        assert 4 in numbers_in(squash(doc.text()))


def test_hidden_ac20_unclicked_link_survives_new_app(app_factory):
    with TestClient(app_factory(), follow_redirects=False) as first:
        code = create(first, "https://example.com/never")["code"]
    with TestClient(app_factory(), follow_redirects=False) as second:
        data = stats(second, code)
        assert is_clicks(data["clicks"], 0)
        assert data["last_accessed_at"] is None


# ---------------------------------------------------------------- AC-21


SPECIAL_URLS = [
    f"https://example.com/?q=<script>window.{XSS_MARKER}=1</script>",
    f"https://example.com/?a=1&b=\"'<script>window.{XSS_MARKER}=2</script>",
    f"https://example.com/path\"><script>window.{XSS_MARKER}=3</script>&x='y'",
    f"https://example.com/x'onmouseover='window.{XSS_MARKER}=4'",
]


@pytest.mark.parametrize("url", SPECIAL_URLS)
def test_hidden_ac21_stats_page_escapes_url(client, parse_html, url):
    code = create(client, url)["code"]
    response, doc = stats_page(client, parse_html, code)
    assert_no_injected_markup(response.text, doc)
    assert url in doc.text()


def test_hidden_ac21_stats_page_escapes_url_after_clicks(client, parse_html):
    url = SPECIAL_URLS[0]
    create(client, url, "xss-alias")
    click(client, "xss-alias", 1)  # Location encoding of special characters is unspecified
    response, doc = stats_page(client, parse_html, "xss-alias")
    assert_no_injected_markup(response.text, doc)
    assert url in doc.text()


# ---------------------------------------------------------------- AC-22


def _stats_response(client, kind):
    if kind == "stats_new":
        code = create(client, "https://example.com/lang")["code"]
        response = client.get(f"/stats/{code}")
        assert response.status_code == 200
    elif kind == "stats_clicked":
        create(client, "https://example.com/lang2", "lang-alias")
        click(client, "lang-alias", 1)
        response = client.get("/stats/lang-alias")
        assert response.status_code == 200
    else:
        response = client.get("/stats/Zz9Zz9Z")
        assert response.status_code == 404
    return response


STATS_KINDS = ["stats_new", "stats_clicked", "stats_not_found"]


@pytest.mark.parametrize("kind", STATS_KINDS)
def test_hidden_ac22_stats_page_has_lang_ko(client, parse_html, kind):
    doc = parse_html(_stats_response(client, kind).text)
    html_elements = list(doc.iter("html"))
    assert html_elements, "no <html> element"
    assert html_elements[0].get("lang") == "ko"


@pytest.mark.parametrize("kind", STATS_KINDS)
def test_hidden_ac22_stats_page_has_viewport_meta(client, parse_html, kind):
    doc = parse_html(_stats_response(client, kind).text)
    assert any(
        (meta.get("name") or "").lower() == "viewport" and (meta.get("content") or "")
        for meta in doc.iter("meta")
    )
