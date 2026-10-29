"""URL validation rules shared by the JSON API and the web form."""

from __future__ import annotations

from urllib.parse import urlsplit

MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = frozenset({"http", "https"})

# User-facing messages (Korean). The web form shows them as-is; the API returns them
# in the 422 body as {"detail": <message>}.
MSG_EMPTY = "URL을 입력해 주세요."
MSG_NOT_STRING = "url은 문자열이어야 합니다."
MSG_SCHEME = "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."
MSG_NO_HOST = "URL에 호스트(도메인)가 없습니다. 예: https://example.com"
MSG_TOO_LONG = "URL은 2,048자 이하여야 합니다."
MSG_INVALID_CHAR = "URL에 공백이나 제어 문자를 넣을 수 없습니다."
MSG_INVALID_ENCODING = "URL에 올바르지 않은 문자가 있습니다."


class InvalidURLError(ValueError):
    """Raised when a URL breaks a validation rule.

    `message` is the Korean, user-facing explanation (one of the MSG_* constants).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def validate_url(url: object) -> str:
    """Check `url` against the F1 rules and return it unchanged.

    Rules, checked in this order (first failure wins):
    1. not a str -> MSG_NOT_STRING
    2. empty string -> MSG_EMPTY
    3. longer than MAX_URL_LENGTH characters -> MSG_TOO_LONG
    4. contains whitespace or an ASCII control character (<= 0x20 or 0x7F) -> MSG_INVALID_CHAR
    5. cannot be encoded as UTF-8 (e.g. an unpaired surrogate such as "\\ud800")
       -> MSG_INVALID_ENCODING
    6. scheme (case-insensitive) not in ALLOWED_SCHEMES -> MSG_SCHEME
    7. no host (e.g. "https://", "https://:80") -> MSG_NO_HOST

    No normalization: the returned value is exactly the input.
    Raises InvalidURLError.
    """
    if not isinstance(url, str):
        raise InvalidURLError(MSG_NOT_STRING)
    if url == "":
        raise InvalidURLError(MSG_EMPTY)
    if len(url) > MAX_URL_LENGTH:
        raise InvalidURLError(MSG_TOO_LONG)
    if any(ord(char) <= 0x20 or ord(char) == 0x7F for char in url):
        raise InvalidURLError(MSG_INVALID_CHAR)
    try:
        url.encode("utf-8")
    except UnicodeEncodeError:
        raise InvalidURLError(MSG_INVALID_ENCODING) from None
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
    except ValueError:
        # urlsplit rejects some malformed hosts, e.g. "https://[" (bad IPv6 literal).
        # Keep the rule order: a wrong scheme is reported before a bad host.
        scheme, separator, _ = url.partition(":")
        if not separator or scheme.lower() not in ALLOWED_SCHEMES:
            raise InvalidURLError(MSG_SCHEME) from None
        raise InvalidURLError(MSG_NO_HOST) from None
    if parts.scheme not in ALLOWED_SCHEMES:
        raise InvalidURLError(MSG_SCHEME)
    if not hostname:
        raise InvalidURLError(MSG_NO_HOST)
    return url
