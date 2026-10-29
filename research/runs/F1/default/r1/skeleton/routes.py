"""HTTP endpoints: POST /links and GET /{code}."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, StrictStr, field_validator

router = APIRouter()


class CreateLinkRequest(BaseModel):
    url: StrictStr

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        """Apply ``validation.validate_url``; its ``ValueError`` becomes a 422."""
        raise NotImplementedError


class LinkResponse(BaseModel):
    code: str
    short_url: str
    url: str
    created_at: str


@router.post("/links", status_code=201, response_model=LinkResponse)
def create_link(body: CreateLinkRequest, request: Request) -> LinkResponse:
    """Create a short link for ``body.url`` and return it with ``201``."""
    raise NotImplementedError


@router.get("/{code}")
def follow_link(code: str, request: Request) -> Response:
    """Redirect with ``302`` to the stored URL, or answer ``404`` if unknown."""
    raise NotImplementedError
