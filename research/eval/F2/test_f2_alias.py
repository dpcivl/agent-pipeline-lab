# EVAL-CANARY-F2-13315d954563022c
"""Hidden acceptance tests for F2 custom aliases (AC-1 to AC-11)."""

from __future__ import annotations

import re

import pytest

BASE_URL = "http://testserver"
CODE_RE = re.compile(r"^[A-Za-z0-9]{7}$")
RANDOM_SHORT_URL_RE = re.compile(r"^http://testserver/([A-Za-z0-9]{7})$")
CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")
XSS_MARKER = "__f2xss"

RESERVED = ["links", "static", "stats", "docs", "redoc", "openapi.json", "api", "admin", "manage"]

# Aliases that satisfy every rule in the spec (4-30 chars, [A-Za-z0-9-],
# no leading/trailing hyphen, not reserved).
VALID_ALIASES = [
    "my-link",
    "MyLink",
    "Abc1234",
    "1234",
    "a-b-c",
    "ab--cd",
    "Release-2026-10",
]

# Aliases that break a character or hyphen rule (AC-5).
BAD_CHAR_ALIASES = [
    pytest.param("my link", id="space"),
    pytest.param("my_link", id="underscore"),
    pytest.param("my/link", id="slash"),
    pytest.param("my.link", id="dot"),
    pytest.param("별칭링크", id="hangul"),
    pytest.param("link-별칭", id="hangul-mixed"),
    pytest.param("my?link", id="question"),
    pytest.param("my#link", id="hash"),
    pytest.param("my%20link", id="percent"),
    pytest.param("my+link", id="plus"),
    pytest.param("my@link", id="at"),
    pytest.param("my:link", id="colon"),
    pytest.param("mylink\n", id="trailing-newline"),
    pytest.param("my\tlink", id="tab"),
]
HYPHEN_EDGE_ALIASES = [
    pytest.param("-mylink", id="leading"),
    pytest.param("mylink-", id="trailing"),
    pytest.param("-my-link-", id="both"),
    pytest.param("----", id="only-hyphens"),
]


def alias_of_length(length: int) -> str:
    """A rule-abiding alias of the given length (letters and digits only)."""
    return ("Ab3d" * 20)[:length]


def post_link(client, url, alias=None):
    payload = {"url": url}
    if alias is not None:
        payload["alias"] = alias
    return client.post("/links", json=payload)


def create(client, url, alias=None) -> dict:
    response = post_link(client, url, alias)
    assert response.status_code == 201, response.text
    return response.json()


def assert_redirects(client, code, url):
    response = client.get(f"/{code}")
    assert response.status_code == 302, f"/{code} -> {response.status_code}"
    assert response.headers["location"] == url


def submit(client, url, alias=None):
    data = {"url": url}
    if alias is not None:
        data["alias"] = alias
    return client.post("/", data=data)


def is_html(response) -> bool:
    return response.headers.get("content-type", "").lower().startswith("text/html")


def field_named(root, name):
    """The first <input> or <textarea> with the given name under `root`."""
    for el in root.iter():
        if el.tag in ("input", "textarea") and el.get("name") == name:
            return el
    return None


def field_value(el) -> str:
    if el.tag == "textarea":
        return el.raw_text()
    return el.get("value") or ""


def labels_for(doc, field):
    """<label> elements attached to `field` (wrapping it or via for=id)."""
    found = [a for a in field.ancestors() if a.tag == "label"]
    field_id = field.get("id")
    if field_id:
        found.extend(lb for lb in doc.iter("label") if lb.get("for") == field_id)
    return found


def post_forms_to_root(doc):
    return [
        form
        for form in doc.iter("form")
        if (form.get("method") or "").lower() == "post" and form.get("action") == "/"
    ]


def shortening_form(doc):
    """The POST / form that contains the name="url" field."""
    forms = [f for f in post_forms_to_root(doc) if field_named(f, "url") is not None]
    assert forms, "no <form method=post action=/> containing name=url field"
    return forms[0]


def link_hrefs(doc) -> list[str]:
    return [a.get("href") or "" for a in doc.iter("a")]


