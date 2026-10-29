# ShortLink 서비스 사용법

ShortLink는 긴 URL을 짧은 코드로 바꿔 저장하고, 짧은 URL로 접속하면 원래 URL로 보내 주는 URL 단축 서비스입니다. 웹 화면과 JSON API를 함께 제공합니다.

이 문서는 현재 구현된 기능(F1: 단축 URL 생성과 리다이렉트)을 설명합니다. 기준은 `src/shortlink/`의 실제 코드와 `docs/features/F1.md`(v2)입니다.

## 서버 실행

저장소 루트에서 실행합니다.

```bash
uv run uvicorn shortlink.main:create_app --factory
```

기본 주소는 `http://localhost:8000`입니다. 다른 포트를 쓰려면 `--port` 옵션을 붙입니다.

```bash
uv run uvicorn shortlink.main:create_app --factory --port 9000
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `SHORTLINK_DB_PATH` | `shortlink.db` | SQLite 파일 경로. 현재 폴더에 만들어진다. 없으면 처음 실행할 때 만든다. |
| `SHORTLINK_BASE_URL` | `http://localhost:8000` | 단축 URL 앞부분. 끝의 `/`는 자동으로 지운다. 응답의 `short_url`에 쓰인다. |

빈 값(`SHORTLINK_DB_PATH=`)은 설정하지 않은 것으로 보고 기본값을 씁니다.

```bash
SHORTLINK_DB_PATH=/var/data/shortlink.db SHORTLINK_BASE_URL=https://sl.example.com uv run uvicorn shortlink.main:create_app --factory
```

같은 `SHORTLINK_DB_PATH`로 서버를 다시 실행해도 이전에 만든 코드는 그대로 리다이렉트됩니다.

## 화면 목록과 사용 흐름

| 화면 | 경로 | 설명 |
|---|---|---|
| 홈 | `GET /` | 서비스 이름, 한 줄 설명, URL 입력 폼 |
| 결과 | `POST /` 성공 (200) | 만든 단축 URL 링크, 원래 URL, "복사" 버튼, "다른 URL 줄이기" 링크 |
| 입력 오류 | `POST /` 실패 (422) | 홈 화면에 오류 문구를 보이고, 입력했던 값을 입력칸에 남김 |
| 찾을 수 없음 | 없는 코드로 `GET /{code}` (404) | "링크를 찾을 수 없습니다" 안내와 "홈으로 가기" 링크 |

모든 화면은 한국어이고 `<html lang="ko">`와 viewport 설정을 갖습니다. 폭 375px 화면에서도 가로 스크롤 없이 쓸 수 있습니다.

### 사용 흐름

1. 브라우저에서 `http://localhost:8000/`을 엽니다.
2. 입력칸(`줄일 URL`)에 원래 URL을 넣고 **줄이기**를 누릅니다.
3. 결과 화면에서 단축 URL을 확인합니다.
   - **복사**: 단축 URL을 클립보드에 복사합니다. 버튼이 2초 동안 "복사됨"으로 바뀝니다. JavaScript가 꺼져 있어도 단축 URL 링크는 보입니다.
   - 단축 URL 링크를 누르면 원래 URL로 이동합니다.
   - **다른 URL 줄이기**를 누르면 홈으로 돌아갑니다.
4. URL이 잘못되면 홈 화면에 오류 문구가 나오고, 입력했던 값이 입력칸에 그대로 남습니다. 이때는 아무것도 저장되지 않습니다.
5. 없는 코드로 접속하면 "링크를 찾을 수 없습니다" 화면이 나오고 **홈으로 가기** 링크로 홈에 갈 수 있습니다.

입력칸에는 `required`나 `type="url"`을 쓰지 않습니다. 빈 값과 잘못된 URL은 브라우저가 막지 않고 서버가 검사해 422 화면으로 보여 줍니다.

## URL 검증 규칙

화면과 API가 같은 규칙을 씁니다. 실패하면 아무것도 저장하지 않습니다. 앞에서부터 검사하며 처음 걸리는 오류 문구 하나만 보여 줍니다.

| 순서 | 조건 | 오류 문구 |
|---|---|---|
| 1 | `url` 값이 없거나 빈 문자열 | `URL을 입력해 주세요.` |
| 2 | `url` 값이 문자열이 아님 (예: 숫자) | `URL은 문자열이어야 합니다.` |
| 3 | 길이가 2,048자를 넘음 | `URL은 2,048자를 넘을 수 없습니다.` |
| 4 | 공백 문자(스페이스, 탭, 줄바꿈 등)나 제어 문자(U+0000~U+001F, U+007F)가 있음. 앞뒤 공백 포함 | `URL에 공백이나 제어 문자를 넣을 수 없습니다.` |
| 4-1 | 짝 없는 서로게이트 문자(U+D800~U+DFFF)가 있음 | `URL에 쓸 수 없는 문자가 있습니다.` |
| 5 | 스킴이 `http`, `https`가 아님 (대소문자 무시) | `http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.` |
| 6 | 호스트가 없음 (예: `https://`), 또는 파싱할 수 없는 URL | `URL에 호스트(도메인)가 없습니다.` |

