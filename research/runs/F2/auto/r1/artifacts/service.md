# ShortLink 서비스 사용법

ShortLink는 긴 URL을 짧은 코드로 바꿔 저장하고, 짧은 URL로 접속하면 원래 URL로 보내 주는 서비스입니다. 원하는 별칭으로 코드를 정할 수 있고, 클릭 수와 마지막 접근 시각을 확인할 수 있습니다. 웹 화면과 JSON API를 함께 제공합니다.

이 문서는 현재 구현된 기능(F1: 단축 URL 생성과 리다이렉트, F2: 커스텀 별칭과 클릭 통계)을 설명합니다. 기능별 요구사항은 `docs/features/`, 구현 계획은 `docs/plans/`를 봅니다.

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
| `SHORTLINK_DB_PATH` | `shortlink.db` | SQLite DB 파일 경로. 같은 파일을 가리키면 서버를 다시 띄워도 이전 링크와 클릭 수가 유지됩니다. |
| `SHORTLINK_BASE_URL` | `http://localhost:8000` | 응답의 `short_url`과 화면의 단축 URL을 만들 때 쓰는 주소. 끝의 `/`는 자동으로 뗍니다. |

빈 값으로 설정하면 기본값을 씁니다.

```bash
SHORTLINK_DB_PATH=/var/data/shortlink.db SHORTLINK_BASE_URL=https://sl.example.com uv run uvicorn shortlink.main:create_app --factory
```

Windows PowerShell에서는 `$env:SHORTLINK_DB_PATH = "..."`처럼 설정합니다.

## 3. 웹 화면

화면은 한국어로 표시되며, 서버가 HTML을 만들어 보냅니다. 모든 화면은 `<html lang="ko">`와 viewport 설정을 갖고 있어 폭 375px 휴대폰 화면에서도 쓸 수 있습니다.

| 화면 | 경로 | 상태 | 내용 |
|---|---|---|---|
| 홈 | `GET /` | 200 | 서비스 이름, 한 줄 설명, URL 입력칸, "별칭 (선택)" 입력칸, "줄이기" 버튼 |
| 결과 | `POST /` 성공 | 200 | 단축 URL 링크, "복사" 버튼, 원래 URL, "통계 보기" 링크, "다른 URL 줄이기" 링크 |
| 입력 오류 | `POST /` 실패 (URL 또는 별칭 규칙 위반) | 422 | 홈 화면에 오류 문구를 표시하고, 입력했던 URL과 별칭을 입력칸에 남김 |
| 별칭 중복 | `POST /` 실패 (이미 쓰이는 별칭) | 409 | 홈 화면에 "이미 쓰이는 별칭입니다." 문구를 표시하고, 입력했던 URL과 별칭을 입력칸에 남김 |
| 통계 | `GET /stats/{code}` | 200 | 단축 URL, 원래 URL, 클릭 수, 생성 시각, 마지막 접근 시각(접근한 적이 없으면 "아직 없음") |
| 찾을 수 없음 | 없는 코드로 `GET /{code}` 또는 `GET /stats/{code}` | 404 | "링크를 찾을 수 없습니다" 안내와 "홈으로 가기" 링크 |

### 사용 흐름

1. `http://localhost:8000/`에 접속합니다.
2. 입력칸에 줄일 URL을 넣고 "줄이기"를 누릅니다. 예: `https://example.com/path?q=1`
3. 원하는 코드가 있으면 "별칭 (선택)" 입력칸에 별칭을 넣습니다. 예: `my-link`. 비워 두면 7자 무작위 코드를 만듭니다.
4. 결과 화면에서 단축 URL(예: `http://localhost:8000/aB3dE9f` 또는 `http://localhost:8000/my-link`)을 확인합니다.
5. "복사"를 누르면 클립보드에 복사하고 "복사했습니다."가 표시됩니다. 복사를 할 수 없는 환경이면 "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."가 표시됩니다. JavaScript가 꺼져 있어도 단축 URL 링크는 그대로 보입니다.
6. 결과 화면의 "통계 보기"를 누르면 `/stats/{code}` 통계 화면으로 이동합니다.
7. 단축 URL에 접속하면 원래 URL로 이동하고, 그 때마다 클릭 수가 1 늘어납니다.
8. 잘못된 URL이나 별칭을 제출하면 입력 오류 화면이 뜹니다. 이미 쓰이는 별칭을 제출하면 별칭 중복 화면이 뜹니다. 오류 문구는 아래 4절의 목록을 봅니다.
9. 없는 코드로 접속하면 "링크를 찾을 수 없습니다" 화면이 뜹니다.

