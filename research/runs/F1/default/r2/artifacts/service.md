# ShortLink 서비스 사용법

ShortLink는 긴 URL을 짧은 코드로 바꿔 저장하고, 짧은 URL로 접속하면 원래 URL로 보내 주는 URL 단축 서비스입니다. 웹 화면에서 직접 URL을 줄이거나, JSON API(`POST /links`)로 다른 프로그램에서 같은 기능을 쓸 수 있습니다.

현재 제공 기능은 F1(단축 URL 생성과 리다이렉트)입니다. 클릭 통계와 별칭(F2), 인증·만료·삭제(F3)는 아직 없습니다.

## 실행 방법

의존성은 `uv`로 관리합니다. 저장소 루트에서 다음 명령으로 서버를 띄웁니다.

```sh
uv sync
uv run uvicorn shortlink.main:create_app --factory
```

기본 주소는 `http://localhost:8000`입니다. 처음 실행하면 `SHORTLINK_DB_PATH`가 가리키는 SQLite 파일과 `links` 테이블이 자동으로 만들어집니다.

테스트는 `uv run pytest`로 실행합니다.

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `SHORTLINK_DB_PATH` | `shortlink.db` | 링크를 저장할 SQLite 파일 경로. 같은 경로로 앱을 다시 띄우면 이전에 만든 코드가 그대로 동작합니다. |
| `SHORTLINK_BASE_URL` | `http://localhost:8000` | 응답의 `short_url`을 만들 때 쓰는 기본 주소. 끝의 `/`는 자동으로 제거됩니다. |

빈 값으로 설정한 변수는 설정하지 않은 것과 같이 기본값을 씁니다.

```sh
SHORTLINK_DB_PATH=/var/lib/shortlink/links.db SHORTLINK_BASE_URL=https://sl.example.com \
  uv run uvicorn shortlink.main:create_app --factory
```

## 화면 목록과 사용 흐름

화면은 한국어로 되어 있고 서버에서 HTML을 만들어 보냅니다. 모든 화면은 `<html lang="ko">`와 viewport 설정을 갖고 있어 모바일 폭(375px)에서도 쓸 수 있습니다.

| 화면 | 경로 | 설명 |
|---|---|---|
| 홈 | `GET /` | 서비스 이름, 한 줄 설명, URL 입력 폼을 보여 줍니다. |
| 결과 | `POST /` (성공) | 만든 단축 URL 링크, 원래 URL, "복사" 버튼, "다른 URL 줄이기" 링크를 보여 줍니다. |
| 입력 오류 | `POST /` (실패) | 홈 화면에 오류 메시지를 표시하고, 입력했던 값을 입력칸에 남겨 둡니다. 아무것도 저장하지 않습니다. |
| 찾을 수 없음 | `GET /{code}` (없는 코드) | "링크를 찾을 수 없습니다" 안내와 홈으로 가는 링크를 보여 줍니다. |

### 사용 흐름

1. `/`에 접속합니다.
2. "줄일 URL" 입력칸에 `http://` 또는 `https://`로 시작하는 주소를 넣고 **줄이기**를 누릅니다.
3. 검증을 통과하면 결과 화면이 나옵니다. 단축 URL 링크를 누르거나 **복사** 버튼으로 클립보드에 복사할 수 있습니다. 복사 기능은 브라우저 JavaScript를 쓰며, JavaScript가 꺼져 있어도 링크는 그대로 보입니다.
4. 검증에 걸리면 홈 화면에 빨간 오류 메시지가 나오고 입력한 값이 남습니다. 값을 고쳐서 다시 제출합니다.
5. 단축 URL(`/{code}`)로 접속하면 원래 URL로 `302` 리다이렉트됩니다. 없는 코드이면 "찾을 수 없음" 화면이 나옵니다.

단축 코드는 대소문자를 구분합니다.

## URL 검증 규칙

웹 폼과 API는 같은 규칙으로 URL을 검사합니다. 아래 조건 중 하나라도 해당하면 거절하고 아무것도 저장하지 않습니다. 검사는 위에서부터 순서대로 하며 처음 걸린 조건의 메시지를 보여 줍니다.

| 순서 | 조건 | 웹 화면 메시지 | API `msg` (접두사 `Value error, ` 제외) |
|---|---|---|---|
| 1 | 문자열이 아님 (API만 해당) | - | `Input should be a valid string` (FastAPI 기본 문구) |
| 2 | 빈 문자열, 또는 폼에서 `url` 필드가 없음 | URL을 입력해 주세요. | URL을 입력해 주세요. |
| 3 | 2,048자를 넘음 (글자 수 기준) | URL은 2,048자 이하여야 합니다. | URL은 2,048자 이하여야 합니다. |
| 4 | 공백이나 제어 문자가 있음 (아래 설명) | URL에 공백이나 제어 문자를 넣을 수 없습니다. | URL에 공백이나 제어 문자를 넣을 수 없습니다. |
| 5 | 스킴이 `http`도 `https`도 아님 | http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다. | http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다. |
| 6 | 호스트(도메인)가 없음 (예: `https://`) | URL에 호스트(도메인)가 없습니다. | URL에 호스트(도메인)가 없습니다. |

