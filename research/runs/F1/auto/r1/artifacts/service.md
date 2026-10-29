# ShortLink 서비스 사용법

ShortLink는 긴 URL을 짧은 링크로 바꿔 주는 URL 단축 서비스입니다. 웹 화면에서 직접 줄일 수 있고, 다른 프로그램은 JSON API를 쓸 수 있습니다. 이 문서는 현재 구현된 기능(F1: 단축 URL 생성과 리다이렉트)을 설명합니다.

## 서버 실행

```bash
uv run uvicorn shortlink.main:create_app --factory
```

기본 주소는 `http://localhost:8000`입니다. 처음 실행하면 현재 폴더에 SQLite 파일 `shortlink.db`가 만들어집니다.

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `SHORTLINK_DB_PATH` | `shortlink.db` | 링크를 저장하는 SQLite 파일 경로 |
| `SHORTLINK_BASE_URL` | `http://localhost:8000` | 단축 URL(`short_url`)의 앞부분. 끝의 `/`는 자동으로 제거됩니다 |

값이 비어 있으면 기본값을 씁니다.

```bash
SHORTLINK_DB_PATH=/data/shortlink.db SHORTLINK_BASE_URL=https://s.example.com \
  uv run uvicorn shortlink.main:create_app --factory
```

## 화면과 사용 흐름

| 화면 | 경로 | 설명 |
|---|---|---|
| 홈 | `GET /` | 서비스 이름, 한 줄 설명, "줄일 URL" 입력칸과 "줄이기" 버튼 |
| 결과 | `POST /` 성공 (200) | 만든 단축 URL 링크, 원래 URL, "복사" 버튼, "다른 URL 줄이기" 링크 |
| 입력 오류 | `POST /` 실패 (422) | 홈 화면에 오류 문구를 보여 주고, 입력했던 값을 입력칸에 그대로 남깁니다 |
| 찾을 수 없음 | 없는 코드로 `GET /{code}` (404) | "링크를 찾을 수 없습니다" 안내와 "홈으로 가기" 링크 |

사용 흐름:

1. `http://localhost:8000/`을 엽니다.
2. 줄일 URL(예: `https://www.example.com/articles?id=1`)을 입력하고 "줄이기"를 누릅니다.
3. 결과 화면에서 단축 URL을 확인합니다. "복사" 버튼을 누르면 클립보드에 단축 URL이 들어갑니다. JavaScript가 꺼져 있어도 단축 URL 링크는 보입니다.
4. 단축 URL에 접속하면 원래 URL로 이동합니다.
5. URL이 잘못되었으면 홈 화면에 빨간 오류 문구가 나오고, 입력값이 남아 있습니다. 입력칸을 고쳐 다시 제출합니다.

모든 화면은 한국어이며 `<html lang="ko">`와 viewport 설정을 갖고, 폭 375px 화면에서도 가로 스크롤 없이 쓸 수 있습니다.

## API

### 단축 URL 생성: `POST /links`

요청 본문은 JSON 객체이고 `url` 필드를 가집니다.

요청:

```bash
curl -i -X POST http://localhost:8000/links \
  -H "content-type: application/json" \
  -d '{"url": "https://example.com/path?q=1"}'
```

성공 응답 (`201 Created`):

```json
{
  "code": "aB3dE9x",
  "short_url": "http://localhost:8000/aB3dE9x",
  "url": "https://example.com/path?q=1",
  "created_at": "2026-10-29T01:23:45Z"
}
```

| 필드 | 설명 |
|---|---|
| `code` | 영문 대소문자와 숫자로 된 7자 무작위 코드 |
| `short_url` | `<SHORTLINK_BASE_URL>/<code>` |
| `url` | 요청한 원래 URL을 글자 그대로 돌려줌 |
| `created_at` | 생성 시각. UTC, ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) |

같은 URL을 여러 번 보내면 요청마다 새 코드가 나옵니다. 중복을 합치지 않습니다.

#### 422 오류 응답

거절된 요청은 `422 Unprocessable Entity`와 `{"detail": "<문구>"}` 본문을 돌려주고, 아무것도 저장하지 않습니다. 화면에서도 같은 문구를 보여 줍니다.

