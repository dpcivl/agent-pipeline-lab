"""Short code generation."""

from __future__ import annotations

import secrets
import string

CODE_LENGTH = 7
CODE_ALPHABET = string.ascii_letters + string.digits


def generate_code() -> str:
    """Return a new random code of CODE_LENGTH characters from CODE_ALPHABET.

    Uses the `secrets` module so codes are hard to predict.
    """
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def build_short_url(base_url: str, code: str) -> str:
    """Return "<base_url>/<code>". `base_url` is already stored without a trailing slash."""
    return f"{base_url}/{code}"
