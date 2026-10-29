"""Shared test fixtures.

FIXED CONTRACT (see docs/00-pipeline-design.md section 7.2):
- Keep the fixtures `settings`, `app`, and `client` with their current meaning.
- Adding new fixtures is allowed.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shortlink.config import Settings
from shortlink.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Settings pointing at a fresh temporary database for each test."""
    return Settings(db_path=str(tmp_path / "test.db"), base_url="http://testserver")


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
