"""URL validation rules for link creation (see docs/plans/F1-plan.md section 3)."""

from __future__ import annotations

MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = frozenset({"http", "https"})


def validate_url(url: str) -> None:
    """Raise ``ValueError`` if ``url`` must be rejected; return ``None`` otherwise.

    Rejects: empty string, more than ``MAX_URL_LENGTH`` characters, any space or
    ASCII control character, a scheme other than http/https (case-insensitive),
    and a missing host. The URL is never modified.
    """
    raise NotImplementedError
