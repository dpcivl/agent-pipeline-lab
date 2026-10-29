# EVAL-CANARY-F3-a35abd6a9f5f3b84
"""Hidden acceptance tests for the F3 manage screen (AC-15 to AC-21)."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit

import pytest
from f3_support import (
    BASE_URL,
    KEY_A,
    KEY_B,
    KEY_UNKNOWN,
    action_path,
    assert_no_key_leak,
    delete_request,
    delete_rows,
    field_labels,
    has_lang_ko,
    has_viewport_meta,
    is_html,
    manage_login,
    manage_login_form,
    parse_html,
    post_form,
    squash,
)

XSS_MARKER = "__f3xss"

# Aliases chosen so that none is a prefix of another.
LINKS = {
    "alpha-one": ("f3m-alpha-one", "https://example.com/f3m/alpha/first", KEY_A),
    "alpha-two": ("f3m-alpha-two", "https://example.com/f3m/alpha/second", KEY_A),
    "bravo-one": ("f3m-bravo-one", "https://example.com/f3m/bravo/only", KEY_B),
    "nobody-one": ("f3m-nobody-one", "https://example.com/f3m/nobody/only", None),
}
OWNED_BY = {
    KEY_A: ["alpha-one", "alpha-two"],
    KEY_B: ["bravo-one"],
}


def short_url(code: str) -> str:
    return f"{BASE_URL}/{code}"


def create(client, url: str, key: str | None = None, alias: str | None = None) -> dict:
    body = {"url": url}
    if alias is not None:
        body["alias"] = alias
    headers = {"X-API-Key": key} if key is not None else {}
    response = client.post("/links", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def seed(client) -> None:
    for alias, url, key in LINKS.values():
        create(client, url, key, alias=alias)


def list_page(client, key: str):
    response = manage_login(client, key)
    assert response.status_code == 200, response.status_code
    assert is_html(response)
    return response


def own_short_urls(key: str) -> list[str]:
    return [short_url(LINKS[name][0]) for name in OWNED_BY[key]]


def shows_short_url(doc, url: str) -> bool:
    return url in doc.text() or any((a.get("href") or "") == url for a in doc.iter("a"))


def assert_alive(client, code: str, url: str) -> None:
    redirect = client.get(f"/{code}")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == url
    assert client.get(f"/links/{code}/stats").status_code == 200


def number_tokens(text: str) -> list[str]:
    return re.findall(r"\d+", text)


def assert_no_injected_markup(html: str, doc) -> None:
    assert f"<script>window.{XSS_MARKER}" not in html.lower()
    for script in doc.iter("script"):
        assert XSS_MARKER not in "".join(c for c in script.children if isinstance(c, str))
    for el in doc.iter():
        for name, value in el.attrs.items():
            if name.startswith("on"):
                assert XSS_MARKER not in (value or "")


# ---------------------------------------------------------------- AC-15


def test_hidden_ac15_manage_returns_html(client):
    response = client.get("/manage")
    assert response.status_code == 200
    assert is_html(response)
    assert_no_key_leak(client)


def test_hidden_ac15_manage_has_password_api_key_field(client):
    doc = parse_html(client.get("/manage").text)
    fields = [el for el in doc.iter("input") if el.get("name") == "api_key"]
    assert fields, "no input name=api_key"
    assert (fields[0].get("type") or "").lower() == "password"


def test_hidden_ac15_api_key_field_labeled(client):
    doc = parse_html(client.get("/manage").text)
    fields = [el for el in doc.iter("input") if el.get("name") == "api_key"]
    assert fields
    labels = field_labels(doc, fields[0])
    assert labels, "api_key field has no <label>"
    assert any("API 키" in label for label in labels)


def test_hidden_ac15_key_form_posts_to_manage(client):
    doc = parse_html(client.get("/manage").text)
    form = manage_login_form(doc)
    assert form is not None, "api_key field is not in a method=post form"
    assert action_path(form, "/manage") == "/manage"


# ---------------------------------------------------------------- AC-16


@pytest.mark.parametrize("key", [KEY_A, KEY_B], ids=["owner-a", "owner-b"])
def test_hidden_ac16_list_shows_only_own_links(client, key):
    seed(client)
    response = list_page(client, key)
    doc = parse_html(response.text)
    for name, (alias, url, owner) in LINKS.items():
        if owner == key:
            assert shows_short_url(doc, short_url(alias)), f"own link {name} not listed"
            assert url in doc.text(), f"original URL of {name} not shown"
        else:
            assert alias not in response.text, f"{name} must not be listed"
            assert url not in response.text, f"{name} must not be listed"
    assert_no_key_leak(client)


def test_hidden_ac16_list_row_contents(client):
    seed(client)
    alias, url, _ = LINKS["alpha-one"]
    for _ in range(61):  # a count that cannot be mistaken for a date or time part
        assert client.get(f"/{alias}").status_code == 302
    doc = parse_html(list_page(client, KEY_A).text)
    rows = delete_rows(doc, own_short_urls(KEY_A))
    assert set(rows) == set(own_short_urls(KEY_A)), "each own link needs a row with 삭제"
    row, _button = rows[short_url(alias)]
    row_text = " ".join(row.chunks())
    assert url in row_text
    assert "61" in number_tokens(row_text), "click count not shown in the row"
    assert "없음" in row_text, 'no-expiry link should show "없음"'
    assert_no_key_leak(client)


def test_hidden_ac16_owner_without_links_sees_none(client):
    create(client, "https://example.com/f3m/alpha/lonely", KEY_A, alias="f3m-lonely")
    response = list_page(client, KEY_B)
    assert "f3m-lonely" not in response.text
    assert "https://example.com/f3m/alpha/lonely" not in response.text
    assert_no_key_leak(client)


# ---------------------------------------------------------------- AC-17


@pytest.mark.parametrize(
    "key",
    [
        pytest.param(KEY_UNKNOWN, id="unknown"),
        pytest.param(KEY_A[:-1], id="prefix-of-registered"),
    ],
)
def test_hidden_ac17_wrong_key_shows_401_error(client, key):
    seed(client)
    form_chunks = set(parse_html(client.get("/manage").text).chunks())
    response = manage_login(client, key)
    assert response.status_code == 401
    assert is_html(response)
    doc = parse_html(response.text)
    extra = [c for c in doc.chunks() if c not in form_chunks and c != key]
    assert extra, "401 page shows no error message"
    assert "f3m-alpha-one" not in response.text
    assert_no_key_leak(client)


# ---------------------------------------------------------------- AC-18


def test_hidden_ac18_delete_from_manage_screen(client):
    seed(client)
    doc = parse_html(list_page(client, KEY_A).text)
    rows = delete_rows(doc, own_short_urls(KEY_A))
    target = short_url(LINKS["alpha-one"][0])
    assert target in rows, "no row with a 삭제 button for the link"
    path, fields = delete_request(doc, rows[target][1], password=KEY_A)

    response = post_form(client, path, fields)
    assert response.status_code == 200
    assert is_html(response)
    after = parse_html(response.text)
    remaining = delete_rows(after, own_short_urls(KEY_A))
    assert target not in remaining, "deleted link is still listed"
    assert short_url(LINKS["alpha-two"][0]) in remaining, "other own link vanished"

    gone = LINKS["alpha-one"][0]
    assert client.get(f"/{gone}").status_code == 404
    assert client.get(f"/links/{gone}/stats").status_code == 404
    alias, url, _ = LINKS["alpha-two"]
    assert_alive(client, alias, url)
    assert_no_key_leak(client)


def _retarget(path: str, fields, old: str, new: str):
    """Point a delete request at another code wherever the old code appears."""
    changed = old in path
    new_fields = []
    for name, value in fields:
        if old in value:
            changed = True
            value = value.replace(old, new)
        new_fields.append((name, value))
    return path.replace(old, new), new_fields, changed


@pytest.mark.parametrize("victim", ["bravo-one", "nobody-one"])
def test_hidden_ac18_cannot_delete_others_link_from_manage_screen(client, victim):
    seed(client)
    doc = parse_html(list_page(client, KEY_A).text)
    rows = delete_rows(doc, own_short_urls(KEY_A))
    own = short_url(LINKS["alpha-one"][0])
    assert own in rows, "no row with a 삭제 button for the link"
    path, fields = delete_request(doc, rows[own][1], password=KEY_A)

    victim_alias, victim_url, _ = LINKS[victim]
    path, fields, changed = _retarget(path, fields, LINKS["alpha-one"][0], victim_alias)
    if changed:
        response = post_form(client, path, fields)
        assert response.status_code < 500
    # Either the request was refused, or the form cannot name another link at all.
    assert_alive(client, victim_alias, victim_url)
    assert_no_key_leak(client)


# ---------------------------------------------------------------- AC-19


VALID_SPECIAL_URLS = [
    f"https://example.com/?q=<script>window.{XSS_MARKER}=1</script>",
    f"https://example.com/?a=1&b=\"'<script>window.{XSS_MARKER}=2</script>",
    f"https://example.com/path\"><script>window.{XSS_MARKER}=3</script>&x='y'",
]


def test_hidden_ac19_list_escapes_original_url(client):
    for url in VALID_SPECIAL_URLS:
        create(client, url, KEY_A)
    response = list_page(client, KEY_A)
    doc = parse_html(response.text)
    assert_no_injected_markup(response.text, doc)
    for url in VALID_SPECIAL_URLS:
        assert url in doc.text()
    assert_no_key_leak(client)


def test_hidden_ac19_expired_link_marked_in_list(expiry_world):
    client = expiry_world.client
    expiring = short_url("f3-expiring")
    future = short_url("f3-future")
    forever = short_url("f3-forever")
    doc = parse_html(list_page(client, KEY_A).text)
    rows = delete_rows(doc, [expiring, future, forever])
    assert set(rows) == {expiring, future, forever}, "each own link needs a row with 삭제"
    assert "만료됨" in " ".join(rows[expiring][0].chunks())
    assert "만료됨" not in " ".join(rows[future][0].chunks())
    assert "만료됨" not in " ".join(rows[forever][0].chunks())
    assert "없음" in " ".join(rows[forever][0].chunks())
    assert_no_key_leak(client)


# ---------------------------------------------------------------- AC-20


def test_hidden_ac20_home_links_to_manage(client):
    doc = parse_html(client.get("/").text)
    links = []
    for a in doc.iter("a"):
        target = urlsplit(urljoin(f"{BASE_URL}/", a.get("href") or ""))
        if target.netloc == "testserver" and target.path == "/manage":
            links.append(squash(a.text()))
    assert any("내 링크 관리" in text for text in links), "no 내 링크 관리 link to /manage"


# ---------------------------------------------------------------- AC-21


def _screen(kind, client, request):
    if kind == "expired":
        response = request.getfixturevalue("expiry_world").client.get("/f3-expiring")
        assert response.status_code == 410
        return response
    if kind == "manage_form":
        response = client.get("/manage")
        assert response.status_code == 200
        return response
    seed(client)
    if kind == "manage_error":
        response = manage_login(client, KEY_UNKNOWN)
        assert response.status_code == 401
        return response
    response = list_page(client, KEY_A)
    if kind == "manage_list":
        return response
    doc = parse_html(response.text)
    rows = delete_rows(doc, own_short_urls(KEY_A))
    target = short_url(LINKS["alpha-one"][0])
    assert target in rows
    path, fields = delete_request(doc, rows[target][1], password=KEY_A)
    response = post_form(client, path, fields)
    assert response.status_code == 200
    return response


SCREENS = ["manage_form", "manage_list", "manage_error", "manage_after_delete", "expired"]


@pytest.mark.parametrize("kind", SCREENS)
def test_hidden_ac21_screen_has_lang_ko(client, request, kind):
    response = _screen(kind, client, request)
    assert is_html(response)
    assert has_lang_ko(parse_html(response.text))


@pytest.mark.parametrize("kind", SCREENS)
def test_hidden_ac21_screen_has_viewport_meta(client, request, kind):
    response = _screen(kind, client, request)
    assert has_viewport_meta(parse_html(response.text))
