"""JSON API: POST /links."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StrictStr

from shortlink.codes import build_short_url
from shortlink.config import Settings
from shortlink.dependencies import get_repository, get_settings
from shortlink.repository import LinkRepository, format_timestamp
from shortlink.validation import InvalidURLError, validate_url

router = APIRouter()


class LinkIn(BaseModel):
    # StrictStr: numbers, null and arrays are rejected instead of being coerced to str.
    url: StrictStr


class LinkOut(BaseModel):
    code: str
    short_url: str
    url: str
    created_at: str  # format_timestamp() output


@router.post("/links", status_code=201, response_model=LinkOut)
def create_link(
    body: LinkIn,
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[LinkRepository, Depends(get_repository)],
) -> LinkOut:
    """Create a short link from a JSON body {"url": "<original URL>"}.

    201 with LinkOut on success. 422 when `url` is missing, not a string, or fails
    validate_url(); custom validation errors use the body {"detail": "<Korean message>"}.
    A malformed or non-object JSON body also gets 422. Nothing is stored on 422.
    (Parameters are left to the implementation: request body, settings, repository.)
    """
    try:
        url = validate_url(body.url)
    except InvalidURLError as error:
        raise HTTPException(status_code=422, detail=error.message) from None
    link = repository.create(url)
    return LinkOut(
        code=link.code,
        short_url=build_short_url(settings.base_url, link.code),
        url=link.url,
        created_at=format_timestamp(link.created_at),
    )