사용자 입력은 HTML에 그대로 넣지 않고 이스케이프해서 표시합니다.

## 4. 입력 규칙과 오류 문구

### 4.1 URL

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

### 4.2 별칭 (F2)

별칭은 단축 URL의 코드가 됩니다. 주지 않으면 7자 무작위 코드(영문 대소문자와 숫자)를 만듭니다. 별칭은 다음 규칙을 모두 지켜야 하며, 아래 순서대로 검사해서 처음 걸린 규칙의 문구 하나를 씁니다.

1. 문자열이어야 합니다.
2. 길이는 4자 이상 30자 이하입니다 (문자 수 기준).
3. 영문 대소문자, 숫자, 하이픈(`-`)만 쓸 수 있습니다. 한글, 밑줄(`_`), 슬래시, 점, 공백은 쓸 수 없습니다.
4. 하이픈으로 시작하거나 끝날 수 없습니다.
5. 예약어를 쓸 수 없습니다. 예약어는 대소문자를 무시하고 비교합니다 (`Admin`, `API`도 거절). 예약어 목록: `links`, `static`, `stats`, `docs`, `redoc`, `openapi.json`, `api`, `admin`, `manage`

별칭은 대소문자를 구분합니다. `My-Link`와 `my-link`는 서로 다른 별칭이고 각각 다른 URL로 연결할 수 있습니다. 앞뒤 공백은 잘라 내지 않으므로 `" my-link"`처럼 공백이 있으면 3번 규칙에 걸려 거절됩니다.

| 상수 | 문구 | 응답 |
|---|---|---|
| `MSG_ALIAS_LENGTH` | 별칭은 4자 이상 30자 이하여야 합니다. | 422 |
| `MSG_ALIAS_CHARS` | 별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다. | 422 |
| `MSG_ALIAS_HYPHEN_EDGE` | 별칭은 하이픈(-)으로 시작하거나 끝날 수 없습니다. | 422 |
| `MSG_ALIAS_RESERVED` | 예약어라서 별칭으로 쓸 수 없습니다. 다른 별칭을 입력해 주세요. | 422 |
| `MSG_ALIAS_TAKEN` | 이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요. | 409 |

- 이미 쓰이는 코드나 별칭을 다시 만들려고 하면 `409`입니다. 무작위로 만들어진 기존 코드와 같은 별칭도 `409`입니다. 기존 링크는 바뀌지 않습니다.
- 규칙 위반(`422`)과 중복(`409`)으로 거절된 요청은 아무것도 저장하지 않습니다.
- 화면에서 URL과 별칭이 둘 다 틀리면 URL 오류 문구 하나만 보입니다. 두 입력값은 모두 입력칸에 남습니다.
- API에서 `alias`가 없거나 `null`이면 무작위 코드를 만듭니다. `""`(빈 문자열)은 별칭을 준 것으로 보고 길이 규칙(`422`)에 걸립니다. 문자열이 아닌 값(숫자, 배열 등)은 FastAPI 기본 `422` 본문(`detail`이 배열)이 옵니다.
- 화면 폼에서 별칭 입력칸을 비워 두면 무작위 코드를 만듭니다.

위 상수는 `src/shortlink/validation.py`에 정의되어 있습니다.

## 5. JSON API

### 5.1 단축 URL 생성: `POST /links`

요청 본문은 JSON 객체이고 `url` 필드가 필요합니다. `alias` 필드는 선택입니다.

| 필드 | 필수 | 내용 |
|---|---|---|
| `url` | 예 | 줄일 원래 URL |
| `alias` | 아니오 | 원하는 코드 (4절 4.2). 없거나 `null`이면 무작위 코드 |

