# EVAL-CANARY-F3-a35abd6a9f5f3b84
"""Shared helpers for the hidden F3 acceptance suite.

A uniquely named module (not `conftest`) so test files can import it even
when several eval suites run in one pytest session.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlsplit

from fastapi.testclient import TestClient

BASE_URL = "http://testserver"

# Two registered keys = two owners. Distinctive so a leak is easy to spot.
KEY_A = "f3k-Alpha-7d2e9c41b8a05f36e1d4"
KEY_B = "f3k-Bravo-0c6b3a59e27d148f9a3b"
REGISTERED_KEYS = (KEY_A, KEY_B)
# Not registered anywhere.
KEY_UNKNOWN = "f3k-Unknown-5e8f1a2b3c4d6e7f8091"

# High enough that ordinary tests are never throttled.
GENEROUS_RATE_LIMIT = 10_000

# Headers a browser sends with a same-origin form POST from the manage screen.
FORM_HEADERS = {"Origin": BASE_URL, "Referer": f"{BASE_URL}/manage"}

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}
HIDDEN_TEXT_TAGS = {"script", "style", "template"}


# --------------------------------------------------------------------------- HTML


class Node:
    """A minimal DOM node built from `html.parser` events."""

    def __init__(self, tag: str, attrs: dict[str, str | None], parent: Node | None):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[Node | str] = []

    def get(self, name: str) -> str | None:
        return self.attrs.get(name)

    def iter(self, tag: str | None = None) -> Iterator[Node]:
        """Yield descendant elements (not self), optionally filtered by tag."""
        for child in self.children:
            if isinstance(child, Node):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.iter(tag)

    def ancestors(self) -> Iterator[Node]:
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def strings(self) -> Iterator[str]:
        """Yield text pieces that would be rendered (skips script/style)."""
        for child in self.children:
            if isinstance(child, str):
                yield child
            elif child.tag not in HIDDEN_TEXT_TAGS:
                yield from child.strings()

    def text(self) -> str:
        return "".join(self.strings())

    def chunks(self) -> list[str]:
        """Non-empty, whitespace-collapsed text pieces."""
        result = []
        for piece in self.strings():
            collapsed = " ".join(piece.split())
            if collapsed:
                result.append(collapsed)
        return result


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_html(source: str) -> Node:
    builder = _TreeBuilder()
    builder.feed(source)
    builder.close()
    return builder.root


def squash(text: str) -> str:
    return " ".join(text.split())


def is_html(response) -> bool:
    return response.headers.get("content-type", "").lower().startswith("text/html")


def has_lang_ko(doc: Node) -> bool:
    html_elements = list(doc.iter("html"))
    return bool(html_elements) and html_elements[0].get("lang") == "ko"


def has_viewport_meta(doc: Node) -> bool:
    return any(
        (meta.get("name") or "").lower() == "viewport" and (meta.get("content") or "")
        for meta in doc.iter("meta")
    )


def is_labeled(doc: Node, field: Node) -> bool:
    return bool(field_labels(doc, field))


def field_labels(doc: Node, field: Node) -> list[str]:
    """Texts of every <label> attached to `field` (wrapping or for=id)."""
    labels = [squash(a.text()) for a in field.ancestors() if a.tag == "label"]
    field_id = field.get("id")
    if field_id:
        labels += [squash(lb.text()) for lb in doc.iter("label") if lb.get("for") == field_id]
    return labels


# ------------------------------------------------------------------------ client


class RecordingTestClient(TestClient):
    """TestClient that keeps every response it receives (for leak checks)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.responses: list = []

    def request(self, *args, **kwargs):
        response = super().request(*args, **kwargs)
        self.responses.append(response)
        return response


def assert_no_key_leak(*clients: RecordingTestClient, keys=REGISTERED_KEYS) -> None:
    """No registered key appears in any received response body or header."""
    checked = 0
    for client in clients:
        for response in client.responses:
            checked += 1
            body = response.content.decode("utf-8", errors="replace")
            where = f"{response.request.method} {response.request.url.path}"
            for key in keys:
                assert key not in body, f"API key in body of {where}"
                for name, value in response.headers.multi_items():
                    assert key not in name and key not in value, f"API key in header of {where}"
    assert checked, "no responses were recorded"


# ----------------------------------------------------------------- form helpers


def resolve_action(form: Node, page_path: str) -> str:
    """Absolute path (+query) a form posts to, resolved like a browser."""
    action = form.get("action") or ""
    absolute = urljoin(BASE_URL + page_path, action)
    parts = urlsplit(absolute)
    return parts.path + (f"?{parts.query}" if parts.query else "")


def action_path(form: Node, page_path: str) -> str:
    return urlsplit(resolve_action(form, page_path)).path


