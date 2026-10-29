"""Request-scoped accessors for objects that create_app() puts on app.state."""

from __future__ import annotations

from fastapi import Request

from shortlink.config import Settings
from shortlink.repository import LinkRepository


def get_settings(request: Request) -> Settings:
    """Return `request.app.state.settings`."""
    return request.app.state.settings


def get_repository(request: Request) -> LinkRepository:
    """Return `request.app.state.repository`."""
    return request.app.state.repository
