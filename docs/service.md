# ShortLink 서비스 사용법

ShortLink는 긴 URL을 짧은 코드로 바꿔 저장하고, 짧은 URL로 접속하면 원래 URL로 보내 주는 서비스입니다. 웹 화면과 JSON API를 함께 제공합니다.

이 문서는 현재 구현된 기능(F1: 단축 URL 생성과 리다이렉트)을 설명합니다. 기능별 요구사항은 `docs/features/`, 구현 계획은 `docs/plans/`를 봅니다.

## 1. 서버 실행

저장소 루트에서 실행합니다.

```bash
uv run uvicorn shortlink.main:create_app --factory
```

기본 주소는 `http://localhost:8000`이고, 기본 DB 파일은 저장소 루트의 `shortlink.db`입니다. 테스트는 다음 명령으로 실행합니다.

```bash
uv run pytest
```

## 2. 환경 변수

| 변수 | 기본값 | 내용 |
|---|---|---|
| `SHORTLINK_DB_PATH` | `shortlink.db` | SQLite DB 파일 경로. 같은 파일을 가리키면 서버를 다시 띄워도 이전 링크가 유지됩니다. |
| `SHORTLINK_BASE_URL` | `http://localhost:8000` | 응답의 `short_url`을 만들 때 쓰는 주소. 끝의 `/`는 자동으로 뗍니다. |

빈 값으로 설정하면 기본값을 씁니다.

```bash
SHORTLINK_DB_PATH=/var/data/shortlink.db SHORTLINK_BASE_URL=https://sl.example.com uv run uvicorn shortlink.main:create_app --factory
```

Windows PowerShell에서는 `$env:SHORTLINK_DB_PATH = "..."`처럼 설정합니다.

## 3. 웹 화면

화면은 한국어로 표시되며, 서버가 HTML을 만들어 보냅니다. 모든 화면은 `<html lang="ko">`와 viewport 설정을 갖고 있어 폭 375px 휴대폰 화면에서도 쓸 수 있습니다.

| 화면 | 경로 | 상태 | 내용 |
|---|---|---|---|
| 홈 | `GET /` | 200 | 서비스 이름, 한 줄 설명, URL 입력 폼("줄이기" 버튼) |
| 결과 | `POST /` 성공 | 200 | 단축 URL 링크, "복사" 버튼, 원래 URL, "다른 URL 줄이기" 링크 |
| 입력 오류 | `POST /` 실패 | 422 | 홈 화면에 오류 문구를 표시하고, 입력했던 값을 입력칸에 남김 |
| 찾을 수 없음 | 없는 코드로 `GET /{code}` | 404 | "링크를 찾을 수 없습니다" 안내와 "홈으로 가기" 링크 |

### 사용 흐름

1. `http://localhost:8000/`에 접속합니다.
2. 입력칸에 줄일 URL을 넣고 "줄이기"를 누릅니다. 예: `https://example.com/path?q=1`
3. 결과 화면에서 단축 URL(예: `http://localhost:8000/aB3dE9f`)을 확인합니다.
4. "복사"를 누르면 클립보드에 복사하고 "복사했습니다."가 표시됩니다. 복사를 할 수 없는 환경이면 "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."가 표시됩니다. JavaScript가 꺼져 있어도 단축 URL 링크는 그대로 보입니다.
5. 단축 URL에 접속하면 원래 URL로 이동합니다.
6. 잘못된 URL을 제출하면 입력 오류 화면이 뜹니다. 오류 문구는 아래 4절의 목록을 봅니다.
7. 없는 코드로 접속하면 "링크를 찾을 수 없습니다" 화면이 뜹니다.

사용자 입력은 HTML에 그대로 넣지 않고 이스케이프해서 표시합니다.

## 4. 입력 규칙과 오류 문구

URL은 받은 그대로 저장하고 돌려줍니다. 앞뒤 공백 제거나 대소문자 변경 같은 정규화는 하지 않습니다. 다음 중 하나라도 해당하면 `422`로 거절하며 아무것도 저장하지 않습니다.

- 값이 없거나 빈 문자열
- 문자열이 아님 (숫자, `null`, 배열 등)
- 2,048자를 넘음 (문자 수 기준)
- 공백이나 ASCII 제어 문자(줄바꿈, 탭 등)가 있음
- UTF-8로 인코딩할 수 없는 문자가 있음 (짝 없는 서로게이트, 예: JSON의 `\ud800`)
- 스킴이 `http` 또는 `https`가 아님 (대소문자 무시: `HTTPS://`는 허용). 예: `ftp:`, `javascript:`, `data:`, `mailto:`
- 호스트(도메인)가 없음 (예: `https://`)