def assert_no_injected_markup(html: str, doc) -> None:
    assert f"<script>window.{XSS_MARKER}" not in html.lower()
    for script in doc.iter("script"):
        assert XSS_MARKER not in script.raw_text()
    for el in doc.iter():
        for name, value in el.attrs.items():
            if name.startswith("on"):
                assert XSS_MARKER not in (value or "")


def error_text_beyond_home(client, parse_html, response, submitted) -> list[str]:
    home_chunks = set(parse_html(client.get("/").text).chunks())
    doc = parse_html(response.text)
    return [c for c in doc.chunks() if c not in home_chunks and c not in submitted]


# ---------------------------------------------------------------- AC-1


@pytest.mark.parametrize("alias", VALID_ALIASES)
def test_hidden_ac01_alias_becomes_code_and_short_url(client, alias):
    url = "https://example.com/alias?q=1"
    response = post_link(client, url, alias)
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == alias
    assert body["short_url"] == f"{BASE_URL}/{alias}"
    assert body["url"] == url
    assert CREATED_AT_RE.fullmatch(body["created_at"]), body["created_at"]


def test_hidden_ac01_alias_short_url_follows_configured_base_url(make_client):
    other = make_client(base_url="https://sho.rt/")
    body = create(other, "https://example.com/base", "my-link")
    assert body["code"] == "my-link"
    assert body["short_url"] == "https://sho.rt/my-link"


# ---------------------------------------------------------------- AC-2


@pytest.mark.parametrize("alias", VALID_ALIASES)
def test_hidden_ac02_alias_redirects_to_original(client, alias):
    url = f"https://example.com/target/{alias}?x=1"
    create(client, url, alias)
    assert_redirects(client, alias, url)


def test_hidden_ac02_alias_and_random_codes_coexist(client):
    random_body = create(client, "https://example.com/random")
    create(client, "https://example.com/aliased", "aliased-link")
    assert_redirects(client, random_body["code"], "https://example.com/random")
    assert_redirects(client, "aliased-link", "https://example.com/aliased")


# ---------------------------------------------------------------- AC-3


def test_hidden_ac03_no_alias_gives_seven_char_code(client):
    codes = set()
    for _ in range(10):
        body = create(client, "https://example.com/no-alias")
        assert CODE_RE.fullmatch(body["code"]), body["code"]
        assert body["short_url"] == f"{BASE_URL}/{body['code']}"
        codes.add(body["code"])
    assert len(codes) == 10
    for code in codes:
        assert_redirects(client, code, "https://example.com/no-alias")


def test_hidden_ac03_form_without_alias_gives_seven_char_code(client, parse_html):
    response = submit(client, "https://example.com/form-no-alias")
    assert response.status_code == 200
    hrefs = [h for h in link_hrefs(parse_html(response.text)) if RANDOM_SHORT_URL_RE.fullmatch(h)]
    assert hrefs, "no <a href> pointing at <base_url>/<7-char code>"


def test_hidden_ac03_form_blank_alias_gives_seven_char_code(client, parse_html):
    """An optional form field left empty is submitted as "" and means "no alias"."""
    url = "https://example.com/form-blank-alias"
    response = submit(client, url, alias="")
    assert response.status_code == 200
    hrefs = [h for h in link_hrefs(parse_html(response.text)) if RANDOM_SHORT_URL_RE.fullmatch(h)]
    assert hrefs, "no <a href> pointing at <base_url>/<7-char code>"
    code = RANDOM_SHORT_URL_RE.fullmatch(hrefs[0]).group(1)
    assert_redirects(client, code, url)


# ---------------------------------------------------------------- AC-4


@pytest.mark.parametrize("length", [4, 30])
def test_hidden_ac04_alias_length_bounds_accepted(client, length):
    alias = alias_of_length(length)
    assert len(alias) == length
    url = f"https://example.com/len{length}"
    body = create(client, url, alias)
    assert body["code"] == alias
    assert_redirects(client, alias, url)


@pytest.mark.parametrize("length", [1, 2, 3, 31, 40])
def test_hidden_ac04_alias_length_bounds_rejected(client, length):
    alias = alias_of_length(length)
    assert len(alias) == length
    assert post_link(client, "https://example.com/len", alias).status_code == 422


