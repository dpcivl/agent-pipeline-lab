"""Short code generation."""

from __future__ import annotations

import string

CODE_LENGTH = 7
CODE_ALPHABET = string.ascii_letters + string.digits


def generate_code() -> str:
    """Return a hard-to-predict random code of ``CODE_LENGTH`` alphanumeric characters.

    Uses the ``secrets`` module, not ``random``.
    """
    raise NotImplementedError
