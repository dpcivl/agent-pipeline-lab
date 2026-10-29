"""Hidden acceptance tests for F1 web pages (AC-16 to AC-23)."""

from __future__ import annotations

import re

import pytest

BASE_URL = "http://testserver"
SHORT_URL_RE = re.compile(r"^http://testserver/([A-Za-z0-9]{7})$")
HOME_HREFS = {"/", f"{BASE_URL}/", BASE_URL}

PREFIX = "https://example.com/"
XSS_MARKER = "__f1xss"


def url_of_length(length: int) -> str:
    return PREFIX + "a" * (length - len(PREFIX))


def submit(client, url):
    return client.post("/", data={"url": url})


def is_html(response) -> bool:
    return response.headers.get("content-type", "").lower().startswith("text/html")


def squash(text: str) -> str:
    return " ".join(text.split())


def url_field(root):
    """The first <input> or <textarea> named "url" under `root`."""
    for el in root.iter():
        if el.tag in ("input", "textarea") and el.get("name") == "url":
            return el
    return None


def field_value(el) -> str:
    if el.tag == "textarea":
        return el.text()
    return el.get("value") or ""


def is_labeled(doc, field) -> bool:
    if any(a.tag == "label" for a in field.ancestors()):
        return True
    field_id = field.get("id")
    return bool(field_id) and any(lb.get("for") == field_id for lb in doc.iter("label"))


def post_forms_to_root(doc):
    return [
        form
        for form in doc.iter("form")
        if (form.get("method") or "").lower() == "post" and form.get("action") == "/"
    ]


def submit_labels(form) -> list[str]:
    labels = []
    for el in form.iter():
        if el.tag == "button" and (el.get("type") or "submit").lower() == "submit":
            labels.append(squash(el.text()))
        elif el.tag == "input" and (el.get("type") or "").lower() == "submit":
            labels.append(squash(el.get("value") or ""))
    return labels


def button_labels(doc) -> list[str]:
    labels = []
    for el in doc.iter():
        if el.tag == "button":
            labels.append(squash(el.text()))
        elif el.tag == "input" and (el.get("type") or "").lower() in ("button", "submit"):
            labels.append(squash(el.get("value") or ""))
    return labels


def short_links(doc, pattern=SHORT_URL_RE):
    return [a for a in doc.iter("a") if pattern.fullmatch(a.get("href") or "")]


def home_links(doc):
    return [a for a in doc.iter("a") if (a.get("href") or "") in HOME_HREFS]


def assert_no_injected_markup(html: str, doc) -> None:
    assert f"<script>window.{XSS_MARKER}" not in html.lower()
    for script in doc.iter("script"):
        assert XSS_MARKER not in "".join(c for c in script.children if isinstance(c, str))
    for el in doc.iter():
        for name, value in el.attrs.items():
            if name.startswith("on"):
                assert XSS_MARKER not in (value or "")


INVALID_FORM_URLS = [
    pytest.param("ftp://example.com/file", id="ftp"),
    pytest.param("javascript:alert(1)", id="javascript"),
    pytest.param("mailto:a@example.com", id="mailto"),
    pytest.param("https://", id="no-host"),
    pytest.param("", id="empty"),
    pytest.param(url_of_length(2049), id="too-long"),
]


# ---------------------------------------------------------------- AC-16


def test_ac16_home_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert is_html(response)


def test_ac16_home_has_post_form_to_root(client, parse_html):
    doc = parse_html(client.get("/").text)
    forms = [f for f in post_forms_to_root(doc) if url_field(f) is not None]
    assert forms, "no <form method=post action=/> containing name=url field"


def test_ac16_url_field_has_label(client, parse_html):
    doc = parse_html(client.get("/").text)
    forms = [f for f in post_forms_to_root(doc) if url_field(f) is not None]
    assert forms
    assert is_labeled(doc, url_field(forms[0]))


def test_ac16_submit_button_says_shorten(client, parse_html):
    doc = parse_html(client.get("/").text)
    forms = [f for f in post_forms_to_root(doc) if url_field(f) is not None]
    assert forms
    assert any("줄이기" in label for label in submit_labels(forms[0]))


# ---------------------------------------------------------------- AC-17


def test_ac17_result_page_shows_short_link_and_original(client, parse_html):
    url = "https://example.com/web?q=1"
    response = submit(client, url)
    assert response.status_code == 200
    assert is_html(response)
    doc = parse_html(response.text)
    assert short_links(doc), "no <a href> pointing at <base_url>/<7-char code>"
    assert url in doc.text()


def test_ac17_short_link_uses_configured_base_url(make_client, parse_html):
    other = make_client(base_url="https://sho.rt/")
    response = submit(other, "https://example.com/base")
    assert response.status_code == 200
    doc = parse_html(response.text)
    assert short_links(doc, re.compile(r"^https://sho\.rt/[A-Za-z0-9]{7}$"))


def test_ac17_accepts_http_url(client, parse_html):
    url = "http://example.com/plain"
    response = submit(client, url)
    assert response.status_code == 200
    doc = parse_html(response.text)
    assert short_links(doc)
    assert url in doc.text()


# ---------------------------------------------------------------- AC-18


