"""Web screens (AC-16 ~ AC-23). Wording follows docs/plans/mockups/F1-*.html."""

from __future__ import annotations

from html.parser import HTMLParser

import pytest

from shortlink.validation import MSG_EMPTY, MSG_INVALID_CHAR, MSG_SCHEME, MSG_TOO_LONG

VOID_TAGS = {"meta", "input", "link", "br", "img", "hr"}


class Page(HTMLParser):
    """Collects every element with its attributes and the text inside it."""

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[dict] = []
        self._open: list[dict] = []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        element = {"tag": tag, "attrs": dict(attrs), "text": ""}
        self.elements.append(element)
        if tag not in VOID_TAGS:
            self._open.append(element)

    def handle_endtag(self, tag):
        for index in range(len(self._open) - 1, -1, -1):
            if self._open[index]["tag"] == tag:
                del self._open[index:]
                break

    def handle_data(self, data):
        for element in self._open:
            element["text"] += data

    def find(self, tag: str, **attrs) -> list[dict]:
        return [
            e
            for e in self.elements
            if e["tag"] == tag and all(e["attrs"].get(k) == v for k, v in attrs.items())
        ]

    @staticmethod
    def text_of(element: dict) -> str:
        return " ".join(element["text"].split())

    @property
    def text(self) -> str:
        return " ".join(self.text_of(e) for e in self.find("body"))


def get_page(response) -> Page:
    return Page(response.text)


def submit(client, url):
    return client.post("/", data={"url": url})


def short_url_link(page: Page, settings) -> dict:
    links = [
        e
        for e in page.find("a")
        if (e["attrs"].get("href") or "").startswith(settings.base_url + "/")
    ]
    assert len(links) == 1, "결과 화면에는 단축 URL 링크가 하나 있어야 한다"
    return links[0]


def assert_html(response, status_code: int) -> None:
    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("text/html")


# --- AC-16 홈 화면 ---------------------------------------------------------------------


def test_home_page_has_form_with_labeled_url_input_and_submit_button(client):
    """AC-16"""
    response = client.get("/")

    assert_html(response, 200)
    page = get_page(response)

    forms = page.find("form")
    assert len(forms) == 1
    assert forms[0]["attrs"].get("method", "").lower() == "post"
    assert forms[0]["attrs"].get("action") == "/"

    inputs = page.find("input", name="url")
    assert len(inputs) == 1
    input_id = inputs[0]["attrs"].get("id")
    assert input_id
    assert page.find("label", **{"for": input_id}), "name=url 입력칸에 <label>이 붙어야 한다"

    buttons = [b for b in page.find("button") if b["attrs"].get("type", "submit") == "submit"]
    assert [page.text_of(b) for b in buttons] == ["줄이기"]


def test_home_page_shows_service_name_and_tagline(client):
    """AC-16 (목업: 서비스 이름, 한 줄 설명)"""
    page = get_page(client.get("/"))

    assert "ShortLink" in page.text
    assert "긴 URL을 짧고 공유하기 쉬운 링크로 바꿔 드립니다." in page.text
    assert not page.find("p", role="alert"), "처음 화면에는 오류 문구가 없어야 한다"


def test_home_input_does_not_block_server_validation(client):
    """D-7: 브라우저 검증이 서버 오류 화면을 가리지 않도록 type=text, required 없음."""
    page = get_page(client.get("/"))

    url_input = page.find("input", name="url")[0]
    assert url_input["attrs"].get("type") == "text"
    assert "required" not in url_input["attrs"]


# --- AC-17, 18 결과 화면 ---------------------------------------------------------------


def test_valid_form_shows_result_with_short_url_link_and_original_url(client, settings):
    """AC-17"""
    url = "https://example.com/path?q=1&r=2"

    response = submit(client, url)

    assert_html(response, 200)
    page = get_page(response)
    link = short_url_link(page, settings)
    code = link["attrs"]["href"].removeprefix(settings.base_url + "/")
    assert len(code) == 7 and code.isalnum()
    assert page.text_of(link) == link["attrs"]["href"]
    assert url in page.text


