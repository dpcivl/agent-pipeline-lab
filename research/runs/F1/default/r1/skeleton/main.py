"""Application entry point.

FIXED CONTRACT (see docs/00-pipeline-design.md section 7.2):
- Keep the name and signature of `create_app()`.
- `create_app()` must return a ready-to-serve app: routers registered and the
  database schema prepared at `settings.db_path`.
- Run locally with: uv run uvicorn shortlink.main:create_app --factory
Agents implement everything behind this contract.
"""

from __future__ import annotations

from fastapi import FastAPI

from shortlink.config import Settings
from shortlink.db import init_schema
from shortlink.routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    init_schema(settings.db_path)
    app = FastAPI(title="ShortLink")
    app.state.settings = settings
    app.include_router(router)
    return app