| 상황 | `detail` 문구 |
|---|---|
| 본문이 JSON 객체가 아님 (JSON이 아니거나 배열 등) | `요청 본문은 JSON 객체여야 합니다.` |
| `url` 필드가 없거나 빈 문자열 (`null` 포함) | `URL을 입력해 주세요.` |
| `url`이 문자열이 아님 (예: 숫자) | `URL은 문자열이어야 합니다.` |
| 길이가 2,048자를 넘음 | `URL은 2,048자 이하여야 합니다.` |
| 짝이 없는 서로게이트 문자가 들어 있음 | `URL에 쓸 수 없는 문자가 들어 있습니다.` |
| 공백(스페이스) 또는 제어 문자가 들어 있음 | `URL에 공백이나 제어 문자를 넣을 수 없습니다.` |
| 스킴이 `http`/`https`가 아님 | `http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.` |
| 호스트(도메인)가 없음 | `URL에 호스트(도메인)가 없습니다.` |

422 예시:

```bash
curl -i -X POST http://localhost:8000/links \
  -H "content-type: application/json" \
  -d '{"url": "ftp://example.com"}'
```

```json
{"detail": "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."}
```

### 리다이렉트: `GET /{code}`

```bash
curl -i http://localhost:8000/aB3dE9x
```

- 코드가 있으면 `302 Found`와 `Location` 헤더에 원래 URL을 담아 응답합니다.
- 코드가 없으면 `404 Not Found`로 "링크를 찾을 수 없습니다" 화면을 보냅니다. 7자가 아닌 코드도 같은 404 응답입니다.

302 응답 예시:

```http
HTTP/1.1 302 Found
location: https://example.com/path?q=1
```

`Location`에서는 출력 가능한 ASCII 문자를 그대로 두고, 한글 같은 비ASCII 문자만 UTF-8 퍼센트 인코딩합니다. 예를 들어 `https://example.com/검색`은 `https://example.com/%EA%B2%80%EC%83%89`로 응답합니다. 이미 있는 `%xx`는 그대로 둡니다.

## 검증 규칙

API와 웹 폼은 같은 규칙을 씁니다. 아래 순서대로 검사하고, 처음 걸리는 규칙의 문구를 돌려줍니다.

1. 값이 없거나(`None`) 빈 문자열이면 거절합니다. 웹 폼에서 `url` 필드가 아예 없어도 빈 값으로 봅니다.
2. 문자열이 아니면 거절합니다.
3. 길이가 2,048자를 넘으면 거절합니다. 2,048자는 허용합니다.
4. 짝이 없는 서로게이트 문자(U+D800–U+DFFF)가 있으면 거절합니다.
5. 공백(U+0020)이나 제어 문자(U+0000–U+001F, U+007F)가 있으면 거절합니다.
6. 스킴이 `http` 또는 `https`가 아니면 거절합니다. 대소문자는 무시하므로 `HTTPS://example.com`은 허용합니다.
7. 호스트가 없으면 거절합니다. 예: `https://`.

정규화는 하지 않습니다. 앞뒤 공백 제거, 대소문자 변경, 중복 URL 합치기를 하지 않고, 받은 URL을 그대로 저장하고 돌려줍니다. 공백이 든 URL은 고쳐 저장하지 않고 거절하므로, 입력 전에 앞뒤 공백을 지워 주세요.

## 저장

- 링크는 `SHORTLINK_DB_PATH`의 SQLite 파일에 저장합니다. 표준 라이브러리 `sqlite3`를 씁니다.
- 같은 DB 파일로 서버를 다시 띄워도 이전 코드로 리다이렉트됩니다.
- 코드가 겹치면 새 코드로 다시 만듭니다.

## 아직 없는 기능

다음 기능은 아직 구현되지 않았습니다.

- 커스텀 별칭과 클릭 통계 (F2 예정)
- 인증, 링크 만료, 삭제, 요청 수 제한 (F3 예정)
- 생성한 링크 목록 조회