무작위 코드로 만들기:

```bash
curl -s -i -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/path?q=1"}' \
  http://localhost:8000/links
```

별칭으로 만들기:

```bash
curl -s -i -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "alias": "my-link"}' \
  http://localhost:8000/links
```

성공 응답 (`201 Created`):

```http
HTTP/1.1 201 Created
content-type: application/json

{
  "code": "my-link",
  "short_url": "http://localhost:8000/my-link",
  "url": "https://example.com",
  "created_at": "2026-10-29T01:23:45Z"
}
```

| 필드 | 내용 |
|---|---|
| `code` | 별칭을 줬으면 별칭, 아니면 영문 대소문자와 숫자로 된 7자 무작위 코드 |
| `short_url` | `<SHORTLINK_BASE_URL>/<code>` |
| `url` | 요청한 URL 그대로 |
| `created_at` | 생성 시각. UTC, ISO 8601, 초 단위, `Z` 접미사 |

같은 URL을 여러 번 보내면 요청마다 다른 `code`가 나옵니다. 중복을 합치지 않습니다.

규칙 위반이면 `422`와 한국어 문구를 담습니다.

```bash
curl -s -i -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "alias": "my_link"}' \
  http://localhost:8000/links
```

```http
HTTP/1.1 422 Unprocessable Entity
content-type: application/json

{"detail": "별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다."}
```

이미 쓰이는 별칭이면 `409`입니다. 같은 `my-link`를 다시 보내면 다음과 같습니다.

```http
HTTP/1.1 409 Conflict
content-type: application/json

{"detail": "이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요."}
```

URL 검증에 실패하면 `422`와 함께 한국어 문구를 담습니다.

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

`url` 필드가 없거나, 본문이 JSON 객체가 아니거나, JSON 형식이 잘못된 경우, `alias`가 문자열이 아닌 경우에는 FastAPI 기본 422 본문(`detail`이 배열)이 옵니다. 어떤 경우든 저장하지 않습니다.

### 5.2 리다이렉트: `GET /{code}`

```bash
curl -s -i http://localhost:8000/my-link
```

코드가 있으면 `302 Found`와 `Location` 헤더를 돌려줍니다. 무작위 코드와 별칭을 같은 방식으로 씁니다.

```http
HTTP/1.1 302 Found
location: https://example.com
```

리다이렉트할 때마다 그 링크의 클릭 수가 1 늘고 마지막 접근 시각이 현재 UTC 시각으로 바뀝니다 (5.3절, 7절 참고).

ASCII 문자는 원문 그대로 보내고, 한글 등 비ASCII 문자만 UTF-8 퍼센트 인코딩합니다.

코드가 없으면 `404 Not Found`와 "링크를 찾을 수 없습니다" HTML 화면을 돌려줍니다. API 클라이언트도 같은 HTML을 받습니다. 없는 코드는 클릭 수를 늘리지 않습니다.

### 5.3 클릭 통계: `GET /links/{code}/stats`

`code`에는 무작위 코드나 별칭을 씁니다. 이 요청은 클릭 수를 늘리지 않으므로 여러 번 조회해도 값이 변하지 않습니다.

```bash
curl -s http://localhost:8000/links/my-link/stats
```

성공 응답 (`200 OK`), 세 번 접속한 뒤의 예:

```http
HTTP/1.1 200 OK
content-type: application/json

{
  "code": "my-link",
  "url": "https://example.com",
  "short_url": "http://localhost:8000/my-link",
  "clicks": 3,
  "created_at": "2026-10-29T01:23:45Z",
  "last_accessed_at": "2026-10-29T02:10:03Z"
}
```

새로 만든 링크는 `clicks`가 `0`이고 `last_accessed_at`이 `null`입니다.

| 필드 | 내용 |
|---|---|
| `code` | 코드 또는 별칭 |
| `url` | 원래 URL |
| `short_url` | `<SHORTLINK_BASE_URL>/<code>` |
| `clicks` | 클릭 수 (정수). 중복을 제거하지 않은 값입니다 (아래 참고) |
| `created_at` | 생성 시각. UTC, ISO 8601, 초 단위, `Z` 접미사 |
| `last_accessed_at` | 마지막 접근 시각 (같은 형식). 접근한 적이 없으면 `null` |

