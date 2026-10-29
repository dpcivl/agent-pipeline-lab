"""Security response headers (plan decision D-10)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
)


def add_security_headers(app: FastAPI) -> None:
    """Register a middleware that adds security headers to every response.

    - `X-Content-Type-Options: nosniff` on all responses.
    - `Content-Security-Policy` on our own HTML pages only. FastAPI's /docs and /redoc
      load scripts from a CDN and run inline scripts, so they are left without CSP.
    """
    # Paths looked up here, not hard-coded, so a changed docs_url is respected.
    docs_paths = {app.docs_url, app.redoc_url, app.swagger_ui_oauth2_redirect_url}

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        is_html = response.headers.get("content-type", "").startswith("text/html")
        if is_html and request.url.path not in docs_paths:
            response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        return response
