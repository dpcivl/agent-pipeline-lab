"""validate_url: rule order, Korean messages, D-1 (uppercase scheme), D-2 (whitespace),
D-3 (length in characters), D-9 (unpaired surrogates)."""

from __future__ import annotations

import pytest

from shortlink import validation
from shortlink.validation import (
    MSG_EMPTY,
    MSG_INVALID_CHAR,
    MSG_INVALID_ENCODING,
    MSG_NO_HOST,
    MSG_NOT_STRING,
    MSG_SCHEME,
    MSG_TOO_LONG,
    InvalidURLError,
    validate_url,
)


def rejection(value: object) -> str:
    with pytest.raises(InvalidURLError) as info:
        validate_url(value)
    return info.value.message


def url_of_length(length: int) -> str:
    prefix = "https://example.com/"
    return prefix + "a" * (length - len(prefix))


def test_message_constants_match_the_plan():
    assert MSG_NOT_STRING == "url은 문자열이어야 합니다."
    assert MSG_EMPTY == "URL을 입력해 주세요."
    assert MSG_TOO_LONG == "URL은 2,048자 이하여야 합니다."
    assert MSG_INVALID_CHAR == "URL에 공백이나 제어 문자를 넣을 수 없습니다."
    assert MSG_INVALID_ENCODING == "URL에 올바르지 않은 문자가 있습니다."
    assert MSG_SCHEME == "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."
    assert MSG_NO_HOST == "URL에 호스트(도메인)가 없습니다. 예: https://example.com"


def test_max_length_constant_is_2048():
    assert validation.MAX_URL_LENGTH == 2048


def test_error_exposes_message_and_is_a_value_error():
    with pytest.raises(ValueError) as info:
        validate_url("")
    assert isinstance(info.value, InvalidURLError)
    assert info.value.message == str(info.value) == MSG_EMPTY


# --- 통과하는 입력 ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/path?q=1",
        "http://example.com",
        "http://localhost:8000/x",
        "http://127.0.0.1/",
        "https://user:pw@example.com/",
        "https://Example.COM/Mixed/Case?Key=Value#Frag",
        "https://example.com/경로",
        "https://example.com/😀",
        "https://example.com/a%20b",
        'https://example.com/<script>alert(1)</script>"',
    ],
)
def test_valid_url_is_returned_unchanged(url):
    assert validate_url(url) == url


@pytest.mark.parametrize(
    "url", ["HTTPS://example.com", "Http://example.com/A", "hTtP://example.com"]
)
def test_scheme_is_case_insensitive_and_value_is_kept(url):
    """D-1"""
    assert validate_url(url) == url


# --- 규칙 1: 문자열 아님 ---------------------------------------------------------------


@pytest.mark.parametrize("value", [123, 1.5, None, True, ["https://example.com"], {"a": 1}, b"x"])
def test_non_string_is_rejected(value):
    assert rejection(value) == MSG_NOT_STRING


# --- 규칙 2: 빈 문자열 -----------------------------------------------------------------


def test_empty_string_is_rejected():
    assert rejection("") == MSG_EMPTY


# --- 규칙 3: 길이 (D-3) ----------------------------------------------------------------


def test_2048_chars_is_valid():
    url = url_of_length(2048)
    assert len(url) == 2048
    assert validate_url(url) == url


def test_2049_chars_is_rejected():
    url = url_of_length(2049)
    assert len(url) == 2049
    assert rejection(url) == MSG_TOO_LONG


def test_length_counts_characters_not_bytes():
    """D-3: 한글 2,048자(6,144바이트)는 통과, 2,049자는 거절."""
    prefix = "https://example.com/"
    ok = prefix + "가" * (2048 - len(prefix))
    too_long = prefix + "가" * (2049 - len(prefix))
    assert validate_url(ok) == ok
    assert rejection(too_long) == MSG_TOO_LONG


# --- 규칙 4: 공백과 제어 문자 (D-2) ----------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        " https://example.com",
        "https://example.com ",
        "https://exa mple.com",
        "https://example.com/a b",
        "https://example.com/\n",
        "\nhttps://example.com",
        "https://example.com/\r\nX-Injected: 1",
        "https://example.com/\t",
        "https://example.com/\x00",
        "https://example.com/\x1f",
        "https://example.com/\x7f",
        "   ",
    ],
    ids=[
        "leading-space",
        "trailing-space",
        "space-in-host",
        "space-in-path",
        "trailing-newline",
        "leading-newline",
        "crlf",
        "tab",
        "nul",
        "unit-separator",
        "del",
        "only-spaces",
    ],
)
def test_whitespace_and_control_characters_are_rejected(url):
    assert rejection(url) == MSG_INVALID_CHAR


# --- 규칙 5: UTF-8로 인코딩할 수 없는 문자 (D-9) ---------------------------------------


HIGH = chr(0xD800)
LOW = chr(0xDC80)
LAST = chr(0xDFFF)


@pytest.mark.parametrize(
    "url",
    [
        f"https://e.com/{HIGH}",
        f"https://e.com/{LOW}",
        f"https://e.com/{LAST}",
        f"https://e.com/{HIGH}{HIGH}",
        f"https://e.com/a{chr(0xD83D)}z",
        f"{HIGH}https://e.com",
    ],
    ids=["high", "low", "last", "two-high", "middle", "leading"],
)
def test_unpaired_surrogate_is_rejected(url):
    assert rejection(url) == MSG_INVALID_ENCODING


# --- 규칙 6: 스킴 ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "javascript:alert(1)",
        "data:text/html,hi",
        "mailto:a@example.com",
        "example.com",
        "//example.com",
        "/path/only",
        "httpx://example.com",
        "ftp://",
        "<script>alert(1)</script>",
    ],
)
def test_other_schemes_and_missing_scheme_are_rejected(url):
    assert rejection(url) == MSG_SCHEME


# --- 규칙 7: 호스트 --------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    ["https://", "http://", "https://:80", "http:///path", "https://?q=1", "https:///"],
)
def test_missing_host_is_rejected(url):
    assert rejection(url) == MSG_NO_HOST


# --- 규칙 순서 (처음 걸린 규칙의 문구) -------------------------------------------------


def test_order_not_string_before_everything():
    assert rejection(None) == MSG_NOT_STRING


def test_order_empty_before_length_and_others():
    assert rejection("") == MSG_EMPTY


def test_order_length_before_invalid_char():
    assert rejection("ftp://" + " " * 2100) == MSG_TOO_LONG


def test_order_length_before_invalid_encoding():
    assert rejection(f"https://e.com/{HIGH}" + "a" * 2100) == MSG_TOO_LONG


def test_order_invalid_char_before_invalid_encoding():
    assert rejection(f"https://e.com/ {HIGH}") == MSG_INVALID_CHAR
    assert rejection(f"https://e.com/{HIGH}\n") == MSG_INVALID_CHAR


def test_order_invalid_encoding_before_scheme():
    assert rejection(f"ftp://e.com/{HIGH}") == MSG_INVALID_ENCODING


def test_order_invalid_encoding_before_host():
    assert rejection(f"https://{HIGH}") == MSG_INVALID_ENCODING


def test_order_invalid_char_before_scheme():
    assert rejection("ftp://exa mple.com") == MSG_INVALID_CHAR


def test_order_scheme_before_host():
    assert rejection("ftp://") == MSG_SCHEME


def test_order_length_before_scheme():
    assert rejection("ftp://example.com/" + "a" * 2100) == MSG_TOO_LONG