def test_result_page_has_copy_button_and_link_back_home(client, settings):
    """AC-18"""
    response = submit(client, "https://example.com/path")

    page = get_page(response)
    copy_buttons = [b for b in page.find("button") if page.text_of(b) == "복사"]
    assert len(copy_buttons) == 1
    assert copy_buttons[0]["attrs"].get("type") == "button"
    assert (
        copy_buttons[0]["attrs"].get("data-copy") == short_url_link(page, settings)["attrs"]["href"]
    )

    back_links = [a for a in page.find("a") if page.text_of(a) == "다른 URL 줄이기"]
    assert len(back_links) == 1
    assert back_links[0]["attrs"].get("href") == "/"


def test_result_page_keeps_short_url_link_without_javascript(client, settings):
    """설계서: JavaScript가 꺼져 있어도 단축 URL 링크는 보여야 한다(링크가 서버 HTML에 있다)."""
    page = get_page(submit(client, "https://example.com/nojs"))

    assert short_url_link(page, settings)["attrs"]["href"].startswith("http://testserver/")


# --- AC-19 입력 오류 화면 --------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("ftp://example.com/files/report.pdf", MSG_SCHEME),
        ("javascript:alert(1)", MSG_SCHEME),
        ("example.com", MSG_SCHEME),
        ("", MSG_EMPTY),
        ("https://example.com/" + "a" * 2029, MSG_TOO_LONG),
        ("https://example.com/with space", MSG_INVALID_CHAR),
    ],
    ids=["ftp", "javascript", "no-scheme", "empty", "too-long", "space"],
)
def test_invalid_form_shows_422_page_with_message_and_kept_value(
    client, count_links, value, message
):
    """AC-19 (같은 검증 규칙을 따른다)"""
    response = submit(client, value)

    assert_html(response, 422)
    page = get_page(response)
    assert message in page.text
    alerts = page.find("p", role="alert")
    assert alerts and message in page.text_of(alerts[0])

    url_input = page.find("input", name="url")[0]
    assert url_input["attrs"].get("value", "") == value
    assert page.find("form")[0]["attrs"].get("action") == "/"
    assert count_links() == 0


def test_invalid_form_page_matches_mockup_wording(client):
    """AC-19 (목업 F1-error.html)"""
    page = get_page(submit(client, "ftp://example.com/files/report.pdf"))

    assert "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다." in page.text
    assert page.find("input", name="url", value="ftp://example.com/files/report.pdf")
    assert [page.text_of(b) for b in page.find("button")] == ["줄이기"]


def test_form_without_url_field_is_treated_as_empty(client, count_links):
    """계획 3.4: url 필드가 없으면 빈 문자열로 보고 '입력해 주세요' 오류."""
    response = client.post("/", data={})

    assert_html(response, 422)
    assert MSG_EMPTY in get_page(response).text
    assert count_links() == 0


# --- AC-20 이스케이프 ------------------------------------------------------------------


def test_result_page_escapes_html_in_the_url(client):
    """AC-20 (결과 화면)"""
    url = "https://example.com/<script>alert(1)</script>"

    response = submit(client, url)

    assert_html(response, 200)
    assert "<script>alert(1)" not in response.text
    assert "&lt;script&gt;alert(1)" in response.text
    assert url in get_page(response).text  # 브라우저가 해석하면 원문으로 보인다


def test_error_page_escapes_html_in_the_submitted_value(client, count_links):
    """AC-20 (오류 화면)"""
    value = "<script>alert(1)</script>"

    response = submit(client, value)

    assert_html(response, 422)
    assert "<script>alert(1)" not in response.text
    assert "&lt;script&gt;alert(1)" in response.text
    page = get_page(response)
    assert page.find("input", name="url")[0]["attrs"]["value"] == value
    assert count_links() == 0


