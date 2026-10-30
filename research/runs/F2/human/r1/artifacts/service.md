# ShortLink 서비스 사용법

ShortLink는 긴 URL을 짧은 코드로 바꿔 저장하고, 짧은 URL로 접속하면 원래 URL로 보내 주는 서비스입니다. 원하는 별칭(커스텀 코드)을 직접 정할 수 있고, 단축 URL이 몇 번 클릭되었는지 볼 수 있습니다. 웹 화면과 JSON API를 함께 제공합니다.

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

`uv run pytest`가 실행 정책으로 막히는 환경(예: 일부 Windows PC)에서는 다음 명령을 씁니다.

```bash
uv run python -m pytest
```

SQLite 3.35 이상이 필요합니다. 클릭 수 기록에 `UPDATE ... RETURNING` 문을 쓰기 때문입니다. Python 3.12의 표준 `sqlite3`가 쓰는 SQLite가 3.35보다 오래되었다면 서버가 클릭 기록에서 실패합니다.

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
| 홈 | `GET /` | 200 | 서비스 이름, 한 줄 설명, URL 입력칸, 별칭 입력칸 "별칭 (선택)"(`name="alias"`), "줄이기" 버튼 |
| 결과 | `POST /` 성공 | 200 | 단축 URL 링크(별칭을 줬으면 별칭이 들어간 주소), "복사" 버튼, 원래 URL, "통계 보기" 링크(`/stats/{code}`), "다른 URL 줄이기" 링크 |
| 입력 오류 | `POST /` 실패 (URL 또는 별칭 형식 오류) | 422 | 홈 화면에 오류 문구를 표시하고, 입력했던 URL과 별칭을 입력칸에 남김. 문제가 된 칸에 `aria-invalid`가 붙음 |
| 별칭 중복 | `POST /` 실패 (이미 쓰이는 별칭) | 409 | 홈 화면에 "이미 사용 중인 별칭입니다. 다른 별칭을 입력해 주세요."를 표시하고, 입력했던 URL과 별칭을 입력칸에 남김 |
| 통계 | `GET /stats/{code}` | 200 | 단축 URL, 원래 URL, 클릭 수(`1,284회` 형식), 생성 시각, 마지막 접근 시각(접근한 적이 없으면 "아직 없음") |
| 찾을 수 없음 | 없는 코드로 `GET /{code}` 또는 `GET /stats/{code}` | 404 | "링크를 찾을 수 없습니다" 안내와 "홈으로 가기" 링크 |

### 사용 흐름

1. `http://localhost:8000/`에 접속합니다.
2. "줄일 URL" 입력칸에 줄일 URL을 넣습니다. 예: `https://example.com/path?q=1`
3. (선택) "별칭 (선택)" 입력칸에 원하는 코드를 넣습니다. 예: `my-link`. 비워 두면 7자 무작위 코드를 만듭니다. 별칭 규칙은 아래 4.2절을 봅니다.
4. "줄이기"를 누릅니다.
5. 결과 화면에서 단축 URL(예: `http://localhost:8000/my-link` 또는 `http://localhost:8000/aB3dE9f`)을 확인합니다.
6. "복사"를 누르면 클립보드에 복사하고 "복사했습니다."가 표시됩니다. 복사를 할 수 없는 환경이면 "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."가 표시됩니다. JavaScript가 꺼져 있어도 단축 URL 링크는 그대로 보입니다.
7. "통계 보기"를 누르면 클릭 수와 마지막 접근 시각을 보여 주는 통계 화면(`/stats/{code}`)으로 이동합니다.
8. 단축 URL에 접속하면 원래 URL로 이동하고, 그 접속은 클릭 수 1로 셉니다.
9. 잘못된 URL이나 별칭을 제출하면 입력 오류 화면이 뜹니다(422). 이미 쓰이는 별칭을 제출하면 별칭 중복 화면이 뜹니다(409). 입력칸의 값은 그대로 남아 있어 고쳐서 다시 제출할 수 있습니다. 오류 문구는 아래 4절의 목록을 봅니다.
10. 없는 코드로 접속하거나 통계를 보려 하면 "링크를 찾을 수 없습니다" 화면이 뜹니다(404). 이 경우 어떤 링크의 클릭 수도 늘지 않습니다.

사용자 입력은 HTML에 그대로 넣지 않고 이스케이프해서 표시합니다. 통계 화면의 원래 URL도 이스케이프합니다.

통계 화면은 인증이 없습니다. 코드(또는 별칭)를 아는 사람은 누구나 그 링크의 원래 URL, 클릭 수, 마지막 접근 시각을 볼 수 있습니다. 인증은 F3 범위입니다.

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

별칭은 단축 URL의 코드가 됩니다. 별칭을 주지 않으면 7자 무작위 코드를 만듭니다. 별칭은 입력한 그대로 검사하며, 앞뒤 공백 제거나 소문자 변환은 하지 않습니다. 다음 규칙을 **위에서부터 순서대로** 검사하고, 처음 걸린 규칙의 문구가 나옵니다.