# ---------------------------------------------------------------- AC-5


@pytest.mark.parametrize("alias", BAD_CHAR_ALIASES)
def test_hidden_ac05_rejects_disallowed_characters(client, alias):
    assert post_link(client, "https://example.com/chars", alias).status_code == 422


@pytest.mark.parametrize("alias", HYPHEN_EDGE_ALIASES)
def test_hidden_ac05_rejects_leading_or_trailing_hyphen(client, alias):
    assert post_link(client, "https://example.com/hyphen", alias).status_code == 422


# ---------------------------------------------------------------- AC-6


@pytest.mark.parametrize("alias", RESERVED)
def test_hidden_ac06_rejects_reserved_alias(client, alias):
    assert post_link(client, "https://example.com/reserved", alias).status_code == 422


# ---------------------------------------------------------------- AC-7


@pytest.mark.parametrize(
    "second_url",
    ["https://example.com/other", "https://example.com/first"],
    ids=["different-url", "same-url"],
)
def test_hidden_ac07_duplicate_alias_conflicts(client, second_url):
    create(client, "https://example.com/first", "taken-alias")
    response = post_link(client, second_url, "taken-alias")
    assert response.status_code == 409
    assert_redirects(client, "taken-alias", "https://example.com/first")


def test_hidden_ac07_duplicate_alias_conflicts_repeatedly(client):
    create(client, "https://example.com/first", "taken-alias")
    for index in range(3):
        response = post_link(client, f"https://example.com/again{index}", "taken-alias")
        assert response.status_code == 409
    assert_redirects(client, "taken-alias", "https://example.com/first")


def test_hidden_ac07_alias_equal_to_existing_random_code_conflicts(client):
    body = create(client, "https://example.com/random-owner")
    code = body["code"]
    response = post_link(client, "https://example.com/hijack", code)
    assert response.status_code == 409
    assert_redirects(client, code, "https://example.com/random-owner")


# ---------------------------------------------------------------- AC-8


def test_hidden_ac08_aliases_are_case_sensitive(client):
    upper = create(client, "https://example.com/upper", "My-Link")
    lower = create(client, "https://example.com/lower", "my-link")
    assert upper["code"] == "My-Link"
    assert lower["code"] == "my-link"
    assert_redirects(client, "My-Link", "https://example.com/upper")
    assert_redirects(client, "my-link", "https://example.com/lower")


def test_hidden_ac08_case_variants_in_any_order(client):
    create(client, "https://example.com/a", "abcd-link")
    create(client, "https://example.com/b", "ABCD-LINK")
    create(client, "https://example.com/c", "Abcd-Link")
    assert_redirects(client, "abcd-link", "https://example.com/a")
    assert_redirects(client, "ABCD-LINK", "https://example.com/b")
    assert_redirects(client, "Abcd-Link", "https://example.com/c")


def test_hidden_ac08_exact_case_still_conflicts(client):
    create(client, "https://example.com/upper", "My-Link")
    create(client, "https://example.com/lower", "my-link")
    assert post_link(client, "https://example.com/x", "My-Link").status_code == 409
    assert post_link(client, "https://example.com/y", "my-link").status_code == 409


def test_hidden_ac08_other_case_is_not_found_before_creation(client):
    create(client, "https://example.com/upper", "My-Link")
    assert client.get("/my-link").status_code == 404
    assert client.get("/MY-LINK").status_code == 404


# ---------------------------------------------------------------- AC-9


