# EVAL-CANARY-F3-a35abd6a9f5f3b84
"""Hidden acceptance tests for F3 deletion and rate limiting (AC-8 to AC-14)."""

from __future__ import annotations

import re

import pytest
from f3_support import (
    BASE_URL,
    KEY_A,
    KEY_B,
    KEY_UNKNOWN,
    is_html,
    parse_html,
)

SHORT_HREF_RE = re.compile(r"^http://testserver/([A-Za-z0-9-]+)$")


def create(client, url: str, key: str | None = None, alias: str | None = None) -> dict:
    body = {"url": url}
    if alias is not None:
        body["alias"] = alias
    headers = {"X-API-Key": key} if key is not None else {}
    response = client.post("/links", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def delete(client, code: str, key: str | None = None):
    headers = {"X-API-Key": key} if key is not None else {}
    return client.delete(f"/links/{code}", headers=headers)


def assert_alive(client, code: str, url: str) -> None:
    redirect = client.get(f"/{code}")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == url
    assert client.get(f"/links/{code}/stats").status_code == 200


def assert_gone(client, code: str) -> None:
    assert client.get(f"/{code}").status_code == 404
    assert client.get(f"/links/{code}/stats").status_code == 404
    assert client.get(f"/stats/{code}").status_code == 404


def form_create(client, url: str, alias: str | None = None):
    data = {"url": url}
    if alias is not None:
        data["alias"] = alias
    return client.post("/", data=data)


def code_from_result_page(response) -> str:
    doc = parse_html(response.text)
    for a in doc.iter("a"):
        match = SHORT_HREF_RE.fullmatch(a.get("href") or "")
        if match:
            return match.group(1)
    raise AssertionError("no short link on the result page")


def assert_retry_after(response) -> None:
    value = response.headers.get("retry-after")
    assert value is not None, "429 without Retry-After"
    assert value.strip().isdigit(), f"Retry-After is not seconds: {value!r}"


def home_url_form(doc):
    for form in doc.iter("form"):
        if (form.get("method") or "").lower() != "post":
            continue
        if (form.get("action") or "") not in ("/", f"{BASE_URL}/"):
            continue
        if any(el.get("name") == "url" for el in form.iter() if el.tag in ("input", "textarea")):
            return form
    return None


# ---------------------------------------------------------------- AC-8


def test_hidden_ac08_owner_delete_returns_204_then_404_everywhere(client):
    url = "https://example.com/f3/delete-me"
    keep_url = "https://example.com/f3/keep-me"
    create(client, url, KEY_A, alias="f3-delete-me")
    create(client, keep_url, KEY_A, alias="f3-keep-me")
    assert_alive(client, "f3-delete-me", url)
    assert client.get("/stats/f3-delete-me").status_code == 200

    response = delete(client, "f3-delete-me", KEY_A)
    assert response.status_code == 204

    assert_gone(client, "f3-delete-me")
    assert_alive(client, "f3-keep-me", keep_url)


@pytest.mark.parametrize("key", [KEY_A, KEY_B], ids=["key-a", "key-b"])
def test_hidden_ac08_owner_delete_random_code(client, key):
    code = create(client, "https://example.com/f3/random", key)["code"]
    assert delete(client, code, key).status_code == 204
    assert_gone(client, code)


# ---------------------------------------------------------------- AC-9


@pytest.mark.parametrize("owner", [KEY_A, None], ids=["owned", "ownerless"])
def test_hidden_ac09_delete_without_key_is_401(client, owner):
    url = "https://example.com/f3/no-key-delete"
    code = create(client, url, owner)["code"]
    assert delete(client, code).status_code == 401
    assert_alive(client, code, url)


@pytest.mark.parametrize(
    "key",
    [
        pytest.param(KEY_UNKNOWN, id="unknown"),
        pytest.param(KEY_A[:-1], id="prefix-of-registered"),
        pytest.param(KEY_A.upper(), id="registered-upper"),
    ],
)
def test_hidden_ac09_delete_with_unregistered_key_is_401(client, key):
    url = "https://example.com/f3/bad-key-delete"
    code = create(client, url, KEY_A)["code"]
    assert delete(client, code, key).status_code == 401
    assert_alive(client, code, url)


# ---------------------------------------------------------------- AC-10


def test_hidden_ac10_delete_by_other_owner_forbidden(client):
    url = "https://example.com/f3/owned-by-a"
    code = create(client, url, KEY_A)["code"]
    assert delete(client, code, KEY_B).status_code == 403
    assert_alive(client, code, url)
    assert client.get(f"/stats/{code}").status_code == 200
    assert delete(client, code, KEY_A).status_code == 204


@pytest.mark.parametrize("key", [KEY_A, KEY_B], ids=["key-a", "key-b"])
def test_hidden_ac10_delete_ownerless_link_forbidden(client, key):
    url = "https://example.com/f3/ownerless"
    code = create(client, url)["code"]
    assert delete(client, code, key).status_code == 403
    assert_alive(client, code, url)


def test_hidden_ac10_form_created_link_has_no_owner(client):
    url = "https://example.com/f3/from-form"
    response = form_create(client, url)
    assert response.status_code == 200
    code = code_from_result_page(response)
    assert delete(client, code, KEY_A).status_code == 403
    assert_alive(client, code, url)


# ---------------------------------------------------------------- AC-11


@pytest.mark.parametrize("code", ["Zz9Zz9Z", "f3-no-such-alias"])
@pytest.mark.parametrize("key", [KEY_A, KEY_B], ids=["key-a", "key-b"])
def test_hidden_ac11_delete_unknown_code_is_404(client, key, code):
    create(client, "https://example.com/f3/exists", key)
    assert delete(client, code, key).status_code == 404


def test_hidden_ac11_delete_twice_second_is_404(client):
    code = create(client, "https://example.com/f3/twice", KEY_A)["code"]
    assert delete(client, code, KEY_A).status_code == 204
    assert delete(client, code, KEY_A).status_code == 404


# ---------------------------------------------------------------- AC-12


@pytest.mark.parametrize("new_owner", [None, KEY_A], ids=["anonymous", "same-owner"])
def test_hidden_ac12_deleted_alias_can_be_reused(client, new_owner):
    alias = "f3-reuse-me"
    create(client, "https://example.com/f3/old", KEY_A, alias=alias)
    assert client.get(f"/{alias}").status_code == 302  # one click on the old link
    assert delete(client, alias, KEY_A).status_code == 204

    body = create(client, "https://example.com/f3/new", new_owner, alias=alias)
    assert body["code"] == alias
    assert body["short_url"] == f"{BASE_URL}/{alias}"
    stats = client.get(f"/links/{alias}/stats").json()
    assert stats["url"] == "https://example.com/f3/new"
    assert stats["clicks"] == 0
    assert stats["last_accessed_at"] is None
    assert_alive(client, alias, "https://example.com/f3/new")


def test_hidden_ac12_reused_alias_belongs_to_new_owner(client):
    alias = "f3-new-owner"
    create(client, "https://example.com/f3/a", KEY_A, alias=alias)
    assert delete(client, alias, KEY_A).status_code == 204
    create(client, "https://example.com/f3/b", KEY_B, alias=alias)
    assert delete(client, alias, KEY_A).status_code == 403
    assert_alive(client, alias, "https://example.com/f3/b")
    assert delete(client, alias, KEY_B).status_code == 204


# ---------------------------------------------------------------- AC-13


def test_hidden_ac13_fourth_api_creation_is_429_shared_with_form(make_client, limited_app):
    client = make_client(app=limited_app)
    assert client.post("/links", json={"url": "https://example.com/r/1"}).status_code == 201
    assert form_create(client, "https://example.com/r/2").status_code == 200
    keyed = client.post(
        "/links", json={"url": "https://example.com/r/3"}, headers={"X-API-Key": KEY_A}
    )
    assert keyed.status_code == 201

    fourth = client.post("/links", json={"url": "https://example.com/r/4", "alias": "f3-fourth"})
    assert fourth.status_code == 429
    assert_retry_after(fourth)
    assert client.get("/f3-fourth").status_code == 404
    assert client.get("/links/f3-fourth/stats").status_code == 404


def test_hidden_ac13_fourth_form_creation_is_429_shared_with_api(make_client, limited_app):
    client = make_client(app=limited_app)
    home_chunks = set(parse_html(client.get("/").text).chunks())
    assert form_create(client, "https://example.com/r/1").status_code == 200
    assert client.post("/links", json={"url": "https://example.com/r/2"}).status_code == 201
    assert form_create(client, "https://example.com/r/3").status_code == 200

    url = "https://example.com/r/4"
    fourth = form_create(client, url, alias="f3-fourth-form")
    assert fourth.status_code == 429
    assert_retry_after(fourth)
    assert is_html(fourth)
    doc = parse_html(fourth.text)
    assert home_url_form(doc) is not None, "429 page is not the home screen with the URL form"
    extra = [c for c in doc.chunks() if c not in home_chunks and c not in (url, "f3-fourth-form")]
    assert extra, "429 page shows no notice beyond the home screen"
    assert client.get("/f3-fourth-form").status_code == 404
    assert client.get("/links/f3-fourth-form/stats").status_code == 404


def test_hidden_ac13_limit_counts_per_client_ip(make_client, limited_app):
    first = make_client(app=limited_app, client_host="203.0.113.10")
    other = make_client(app=limited_app, client_host="203.0.113.20")
    for n in range(3):
        assert first.post("/links", json={"url": f"https://example.com/ip/{n}"}).status_code == 201
    assert first.post("/links", json={"url": "https://example.com/ip/4"}).status_code == 429
    assert other.post("/links", json={"url": "https://example.com/ip/5"}).status_code == 201


# ---------------------------------------------------------------- AC-14


def test_hidden_ac14_redirect_and_stats_work_after_limit(make_client, limited_app):
    client = make_client(app=limited_app)
    urls = [f"https://example.com/after/{n}" for n in range(3)]
    codes = [create(client, url)["code"] for url in urls]
    assert client.post("/links", json={"url": "https://example.com/after/x"}).status_code == 429

    for code, url in zip(codes, urls, strict=True):
        for _ in range(2):
            redirect = client.get(f"/{code}")
            assert redirect.status_code == 302
            assert redirect.headers["location"] == url
        stats = client.get(f"/links/{code}/stats")
        assert stats.status_code == 200
        assert stats.json()["clicks"] == 2
        assert client.get(f"/stats/{code}").status_code == 200


def test_hidden_ac14_reads_do_not_use_up_the_limit(make_client, limited_app):
    client = make_client(app=limited_app)
    code = create(client, "https://example.com/reads/0")["code"]
    for _ in range(4):
        assert client.get(f"/{code}").status_code == 302
        assert client.get(f"/links/{code}/stats").status_code == 200
        assert client.get(f"/stats/{code}").status_code == 200
    create(client, "https://example.com/reads/1")
    create(client, "https://example.com/reads/2")