def form_of(doc: Node, control: Node) -> Node | None:
    """The form a control belongs to (form= attribute or nearest ancestor)."""
    form_id = control.get("form")
    if form_id:
        for form in doc.iter("form"):
            if form.get("id") == form_id:
                return form
    for ancestor in control.ancestors():
        if ancestor.tag == "form":
            return ancestor
    return None


def form_fields(form: Node, password: str | None = None) -> list[tuple[str, str]]:
    """Successful controls of a form, as a browser would submit them.

    Submit buttons are left out (the clicked one is added by the caller).
    Empty password inputs are filled with `password` when given.
    """
    fields: list[tuple[str, str]] = []
    for el in form.iter():
        name = el.get("name")
        if not name or "disabled" in el.attrs:
            continue
        if el.tag == "input":
            kind = (el.get("type") or "text").lower()
            if kind in ("submit", "button", "image", "reset", "file"):
                continue
            if kind in ("checkbox", "radio"):
                if "checked" in el.attrs:
                    fields.append((name, el.get("value") or "on"))
                continue
            value = el.get("value") or ""
            if kind == "password" and not value and password is not None:
                value = password
            fields.append((name, value))
        elif el.tag == "textarea":
            fields.append((name, el.text()))
        elif el.tag == "select":
            options = list(el.iter("option"))
            chosen = [o for o in options if "selected" in o.attrs] or options[:1]
            for option in chosen:
                value = option.get("value")
                fields.append((name, value if value is not None else squash(option.text())))
    return fields


def submit_buttons(root: Node) -> list[Node]:
    def is_submit(el: Node) -> bool:
        if el.tag == "button":
            return (el.get("type") or "submit").lower() == "submit"
        return el.tag == "input" and (el.get("type") or "").lower() in ("submit", "image")

    return [el for el in root.iter() if is_submit(el)]


def button_label(button: Node) -> str:
    if button.tag == "button":
        return squash(button.text())
    return squash(button.get("value") or "")


def post_form(client, path: str, fields: list[tuple[str, str]], max_redirects: int = 3):
    """POST urlencoded form fields like a browser, following 3xx with GET."""
    body = urlencode(fields)  # keeps duplicate names and their order
    headers = {**FORM_HEADERS, "Content-Type": "application/x-www-form-urlencoded"}
    response = client.post(path, content=body.encode("utf-8"), headers=headers)
    for _ in range(max_redirects):
        if response.status_code not in (301, 302, 303, 307, 308):
            break
        location = response.headers.get("location", "")
        parts = urlsplit(urljoin(BASE_URL + path, location))
        target = parts.path + (f"?{parts.query}" if parts.query else "")
        response = client.get(target, headers={"Referer": f"{BASE_URL}{path}"})
    return response


def manage_login_form(doc: Node) -> Node | None:
    """The POST form on the manage screen that holds the name=api_key field."""
    for form in doc.iter("form"):
        if (form.get("method") or "").lower() != "post":
            continue
        if any(el.get("name") == "api_key" for el in form.iter("input")):
            return form
    return None


def manage_login(client, key: str):
    """Open /manage, fill name=api_key with `key`, and submit the form."""
    page = client.get("/manage")
    assert page.status_code == 200, page.status_code
    form = manage_login_form(parse_html(page.text))
    assert form is not None, "no POST form with name=api_key on /manage"
    assert action_path(form, "/manage") == "/manage", "key form does not post to /manage"
    fields = [(n, v) for n, v in form_fields(form) if n != "api_key"]
    fields.append(("api_key", key))
    return post_form(client, resolve_action(form, "/manage"), fields)


def contains_short_url(node: Node, short_url: str) -> bool:
    if short_url in node.text():
        return True
    return any((a.get("href") or "") == short_url for a in node.iter("a"))


def delete_rows(doc: Node, short_urls: list[str]) -> dict[str, tuple[Node, Node]]:
    """Map short URL -> (row, "삭제" button) on a manage list page.

    A row is the nearest ancestor of a "삭제" submit button that shows one of
    `short_urls` (as text or link). Rows showing several of them are ignored.
    """
    rows: dict[str, tuple[Node, Node]] = {}
    for button in submit_buttons(doc):
        if "삭제" not in button_label(button):
            continue
        for ancestor in button.ancestors():
            shown = [u for u in short_urls if contains_short_url(ancestor, u)]
            if not shown:
                continue
            if len(shown) == 1:
                rows.setdefault(shown[0], (ancestor, button))
            break
    return rows


def delete_request(doc: Node, button: Node, password: str | None = None):
    """(path, fields) a browser would send when this "삭제" button is clicked."""
    form = form_of(doc, button)
    assert form is not None, "삭제 button is not inside a form"
    assert (form.get("method") or "").lower() == "post", "delete form is not method=post"
    path = resolve_action(form, "/manage")
    assert urlsplit(path).path == "/manage/delete", f"delete form posts to {path}"
    fields = form_fields(form, password=password)
    if button.get("name"):
        fields.append((button.get("name"), button.get("value") or ""))
    return path, fields


def utc_z(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