REJECTED_422 = [
    pytest.param({"url": "https://example.com/x", "alias": "abc"}, id="too-short"),
    pytest.param({"url": "https://example.com/x", "alias": alias_of_length(31)}, id="too-long"),
    pytest.param({"url": "https://example.com/x", "alias": "my_link"}, id="underscore"),
    pytest.param({"url": "https://example.com/x", "alias": "my link"}, id="space"),
    pytest.param({"url": "https://example.com/x", "alias": "별칭링크"}, id="hangul"),
    pytest.param({"url": "https://example.com/x", "alias": "-mylink"}, id="leading-hyphen"),
    pytest.param({"url": "https://example.com/x", "alias": "mylink-"}, id="trailing-hyphen"),
    pytest.param({"url": "https://example.com/x", "alias": "links"}, id="reserved-links"),
    pytest.param({"url": "https://example.com/x", "alias": "admin"}, id="reserved-admin"),
    pytest.param({"url": "ftp://example.com/x", "alias": "valid-alias"}, id="bad-url"),
    pytest.param({"url": "", "alias": "valid-alias"}, id="empty-url"),
    pytest.param({"alias": "valid-alias"}, id="missing-url"),
]


def test_hidden_ac09_alias_storage_is_observable_precondition(client, table_counts):
    """Sanity check: a valid alias creation adds rows, so the AC-9 checks are meaningful."""
    before = sum(table_counts().values())
    create(client, "https://example.com/stored", "stored-alias")
    assert sum(table_counts().values()) > before


@pytest.mark.parametrize("payload", REJECTED_422)
def test_hidden_ac09_rejected_422_stores_nothing(client, table_counts, payload):
    create(client, "https://example.com/existing", "existing-one")
    before = table_counts()
    assert client.post("/links", json=payload).status_code == 422
    assert table_counts() == before


def test_hidden_ac09_rejected_409_stores_nothing(client, table_counts):
    create(client, "https://example.com/original", "dup-alias")
    before = table_counts()
    assert post_link(client, "https://example.com/intruder", "dup-alias").status_code == 409
    assert table_counts() == before
    assert_redirects(client, "dup-alias", "https://example.com/original")


@pytest.mark.parametrize("alias", ["abc", alias_of_length(31), "my_link", "-mylink", "mylink-"])
def test_hidden_ac09_rejected_alias_is_not_routable(client, alias):
    assert post_link(client, "https://example.com/x", alias).status_code == 422
    assert client.get(f"/{alias}").status_code == 404


def test_hidden_ac09_alias_rejected_for_bad_url_stays_free(client):
    assert post_link(client, "javascript:alert(1)", "free-alias").status_code == 422
    assert client.get("/free-alias").status_code == 404
    body = create(client, "https://example.com/real", "free-alias")
    assert body["code"] == "free-alias"
    assert_redirects(client, "free-alias", "https://example.com/real")


def test_hidden_ac09_rejections_leave_empty_db_unchanged(client, table_counts):
    before = table_counts()
    for param in REJECTED_422:
        assert client.post("/links", json=param.values[0]).status_code == 422
    assert table_counts() == before


# ---------------------------------------------------------------- AC-10


def test_hidden_ac10_home_form_has_labeled_alias_field(client, parse_html):
    response = client.get("/")
    assert response.status_code == 200
    doc = parse_html(response.text)
    form = shortening_form(doc)
    field = field_named(form, "alias")
    assert field is not None, "no name=alias field in the POST / form"
    assert labels_for(doc, field), "alias field has no <label>"


def test_hidden_ac10_alias_label_text(client, parse_html):
    doc = parse_html(client.get("/").text)
    field = field_named(shortening_form(doc), "alias")
    assert field is not None
    # Whitespace-insensitive, so markup inside the label cannot split the phrase.
    texts = ["".join(label.text().split()) for label in labels_for(doc, field)]
    assert any("별칭(선택)" in text for text in texts), texts


def test_hidden_ac10_form_alias_used_in_result_short_url(client, parse_html):
    url = "https://example.com/form-alias?x=1"
    response = submit(client, url, alias="form-alias")
    assert response.status_code == 200
    assert is_html(response)
    doc = parse_html(response.text)
    assert f"{BASE_URL}/form-alias" in link_hrefs(doc)
    assert url in doc.text()
    assert_redirects(client, "form-alias", url)


def test_hidden_ac10_form_alias_is_case_sensitive(client, parse_html):
    create(client, "https://example.com/api-made", "Form-Case")
    response = submit(client, "https://example.com/form-made", alias="form-case")
    assert response.status_code == 200
    assert f"{BASE_URL}/form-case" in link_hrefs(parse_html(response.text))
    assert_redirects(client, "form-case", "https://example.com/form-made")
    assert_redirects(client, "Form-Case", "https://example.com/api-made")