def test_error_page_value_cannot_break_out_of_the_attribute(client):
    """AC-20: 따옴표가 든 입력도 value 속성 안에 머문다."""
    value = '"onmouseover="alert(1)'

    page = get_page(submit(client, value))

    url_input = page.find("input", name="url")[0]
    assert url_input["attrs"]["value"] == value
    assert "onmouseover" not in url_input["attrs"]


# --- AC-21 찾을 수 없음 화면 -----------------------------------------------------------


def test_unknown_code_shows_404_page_with_notice_and_home_link(client):
    """AC-21"""
    response = client.get("/zzzzzzz", follow_redirects=False)

    assert_html(response, 404)
    page = get_page(response)
    assert "링크를 찾을 수 없습니다" in page.text
    assert "주소가 정확한지 확인해 주세요." in page.text
    home_links = [a for a in page.find("a") if page.text_of(a) == "홈으로 가기"]
    assert len(home_links) == 1
    assert home_links[0]["attrs"].get("href") == "/"


# --- AC-22 lang과 viewport -------------------------------------------------------------


def home_screen(client):
    return client.get("/")


def result_screen(client):
    return submit(client, "https://example.com/ok")


def error_screen(client):
    return submit(client, "ftp://example.com")


def not_found_screen(client):
    return client.get("/zzzzzzz", follow_redirects=False)


@pytest.mark.parametrize(
    ("screen", "status_code"),
    [
        (home_screen, 200),
        (result_screen, 200),
        (error_screen, 422),
        (not_found_screen, 404),
    ],
    ids=["home", "result", "error", "not-found"],
)
def test_every_screen_has_lang_ko_and_viewport_meta(client, screen, status_code):
    """AC-22"""
    response = screen(client)

    assert_html(response, status_code)
    page = get_page(response)
    html_elements = page.find("html")
    assert len(html_elements) == 1
    assert html_elements[0]["attrs"].get("lang") == "ko"
    viewports = page.find("meta", name="viewport")
    assert len(viewports) == 1
    assert "width=device-width" in viewports[0]["attrs"].get("content", "")


# --- AC-23 폼으로 만든 코드의 리다이렉트 ------------------------------------------------


@pytest.mark.parametrize(
    "url",
    ["https://example.com/path?q=1&r=2", "http://example.com", "https://example.com/경로"],
)
def test_code_created_by_form_redirects_to_the_original_url(client, settings, count_links, url):
    """AC-23"""
    page = get_page(submit(client, url))
    href = short_url_link(page, settings)["attrs"]["href"]
    code = href.removeprefix(settings.base_url + "/")
    assert count_links() == 1

    response = client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 302
    if url.isascii():
        assert response.headers["location"] == url
    else:
        assert response.headers["location"] == "https://example.com/%EA%B2%BD%EB%A1%9C"


# --- D-10 보안 헤더 --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("screen", "status_code"),
    [
        (home_screen, 200),
        (result_screen, 200),
        (error_screen, 422),
        (not_found_screen, 404),
    ],
    ids=["home", "result", "error", "not-found"],
)
def test_html_screens_have_csp_and_nosniff(client, screen, status_code):
    """D-10"""
    response = screen(client)

    assert_html(response, status_code)
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert response.headers["x-content-type-options"] == "nosniff"


def test_docs_page_has_no_csp_so_swagger_ui_can_load_its_cdn_assets(client):
    """D-10: /docs는 CDN 자원을 쓰므로 CSP를 붙이지 않는다."""
    response = client.get("/docs")

    assert response.status_code == 200
    assert "content-security-policy" not in response.headers


def test_copy_script_guards_missing_clipboard_api(client):
    """D-11: navigator.clipboard가 없을 때를 처리한다(문자열 확인 수준)."""
    response = client.get("/static/copy.js")

    assert response.status_code == 200
    assert "navigator.clipboard" in response.text