def test_ac18_result_page_has_copy_button(client, parse_html):
    response = submit(client, "https://example.com/copy")
    assert response.status_code == 200
    doc = parse_html(response.text)
    assert any("복사" in label for label in button_labels(doc))


def test_ac18_result_page_links_home_to_shorten_another(client, parse_html):
    response = submit(client, "https://example.com/again")
    assert response.status_code == 200
    doc = parse_html(response.text)
    assert any("다른 URL 줄이기" in squash(a.text()) for a in home_links(doc))


# ---------------------------------------------------------------- AC-19


@pytest.mark.parametrize("bad_url", INVALID_FORM_URLS)
def test_ac19_invalid_url_shows_422_error_page(client, parse_html, bad_url):
    response = submit(client, bad_url)
    assert response.status_code == 422
    assert is_html(response)


@pytest.mark.parametrize("bad_url", INVALID_FORM_URLS)
def test_ac19_invalid_url_keeps_submitted_value(client, parse_html, bad_url):
    doc = parse_html(submit(client, bad_url).text)
    field = url_field(doc)
    assert field is not None, "error page has no name=url field"
    assert field_value(field) == bad_url


@pytest.mark.parametrize("bad_url", INVALID_FORM_URLS)
def test_ac19_invalid_url_shows_error_message(client, parse_html, bad_url):
    home_chunks = set(parse_html(client.get("/").text).chunks())
    doc = parse_html(submit(client, bad_url).text)
    extra = [c for c in doc.chunks() if c not in home_chunks and c != bad_url]
    assert extra, "error page shows no text beyond the home page"


@pytest.mark.parametrize("bad_url", INVALID_FORM_URLS)
def test_ac19_invalid_url_stores_nothing(client, table_counts, bad_url):
    before = table_counts()
    assert submit(client, bad_url).status_code == 422
    assert table_counts() == before


def test_ac19_missing_url_field_rejected_and_not_stored(client, table_counts):
    before = table_counts()
    assert client.post("/", data={}).status_code == 422
    assert table_counts() == before


# ---------------------------------------------------------------- AC-20


VALID_SPECIAL_URLS = [
    f"https://example.com/?q=<script>window.{XSS_MARKER}=1</script>",
    f"https://example.com/?a=1&b=\"'<script>window.{XSS_MARKER}=2</script>",
    f"https://example.com/path\"><script>window.{XSS_MARKER}=3</script>&x='y'",
]

INVALID_SPECIAL_URLS = [
    f"javascript:<script>window.{XSS_MARKER}=4</script>",
    f"ftp://example.com/\"><script>window.{XSS_MARKER}=5</script>&x='y'",
]


@pytest.mark.parametrize("url", VALID_SPECIAL_URLS)
def test_ac20_result_page_escapes_special_characters(client, parse_html, url):
    response = submit(client, url)
    assert response.status_code == 200
    doc = parse_html(response.text)
    assert_no_injected_markup(response.text, doc)
    assert url in doc.text()


@pytest.mark.parametrize("url", INVALID_SPECIAL_URLS)
def test_ac20_error_page_escapes_special_characters(client, parse_html, url):
    response = submit(client, url)
    assert response.status_code == 422
    doc = parse_html(response.text)
    assert_no_injected_markup(response.text, doc)
    field = url_field(doc)
    assert field is not None
    assert field_value(field) == url


# ---------------------------------------------------------------- AC-21


@pytest.mark.parametrize("code", ["Zz9Zz9Z", "nope"])
def test_ac21_not_found_page(client, parse_html, code):
    response = client.get(f"/{code}")
    assert response.status_code == 404
    assert is_html(response)
    doc = parse_html(response.text)
    assert "링크를 찾을 수 없습니다" in squash(doc.text())
    assert home_links(doc), "no link to home (/)"


# ---------------------------------------------------------------- AC-22


def _page(client, kind):
    if kind == "home":
        response = client.get("/")
        assert response.status_code == 200
    elif kind == "result":
        response = submit(client, "https://example.com/lang")
        assert response.status_code == 200
    elif kind == "input_error":
        response = submit(client, "ftp://example.com/lang")
        assert response.status_code == 422
    else:
        response = client.get("/Zz9Zz9Z")
        assert response.status_code == 404
    return response


@pytest.mark.parametrize("kind", ["home", "result", "input_error", "not_found"])
def test_ac22_page_has_lang_ko(client, parse_html, kind):
    doc = parse_html(_page(client, kind).text)
    html_elements = list(doc.iter("html"))
    assert html_elements, "no <html> element"
    assert html_elements[0].get("lang") == "ko"


@pytest.mark.parametrize("kind", ["home", "result", "input_error", "not_found"])
def test_ac22_page_has_viewport_meta(client, parse_html, kind):
    doc = parse_html(_page(client, kind).text)
    assert any(
        (meta.get("name") or "").lower() == "viewport" and (meta.get("content") or "")
        for meta in doc.iter("meta")
    )


# ---------------------------------------------------------------- AC-23


def test_ac23_form_created_code_redirects(client, parse_html):
    url = "https://example.com/from-form?x=1"
    response = submit(client, url)
    assert response.status_code == 200
    links = short_links(parse_html(response.text))
    assert links
    code = SHORT_URL_RE.fullmatch(links[0].get("href")).group(1)
    redirect = client.get(f"/{code}")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == url