| 순서 | 규칙 | 상수 | 문구 |
|---|---|---|---|
| 1 | 문자열이 아님 (API에서만 해당) | `MSG_ALIAS_NOT_STRING` | alias는 문자열이어야 합니다. |
| 2 | 길이 4~30자 (문자 수 기준). 빈 문자열 `""`도 여기서 걸림 | `MSG_ALIAS_LENGTH` | 별칭은 4자 이상 30자 이하여야 합니다. |
| 3 | 영문 대소문자, 숫자, 하이픈(`-`)만 허용. 한글, 공백, `_`, `/`, `.` 등은 거절 | `MSG_ALIAS_CHARS` | 별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다. |
| 4 | 하이픈으로 시작하거나 끝날 수 없음 | `MSG_ALIAS_HYPHEN_EDGE` | 별칭은 하이픈(-)으로 시작하거나 끝날 수 없습니다. |
| 5 | 예약어가 아님 (대소문자 무시) | `MSG_ALIAS_RESERVED` | 예약된 이름이라 별칭으로 쓸 수 없습니다. |
| 6 | 이미 쓰이는 코드나 별칭이 아님 (저장 시점) | `MSG_ALIAS_TAKEN` | 이미 사용 중인 별칭입니다. 다른 별칭을 입력해 주세요. |

예약어(사용할 수 없는 별칭): `links`, `static`, `stats`, `docs`, `redoc`, `openapi.json`, `api`, `admin`, `manage`. `Admin`, `STATS`처럼 대소문자만 다른 값도 예약어로 거절합니다.

별칭은 대소문자를 구분합니다. `My-Link`와 `my-link`는 서로 다른 별칭이며 각각 따로 만들 수 있습니다.

- 규칙 1~5 위반은 `422`입니다.
- 규칙 6 위반(이미 쓰이는 별칭 또는 무작위 코드와 겹침)은 `409`입니다.
- URL과 별칭이 둘 다 틀리면 URL 문구만 나옵니다. URL 검사를 먼저 하기 때문입니다.
- 거절된 요청은 아무것도 저장하지 않습니다.

웹 화면에서는 같은 상태 코드(`422` 또는 `409`)로 홈 화면을 다시 보여 주며, 문구가 나오고 입력했던 URL과 별칭이 입력칸에 남습니다. 별칭 칸이 비어 있으면 별칭 없이 무작위 코드를 만듭니다.

위 상수는 `src/shortlink/validation.py`와 `src/shortlink/repository.py`에 정의되어 있습니다.

## 5. JSON API

### 5.1 단축 URL 생성: `POST /links`

요청 본문은 JSON 객체이고 `url` 필드가 필요합니다. `alias`는 선택입니다.

```bash
curl -s -i -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/path?q=1"}' \
  http://localhost:8000/links
```

별칭을 함께 보낼 수도 있습니다.

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
  "code": "aB3dE9f",
  "short_url": "http://localhost:8000/aB3dE9f",
  "url": "https://example.com/path?q=1",
  "created_at": "2026-10-29T01:23:45Z"
}
```

별칭을 준 경우 `code`와 `short_url`에 별칭이 들어갑니다.

```http
HTTP/1.1 201 Created
content-type: application/json

{
  "code": "my-link",
  "short_url": "http://localhost:8000/my-link",
  "url": "https://example.com",
  "created_at": "2026-10-30T09:00:00Z"
}
```

| 필드 | 내용 |
|---|---|
| `code` | 별칭을 줬으면 별칭, 아니면 영문 대소문자와 숫자로 된 7자 무작위 코드 |
| `short_url` | `<SHORTLINK_BASE_URL>/<code>` |
| `url` | 요청한 URL 그대로 |
| `created_at` | 생성 시각. UTC, ISO 8601, 초 단위, `Z` 접미사 |

`alias`는 생략하거나 `null`이면 별칭이 없는 것으로 보고 무작위 코드를 만듭니다. 빈 문자열 `""`은 별칭이 없다는 뜻이 아니라 길이 규칙 위반이므로 `422`입니다.

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

별칭 규칙을 어기면 역시 `422`이고 4.2절의 문구가 `detail`에 들어갑니다. 예: `"alias": "my_link"`는 `{"detail": "별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다."}`.

이미 쓰이는 별칭을 주면 `409 Conflict`입니다.

```bash
curl -s -i -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/other", "alias": "my-link"}' \
  http://localhost:8000/links
```

```http
HTTP/1.1 409 Conflict
content-type: application/json