검증 실패 시 화면과 API가 같은 문구를 씁니다. 검사 순서는 위 목록 순서이고, 처음 걸린 규칙의 문구가 나옵니다.

| 상수 | 문구 |
|---|---|
| `MSG_NOT_STRING` | url은 문자열이어야 합니다. |
| `MSG_EMPTY` | URL을 입력해 주세요. |
| `MSG_TOO_LONG` | URL은 2,048자 이하여야 합니다. |
| `MSG_INVALID_CHAR` | URL에 공백이나 제어 문자를 넣을 수 없습니다. |
| `MSG_INVALID_ENCODING` | URL에 올바르지 않은 문자가 있습니다. |
| `MSG_SCHEME` | http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다. |
| `MSG_NO_HOST` | URL에 호스트(도메인)가 없습니다. 예: https://example.com |

위 상수는 `src/shortlink/validation.py`에 정의되어 있습니다.

## 5. JSON API

### 5.1 단축 URL 생성: `POST /links`

요청 본문은 JSON 객체이고 `url` 필드가 필요합니다.

```bash
curl -s -i -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/path?q=1"}' \
  http://localhost:8000/links
```

성공 응답 (`201 Created`):

```http
HTTP/1.1 201 Created
content-type: application/json

{
  "code": "aB3dE9f",
  "short_url": "http://localhost:8000/aB3dE9f",
  "url": "https://example.com/path?q=1",
  "created_at": "2026-10-29T01:23:45Z"
}
```

| 필드 | 내용 |
|---|---|
| `code` | 영문 대소문자와 숫자로 된 7자 무작위 코드 |
| `short_url` | `<SHORTLINK_BASE_URL>/<code>` |
| `url` | 요청한 URL 그대로 |
| `created_at` | 생성 시각. UTC, ISO 8601, 초 단위, `Z` 접미사 |

같은 URL을 여러 번 보내면 요청마다 다른 `code`가 나옵니다. 중복을 합치지 않습니다.

검증에 실패하면 `422`와 함께 한국어 문구를 담습니다.

```bash
curl -s -i -X POST -H "Content-Type: application/json" \
  -d '{"url": "ftp://example.com/files/report.pdf"}' \
  http://localhost:8000/links
```

```http
HTTP/1.1 422 Unprocessable Entity
content-type: application/json

{"detail": "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."}
```

`url` 필드가 없거나, 본문이 JSON 객체가 아니거나, JSON 형식이 잘못된 경우에는 FastAPI 기본 422 본문(`detail`이 배열)이 옵니다. 어떤 경우든 저장하지 않습니다.

### 5.2 리다이렉트: `GET /{code}`

```bash
curl -s -i http://localhost:8000/aB3dE9f
```

코드가 있으면 `302 Found`와 `Location` 헤더를 돌려줍니다.

```http
HTTP/1.1 302 Found
location: https://example.com/path?q=1
```

ASCII 문자는 원문 그대로 보내고, 한글 등 비ASCII 문자만 UTF-8 퍼센트 인코딩합니다.

코드가 없으면 `404 Not Found`와 "링크를 찾을 수 없습니다" HTML 화면을 돌려줍니다. API 클라이언트도 같은 HTML을 받습니다.

### 5.3 자동 문서

서버를 띄운 뒤 `http://localhost:8000/docs`(Swagger UI)와 `http://localhost:8000/redoc`에서 API를 볼 수 있습니다.

## 6. 보안 헤더

- 모든 응답에 `X-Content-Type-Options: nosniff`를 붙입니다.
- 웹 화면(HTML)에는 다음 `Content-Security-Policy`를 붙입니다.

  ```
  default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'
  ```

  화면은 같은 서버의 CSS(`/static/style.css`)와 스크립트(`/static/copy.js`)만 읽습니다.
- `/docs`와 `/redoc`은 외부 CDN 자원을 쓰므로 CSP를 붙이지 않습니다.

## 7. 저장

- 링크는 `SHORTLINK_DB_PATH`의 SQLite 파일 `links` 테이블에 저장합니다.
- 테이블 구조: `code TEXT PRIMARY KEY`, `url TEXT NOT NULL`, `created_at TEXT NOT NULL`.
- 서버를 재시작하거나 같은 DB 경로로 앱을 다시 만들어도 이전 코드로 리다이렉트됩니다.
- 현재 링크를 지우거나 목록으로 보는 기능은 없습니다(F3 이후 범위).

## 8. 아직 없는 기능

다음 기능은 아직 구현되어 있지 않습니다.

- 커스텀 별칭, 클릭 통계 (F2 예정)
- 인증, 만료, 삭제, 요청 수 제한 (F3 예정)
- URL 정규화, 중복 URL 합치기, 생성한 링크 목록 조회