추가 규칙:

- URL은 받은 그대로 저장하고 돌려줍니다. 앞뒤 공백 제거, 대소문자 변경 같은 정규화를 하지 않습니다.
- 스킴은 대소문자를 구분하지 않습니다. `HTTPS://example.com`은 허용되고 그대로 저장됩니다.
- 같은 URL을 여러 번 줄이면 요청마다 새 코드가 만들어집니다. 중복을 합치지 않습니다.

## API

### 공통

- 기본 주소: `http://localhost:8000` (실제 값은 `SHORTLINK_BASE_URL`에 따라 다릅니다)
- 요청과 응답 본문은 JSON입니다.
- 성공 응답은 `201`, 검증 실패는 `422`, 없는 코드는 `404`(HTML 화면)입니다.

### POST /links: 단축 URL 생성

요청 본문:

```json
{"url": "https://example.com/path?q=1"}
```

요청 예시:

```bash
curl -i -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/path?q=1"}'
```

성공 응답 (`201 Created`):

```http
HTTP/1.1 201 Created
content-type: application/json

{
  "code": "aB3xK9p",
  "short_url": "http://localhost:8000/aB3xK9p",
  "url": "https://example.com/path?q=1",
  "created_at": "2026-10-29T01:23:45Z"
}
```

| 필드 | 설명 |
|---|---|
| `code` | 영문 대소문자와 숫자로 된 7자 무작위 코드. 이미 있는 코드와 겹치면 다시 만듭니다. |
| `short_url` | `<SHORTLINK_BASE_URL>/<code>` |
| `url` | 요청한 URL 그대로 |
| `created_at` | 생성 시각. UTC, ISO 8601, 초 단위, `Z` 접미사 |

검증 실패 응답 (`422 Unprocessable Entity`) 예시:

```bash
curl -i -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -d '{"url": "ftp://example.com"}'
```

```http
HTTP/1.1 422 Unprocessable Entity
content-type: application/json

{"detail": "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."}
```

422 본문은 항상 `{"detail": "<오류 문구>"}` 형식입니다. 오류 문구는 위 검증 규칙 표의 문구와 아래 본문 형식 오류 문구를 씁니다.

### 422 오류 문구 전체 목록

| 상황 | 오류 문구 |
|---|---|
| `url` 없음, 빈 문자열 | `URL을 입력해 주세요.` |
| `url`이 문자열이 아님 | `URL은 문자열이어야 합니다.` |
| 2,048자 초과 | `URL은 2,048자를 넘을 수 없습니다.` |
| 공백 또는 제어 문자 포함 | `URL에 공백이나 제어 문자를 넣을 수 없습니다.` |
| 짝 없는 서로게이트 문자 포함 | `URL에 쓸 수 없는 문자가 있습니다.` |
| 스킴이 http, https가 아님 | `http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.` |
| 호스트 없음, 파싱 불가 | `URL에 호스트(도메인)가 없습니다.` |
| 본문이 JSON이 아니거나 JSON 객체가 아님 | `요청 본문은 {"url": ...} 형태의 JSON 객체여야 합니다.` |

본문이 JSON이 아니거나 객체가 아닌 경우 예시:

```bash
curl -i -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -d '["https://example.com"]'
```

```http
HTTP/1.1 422 Unprocessable Entity
content-type: application/json

{"detail": "요청 본문은 {\"url\": ...} 형태의 JSON 객체여야 합니다."}
```

### GET /{code}: 리다이렉트

생성한 단축 URL로 접속하면 원래 URL로 보냅니다.

```bash
curl -i http://localhost:8000/aB3xK9p
```

성공 응답 (`302 Found`):

```http
HTTP/1.1 302 Found
location: https://example.com/path?q=1
```

- `Location` 헤더는 ASCII 문자를 그대로 두고, 비ASCII 문자만 UTF-8 퍼센트 인코딩합니다. 예를 들어 `https://example.com/검색`은 `https://example.com/%EA%B2%80%EC%83%89`로 나갑니다. 목적지는 같습니다.
- 없는 코드(또는 7자 영숫자 형식이 아닌 경로)는 항상 `404 Not Found`와 "링크를 찾을 수 없습니다" HTML 화면을 돌려줍니다. JSON 클라이언트도 같습니다.

```http
HTTP/1.1 404 Not Found
content-type: text/html; charset=utf-8

... <h1>링크를 찾을 수 없습니다</h1> ... <a href="/">홈으로 가기</a> ...
```

## 저장

- 링크는 `SHORTLINK_DB_PATH`의 SQLite 파일에 저장됩니다. 테이블 `links`(`code`, `url`, `created_at`)를 서버 시작 시 자동으로 만듭니다.
- 저장과 조회는 표준 라이브러리 `sqlite3`로 합니다. ORM은 쓰지 않습니다.
- 현재 저장된 링크를 목록으로 보는 기능, 삭제 기능, 클릭 통계, 별칭 지정은 아직 없습니다.