규칙의 세부 사항은 다음과 같습니다.

- **공백과 제어 문자 (D-3, D-10)**: 스페이스, 탭, 줄바꿈 같은 공백 문자와 ASCII·C1 제어 문자(0x00~0x1F, 0x7F~0x9F)가 한 글자라도 들어 있으면 거절합니다. 앞뒤 공백을 잘라내지 않고 그대로 거절합니다. 예를 들어 `"https://example.com "`(끝 공백)은 거절됩니다.
- **스킴 (D-4)**: `http`와 `https`는 대소문자를 구분하지 않습니다. `HTTPS://example.com`은 허용되며, 저장과 응답에는 입력한 그대로 남습니다.
- **정규화 없음**: 앞뒤 공백 제거, 대소문자 변경, 후행 슬래시 추가 같은 정규화는 하지 않습니다. 같은 URL을 여러 번 줄이면 매번 새 코드를 받습니다.
- **비ASCII 문자 (D-7)**: 한글 등 비ASCII 문자가 든 URL은 허용됩니다. 저장과 API 응답의 `url`은 입력한 그대로이고, 리다이렉트 `Location` 헤더는 HTTP 헤더에 맞게 퍼센트 인코딩됩니다. `<`, `>`, `"`, `{`, `}`, `|`, `\`, `^`, 백틱처럼 URI에 그대로 쓸 수 없는 ASCII 문자도 같은 방식으로 인코딩됩니다. `Location` 값을 퍼센트 디코딩하면 원래 URL과 같습니다.

## API

### `POST /links` — 단축 URL 만들기

요청 본문은 JSON이고 `url` 필드 하나를 가집니다.

```http
POST /links HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{"url": "https://example.com/path?q=1"}
```

성공하면 `201 Created`와 다음 본문을 돌려줍니다.

```json
{
  "code": "6041Iq3",
  "short_url": "http://localhost:8000/6041Iq3",
  "url": "https://example.com/path?q=1",
  "created_at": "2026-10-29T02:25:41Z"
}
```

| 필드 | 설명 |
|---|---|
| `code` | 단축 코드. 영문 대소문자와 숫자로 된 7자이며 예측할 수 없도록 무작위로 만듭니다. |
| `short_url` | `SHORTLINK_BASE_URL`과 `code`를 `/`로 이은 주소입니다. |
| `url` | 요청한 원래 URL을 글자 그대로 돌려줍니다. |
| `created_at` | 생성 시각. UTC, 초 단위, `Z` 접미사의 ISO 8601 형식입니다. |

**422 Unprocessable Entity**: 검증에 걸리면 FastAPI 표준 형식(`detail` 배열)으로 응답하고 저장하지 않습니다.

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "url"],
      "msg": "Value error, http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.",
      "input": "ftp://example.com",
      "ctx": {"error": {}}
    }
  ]
}
```

- `url` 필드가 없으면 `type`이 `missing`이고 `msg`는 `Field required`입니다.
- `url`이 문자열이 아니면(`null`, 숫자 등 포함) `type`이 `string_type`이고 `msg`는 `Input should be a valid string`입니다.
- 나머지 조건(빈 문자열, 길이, 공백·제어 문자, 스킴, 호스트)은 `type`이 `value_error`이고 `msg`에 위 검증 표의 한국어 문구가 `Value error, ` 접두사와 함께 들어갑니다.
- `input`에는 보낸 값이 그대로 들어갑니다.

curl 예시:

```sh
curl -i -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/path?q=1"}'
```

### `GET /{code}` — 원래 URL로 이동

| 상황 | 응답 |
|---|---|
| 저장된 코드 | `302 Found`, `Location: <원래 URL>` (비ASCII 문자는 퍼센트 인코딩) |
| 없는 코드, 또는 7자 영숫자가 아닌 경로 (예: `/favicon.ico`) | `404 Not Found`, "링크를 찾을 수 없습니다" HTML 화면 |

```sh
curl -i http://localhost:8000/6041Iq3
# HTTP/1.1 302 Found
# location: https://example.com/path?q=1
```

`GET /{code}`의 404는 항상 HTML 화면으로 응답합니다(JSON이 아닙니다).

### 웹 폼 — `POST /`

폼 `<form method="post" action="/">`의 입력칸 `name="url"`로 제출합니다. 검증 규칙은 API와 같습니다.

- 성공: `200 OK`, 결과 HTML 화면.
- 실패: `422`, 오류 메시지와 입력값이 들어간 홈 HTML 화면. 이때 메시지는 `detail` 형식이 아니라 화면 문구(접두사 없음)입니다.

화면에서 만든 링크도 API로 만든 링크와 같은 저장소에 저장되므로 `GET /{code}`로 똑같이 리다이렉트됩니다.

## 저장

- 링크는 `SHORTLINK_DB_PATH`의 SQLite 파일 `links` 테이블(`code`, `url`, `created_at`)에 저장합니다.
- 같은 URL을 여러 번 줄이면 중복을 합치지 않고 행을 여러 개 만듭니다.
- 저장된 링크를 조회하거나 지우는 기능은 아직 없습니다(F3 범위).
