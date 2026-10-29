"""Web pages (Jinja2) and the redirect endpoint.

Templates (src/shortlink/templates/), following docs/plans/mockups/F1-*.html:
- base.html       shared layout: <html lang="ko">, viewport meta, /static/style.css, header
- home.html       home and input-error page (form, optional error, kept input value)
- result.html     result page (short URL link, copy button, original URL, link home)
- not_found.html  404 page
Static: src/shortlink/static/style.css, src/shortlink/static/copy.js
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from shortlink.codes import build_short_url
from shortlink.config import Settings
from shortlink.dependencies import get_repository, get_settings
from shortlink.repository import LinkRepository
from shortlink.validation import InvalidURLError, validate_url

# Same directory as shortlink.main.TEMPLATES_DIR (not imported to avoid a circular import).
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def location_header_value(url: str) -> str:
    """Return `url` for the Location header.

    ASCII characters are kept byte-for-byte (validate_url already rejected whitespace and
    control characters). Only non-ASCII characters are percent-encoded as UTF-8, because
    HTTP header values must be latin-1.
    """
    return "".join(char if char.isascii() else quote(char, safe="") for char in url)


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    """200 home page with an empty form."""
    return templates.TemplateResponse(request, "home.html", {"error": None, "url_value": ""})


@router.post("/", response_class=HTMLResponse)
def shorten_form(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[LinkRepository, Depends(get_repository)],
    url: Annotated[str, Form()] = "",
) -> HTMLResponse:
    """Handle the form field `url` (missing field counts as empty string).

    Valid: store via the repository and render result.html with 200.
    Invalid: render home.html with 422, the error message, and the submitted value kept
    in the input. Nothing is stored.
    """
    try:
        valid_url = validate_url(url)
    except InvalidURLError as error:
        return templates.TemplateResponse(
            request,
            "home.html",
            {"error": error.message, "url_value": url},
            status_code=422,
        )
    link = repository.create(valid_url)
    return templates.TemplateResponse(
        request,
        "result.html",
        {"short_url": build_short_url(settings.base_url, link.code), "url": link.url},
    )


@router.get("/{code}")
def follow_link(
    request: Request,
    code: str,
    repository: Annotated[LinkRepository, Depends(get_repository)],
) -> Response:
    """302 with Location: location_header_value(url) if the code exists, else 404 not_found.html."""
    link = repository.get(code)
    if link is None:
        return templates.TemplateResponse(request, "not_found.html", {}, status_code=404)
    # Not RedirectResponse: it re-quotes some ASCII characters (<, >, ") in the URL.
    return Response(status_code=302, headers={"Location": location_header_value(link.url)})