없는 코드이면 `404`와 JSON 본문을 돌려줍니다.

```http
HTTP/1.1 404 Not Found
content-type: application/json

{"detail": "링크를 찾을 수 없습니다."}
```

**클릭 수는 중복을 제거하지 않은 값입니다.** 같은 사람이 같은 링크를 여러 번 열어도, 새로 고침을 해도, 자동 미리보기나 봇이 요청해도 매번 1씩 늘어납니다. 방문자를 구분하거나 같은 시간 안의 요청을 합치지 않습니다. 따라서 "방문자 수"가 아니라 "리다이렉트 요청 수"로 읽어야 합니다.

### 5.4 자동 문서

서버를 띄운 뒤 `http://localhost:8000/docs`(Swagger UI)와 `http://localhost:8000/redoc`에서 API를 볼 수 있습니다.

## 6. 보안 헤더

- 모든 응답에 `X-Content-Type-Options: nosniff`를 붙입니다.
- 웹 화면(HTML, 통계 화면 포함)에는 다음 `Content-Security-Policy`를 붙입니다.

  ```
  default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'
  ```

  화면은 같은 서버의 CSS(`/static/style.css`)와 스크립트(`/static/copy.js`)만 읽습니다.
- `/docs`와 `/redoc`은 외부 CDN 자원을 쓰므로 CSP를 붙이지 않습니다.

## 7. 저장

- 링크는 `SHORTLINK_DB_PATH`의 SQLite 파일 `links` 테이블에 저장합니다.
- 테이블 구조:

  | 열 | 형식 | 내용 |
  |---|---|---|
  | `code` | `TEXT PRIMARY KEY` | 무작위 코드 또는 별칭. 대소문자를 구분합니다 |
  | `url` | `TEXT NOT NULL` | 원래 URL |
  | `created_at` | `TEXT NOT NULL` | 생성 시각 (UTC, `YYYY-MM-DDTHH:MM:SSZ`) |
  | `clicks` | `INTEGER NOT NULL DEFAULT 0` | 리다이렉트 횟수 (F2) |
  | `last_accessed_at` | `TEXT` | 마지막 접근 시각 (F2). 접근한 적이 없으면 `NULL` |

- F1에서 만든 DB 파일을 그대로 쓸 수 있습니다. 서버나 앱이 시작할 때 `clicks`와 `last_accessed_at` 열이 없으면 `ALTER TABLE`로 자동으로 추가합니다. 별도의 마이그레이션 명령은 없습니다.
  - 기존 링크는 그대로 동작하고, 클릭 수는 `0`부터 셉니다.
  - 마지막 접근 시각은 `null`입니다.
  - 이미 열이 있으면 아무것도 바꾸지 않으므로 여러 번 시작해도 안전합니다.
  - 아주 드물게, F1 DB로 여러 프로세스가 같은 순간에 처음 시작하면 한쪽이 `duplicate column name` 오류로 시작에 실패할 수 있습니다. 다시 시작하면 정상입니다.
- 서버를 재시작하거나 같은 DB 경로로 앱을 다시 만들어도 이전 코드로 리다이렉트되고, 클릭 수도 그대로 남아 있습니다.
- 현재 링크를 지우거나 목록으로 보는 기능은 없습니다(F3 이후 범위).
- 단축 URL에 접속할 때마다 DB에 쓰기가 일어납니다. 요청 수 제한이 아직 없으므로 대량 요청이 오면 DB 쓰기 경합이 생길 수 있습니다.

## 8. 아직 없는 기능

다음 기능은 아직 구현되어 있지 않습니다.

- 인증, 만료, 삭제, 요청 수 제한, 관리 화면 (F3 예정)
- 별칭 수정
- 날짜별·지역별 같은 상세 통계, 그래프
- URL 정규화, 중복 URL 합치기, 생성한 링크 목록 조회