# ---------------------------------------------------------------- AC-11


INVALID_FORM_ALIASES = [
    pytest.param("abc", id="too-short"),
    pytest.param(alias_of_length(31), id="too-long"),
    pytest.param("my link", id="space"),
    pytest.param("my_link", id="underscore"),
    pytest.param("별칭링크", id="hangul"),
    pytest.param("-mylink", id="leading-hyphen"),
    pytest.param("stats", id="reserved"),
    pytest.param(f'x"><script>window.{XSS_MARKER}=1</script>', id="markup"),
]


@pytest.mark.parametrize("alias", INVALID_FORM_ALIASES)
def test_hidden_ac11_invalid_alias_form_shows_422(client, parse_html, alias):
    url = "https://example.com/form-invalid"
    response = submit(client, url, alias=alias)
    assert response.status_code == 422
    assert is_html(response)
    assert error_text_beyond_home(client, parse_html, response, {url, alias}), (
        "error page shows no text beyond the home page"
    )


@pytest.mark.parametrize("alias", INVALID_FORM_ALIASES)
def test_hidden_ac11_invalid_alias_form_keeps_values(client, parse_html, alias):
    url = "https://example.com/form-invalid?q=1&r=2"
    response = submit(client, url, alias=alias)
    assert response.status_code == 422
    doc = parse_html(response.text)
    assert_no_injected_markup(response.text, doc)
    url_field = field_named(doc, "url")
    alias_field = field_named(doc, "alias")
    assert url_field is not None, "error page has no name=url field"
    assert alias_field is not None, "error page has no name=alias field"
    assert field_value(url_field) == url
    assert field_value(alias_field) == alias


def test_hidden_ac11_duplicate_alias_form_shows_409(client, parse_html):
    create(client, "https://example.com/owner", "busy-alias")
    url = "https://example.com/form-dup"
    response = submit(client, url, alias="busy-alias")
    assert response.status_code == 409
    assert is_html(response)
    assert error_text_beyond_home(client, parse_html, response, {url, "busy-alias"}), (
        "error page shows no text beyond the home page"
    )


def test_hidden_ac11_duplicate_alias_form_keeps_values(client, parse_html):
    create(client, "https://example.com/owner", "busy-alias")
    url = "https://example.com/form-dup?keep=1"
    response = submit(client, url, alias="busy-alias")
    assert response.status_code == 409
    doc = parse_html(response.text)
    url_field = field_named(doc, "url")
    alias_field = field_named(doc, "alias")
    assert url_field is not None and alias_field is not None
    assert field_value(url_field) == url
    assert field_value(alias_field) == "busy-alias"
    assert_redirects(client, "busy-alias", "https://example.com/owner")


def test_hidden_ac11_form_alias_equal_to_random_code_shows_409(client, parse_html):
    code = create(client, "https://example.com/random-owner")["code"]
    response = submit(client, "https://example.com/form-hijack", alias=code)
    assert response.status_code == 409
    assert is_html(response)
    assert_redirects(client, code, "https://example.com/random-owner")


def test_hidden_ac11_invalid_url_with_alias_keeps_both_values(client, parse_html):
    url = "ftp://example.com/file"
    response = submit(client, url, alias="good-alias")
    assert response.status_code == 422
    assert is_html(response)
    doc = parse_html(response.text)
    url_field = field_named(doc, "url")
    alias_field = field_named(doc, "alias")
    assert url_field is not None and alias_field is not None
    assert field_value(url_field) == url
    assert field_value(alias_field) == "good-alias"
    assert client.get("/good-alias").status_code == 404


@pytest.mark.parametrize(
    ("alias", "status"),
    [("abc", 422), ("my_link", 422), ("links", 422), ("busy-alias", 409)],
)
def test_hidden_ac11_form_rejection_stores_nothing(client, table_counts, alias, status):
    create(client, "https://example.com/owner", "busy-alias")
    before = table_counts()
    assert submit(client, "https://example.com/form", alias=alias).status_code == status
    assert table_counts() == before