{"detail": "이미 사용 중인 별칭입니다. 다른 별칭을 입력해 주세요."}
```

409일 때는 아무것도 저장하지 않으며, 기존 `my-link`는 그대로 원래 URL로 리다이렉트됩니다.

`url` 필드가 없거나, 본문이 JSON 객체가 아니거나, JSON 형식이 잘못된 경우에는 FastAPI 기본 422 본문(`detail`이 배열)이 옵니다. `alias`가 문자열이 아니면(숫자, 배열 등) 같은 기본 422 본문이 옵니다. 어떤 경우든 저장하지 않습니다.

### 5.2 리다이렉트: `GET /{code}`

```bash
curl -s -i http://localhost:8000/aB3dE9f
```

코드가 있으면 `302 Found`와 `Location` 헤더를 돌려줍니다. 별칭으로 만든 코드도 같은 방식으로 리다이렉트됩니다.

```http
HTTP/1.1 302 Found
location: https://example.com/path?q=1
```

ASCII 문자는 원문 그대로 보내고, 한글 등 비ASCII 문자만 UTF-8 퍼센트 인코딩합니다.

리다이렉트할 때마다 그 링크의 클릭 수를 1 늘리고 마지막 접근 시각을 기록합니다. 클릭 수는 통계 API와 통계 화면에서 볼 수 있습니다. 같은 링크를 3번 열면 클릭 수는 3이 됩니다. 이 경로는 `GET`만 받으므로 `HEAD` 요청은 세지 않고 `405`를 돌려줍니다.

코드가 없으면 `404 Not Found`와 "링크를 찾을 수 없습니다" HTML 화면을 돌려줍니다. API 클라이언트도 같은 HTML을 받습니다. 없는 코드로 요청하면 어떤 링크의 클릭 수도 늘지 않습니다.

### 5.3 통계 조회: `GET /links/{code}/stats`

`code`(또는 별칭)의 통계를 JSON으로 돌려줍니다. 공개 API이므로 인증이 없습니다. 통계 조회는 클릭 수를 늘리지 않습니다. 여러 번 조회해도 같은 값입니다.

```bash
curl -s http://localhost:8000/links/my-link/stats
```

성공 응답 (`200 OK`), 접근한 적이 없는 링크:

```json
{
  "code": "my-link",
  "url": "https://example.com",
  "short_url": "http://localhost:8000/my-link",
  "clicks": 0,
  "created_at": "2026-10-30T09:00:00Z",
  "last_accessed_at": null
}
```

`curl -s -o /dev/null http://localhost:8000/my-link`를 세 번 실행한 뒤에는 `clicks`가 `3`이고 `last_accessed_at`이 마지막 접근 시각(예: `"2026-10-30T09:05:12Z"`)으로 채워집니다.

| 필드 | 내용 |
|---|---|
| `code` | 코드 또는 별칭 |
| `url` | 원래 URL |
| `short_url` | `<SHORTLINK_BASE_URL>/<code>` |
| `clicks` | 클릭 수 (정수). 처음에는 0 |
| `created_at` | 생성 시각. `POST /links`와 같은 형식(UTC, `Z` 접미사) |
| `last_accessed_at` | 마지막 접근 시각(같은 형식). 접근한 적이 없으면 `null` |

없는 코드면 `404`입니다. 본문은 JSON입니다.

```http
HTTP/1.1 404 Not Found
content-type: application/json

{"detail": "링크를 찾을 수 없습니다."}
```

통계 화면(`GET /stats/{code}`)은 같은 정보를 HTML로 보여 줍니다. 없는 코드면 `404` HTML 화면이며, 본문 형식이 JSON API와 다릅니다.

### 5.4 자동 문서

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
- 테이블 구조:

  ```sql
  CREATE TABLE IF NOT EXISTS links (
      code             TEXT PRIMARY KEY,
      url              TEXT NOT NULL,
      created_at       TEXT NOT NULL,
      clicks           INTEGER NOT NULL DEFAULT 0,
      last_accessed_at TEXT
  )
  ```

  `code`에는 무작위 코드와 별칭이 함께 들어갑니다. 별칭이 기존 코드와 같으면 저장에 실패하고 `409`가 됩니다. `clicks`는 클릭 수, `last_accessed_at`은 마지막 접근 시각(`created_at`과 같은 형식, 접근한 적이 없으면 `NULL`)입니다.
- F1 때 만든 DB 파일로 앱을 시작해도 됩니다. 시작할 때 `clicks`와 `last_accessed_at` 열이 없으면 자동으로 추가합니다(`ALTER TABLE ... ADD COLUMN`). 기존 링크는 리다이렉트가 그대로 되고, 클릭 수는 0부터 셉니다. 데이터를 옮기거나 따로 준비할 필요는 없습니다.
- 여러 프로세스나 워커가 같은 F1 DB로 동시에 시작해도 마이그레이션은 한 번만 실행됩니다.
- 클릭 수는 `UPDATE ... RETURNING`으로 한 문장에서 올립니다. SQLite 3.35 이상이 필요합니다(1절 참고).
- 서버를 재시작하거나 같은 DB 경로로 앱을 다시 만들어도 이전 코드와 클릭 수가 유지됩니다.
- 현재 링크를 지우거나 목록으로 보는 기능은 없습니다(F3 이후 범위).

## 8. 아직 없는 기능

다음 기능은 아직 구현되어 있지 않습니다.

- 인증, 만료, 삭제, 요청 수 제한, 관리 화면 (F3 예정). 통계 조회는 현재 인증 없이 공개입니다.
- 날짜별, 지역별 같은 상세 통계와 그래프
- 별칭 수정
- URL 정규화, 중복 URL 합치기, 생성한 링크 목록 조회
