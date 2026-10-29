"""Application entry point.

FIXED CONTRACT (see docs/00-pipeline-design.md section 7.2):
- Keep the name and signature of `create_app()`.
- `create_app()` must return a ready-to-serve app: routers registered and the
  database schema prepared at `settings.db_path`.
- Web pages use Jinja2 templates in `src/shortlink/templates/`. Static files
  (CSS, images, scripts) live in `src/shortlink/static/` and are served at `/static`.
- Run locally with: uv run uvicorn shortlink.main:create_app --factory
Agents implement everything behind this contract.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from shortlink import api, web
from shortlink.config import Settings
from shortlink.db import init_schema
from shortlink.repository import LinkRepository
from shortlink.security import add_security_headers

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="ShortLink")
    app.state.settings = settings
    add_security_headers(app)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    # Feature code registers routers and prepares the database schema here.
    init_schema(settings.db_path)
    app.state.repository = LinkRepository(settings.db_path)
    app.include_router(api.router)
    # web.router has the catch-all GET /{code}, so it goes last.
    app.include_router(web.router)
    return app
