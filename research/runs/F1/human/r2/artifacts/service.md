# ShortLink 서비스 사용법

ShortLink는 긴 URL을 짧은 코드로 바꿔 저장하고, 짧은 URL로 접속하면 원래 URL로 보내 주는 서비스입니다. 웹 화면에서 직접 줄이거나, JSON API로 다른 프로그램에서 호출할 수 있습니다.

이 문서는 F1 기능(단축 URL 생성과 리다이렉트)을 기준으로 씁니다. 기능 설계는 `docs/features/F1.md`를 참고합니다.

## 1. 서버 실행

저장소 루트에서 다음 명령으로 서버를 실행합니다.

```bash
uv run uvicorn shortlink.main:create_app --factory
```

기본 주소는 `http://localhost:8000`입니다. 서버를 시작하면 `SHORTLINK_DB_PATH`가 가리키는 SQLite 파일(기본값 `shortlink.db`)과 테이블이 없으면 자동으로 만들어집니다.

## 2. 환경 변수

| 이름 | 기본값 | 설명 |
|---|---|---|
| `SHORTLINK_DB_PATH` | `shortlink.db` | 링크를 저장할 SQLite 파일 경로. 같은 경로로 서버를 다시 켜면 이전에 만든 링크도 계속 동작합니다. |
| `SHORTLINK_BASE_URL` | `http://localhost:8000` | 응답의 `short_url`을 만들 때 쓰는 기준 주소. 끝의 `/`는 자동으로 제거합니다. |

값이 비어 있으면 기본값을 씁니다. 실행 전에 설정하는 예는 다음과 같습니다.

```bash
export SHORTLINK_DB_PATH=/var/data/shortlink.db
export SHORTLINK_BASE_URL=https://sho.rt
uv run uvicorn shortlink.main:create_app --factory
```

```powershell
$env:SHORTLINK_DB_PATH = "C:\data\shortlink.db"
$env:SHORTLINK_BASE_URL = "https://sho.rt"
uv run uvicorn shortlink.main:create_app --factory
```

## 3. 웹 화면

화면은 모두 한국어이며, 서버가 HTML을 만들어 보냅니다.

| 화면 | 경로 | 상태 코드 | 내용 |
|---|---|---|---|
| 홈 | `GET /` | 200 | 서비스 이름, 한 줄 설명, URL 입력 폼 |
| 결과 | `POST /` 성공 | 200 | 단축 URL(링크), 원래 URL, "복사" 버튼, "다른 URL 줄이기" 링크 |
| 입력 오류 | `POST /` 실패 | 422 | 홈 화면에 오류 문구를 표시하고, 입력했던 값을 입력칸에 남김 |
| 찾을 수 없음 | 없는 코드로 `GET /{code}` | 404 | "링크를 찾을 수 없습니다" 안내와 "홈으로 가기" 링크 |

### 사용 흐름

1. **URL 줄이기**: `http://localhost:8000/`에 접속합니다. "줄일 URL" 입력칸에 `https://example.com/path?q=1`을 넣고 "줄이기"를 누릅니다.
2. **결과 확인**: 결과 화면에 단축 URL(예: `http://localhost:8000/aB3xY9Q`), 원래 URL, "복사" 버튼이 나옵니다.
   - "복사"를 누르면 단축 URL이 클립보드에 복사되고, 버튼이 2초 동안 "복사됨"으로 바뀝니다. 이 기능은 JavaScript를 씁니다.
   - JavaScript가 꺼져 있어도 단축 URL 링크는 보입니다.
   - "다른 URL 줄이기"를 누르면 홈으로 돌아갑니다.
3. **단축 URL 사용**: 단축 URL 링크를 누르면 원래 URL(`https://example.com/path?q=1`)로 이동합니다(302 리다이렉트).
4. **입력 오류**: 홈에서 `javascript:alert(1)`처럼 허용되지 않는 URL을 넣고 "줄이기"를 누르면, 같은 화면에 빨간 오류 문구가 나오고 입력값이 입력칸에 그대로 남습니다. 이 경우 아무것도 저장되지 않습니다.
5. **찾을 수 없음**: 없는 코드(예: `http://localhost:8000/zzzzzzz`)로 접속하면 "링크를 찾을 수 없습니다" 화면이 나오고, "홈으로 가기" 링크로 홈에 돌아갈 수 있습니다.

### 입력 오류 문구

웹 화면과 API는 같은 검증 규칙과 같은 문구를 씁니다. API에서는 문구가 `detail` 필드에 담깁니다.

| 상황 | 오류 문구 |
|---|---|
| `url`이 없거나, `null`이거나, 빈 문자열 | URL을 입력해 주세요. |
| `url`이 문자열이 아님 (숫자, 목록, 불리언 등) | URL은 문자열이어야 합니다. |
| 길이가 2,048자를 넘음 | URL은 2,048자 이하여야 합니다. |
| 공백이나 제어 문자가 들어 있음 | URL에 공백이나 제어 문자를 넣을 수 없습니다. |
| 스킴이 `http`나 `https`가 아님 (`ftp:`, `javascript:`, `data:`, `mailto:` 등) | http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다. |
| 호스트(도메인)가 없음 (예: `https://`) | URL에 도메인이 없습니다. 예: https://example.com |
| API 본문이 JSON 객체가 아님 (JSON이 아니거나, 배열이거나, `null`) | 요청 본문은 JSON 객체여야 합니다. (API 전용) |

검증은 위에서 아래 순서로 하며, 처음 걸린 규칙의 문구를 돌려줍니다. 통과한 URL은 입력한 글자 그대로 저장합니다. 앞뒤 공백 제거나 대소문자 변경 같은 정규화는 하지 않습니다. 스킴 검사는 대소문자를 구분하지 않습니다(`HTTPS://example.com`은 허용).

## 4. API

### 4.1 단축 URL 만들기: `POST /links`

요청 본문은 JSON이며, `url` 필드에 원래 URL을 담습니다.

```http
POST /links HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{"url": "https://example.com/path?q=1"}
```

curl 예:

```bash
curl -s -i -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/path?q=1"}'
```

#### 성공: `201 Created`

| 필드 | 내용 |
|---|---|
| `code` | 단축 코드. 영문 대소문자와 숫자로 된 7자 |
| `short_url` | `<SHORTLINK_BASE_URL>/<code>` |
| `url` | 요청한 원래 URL 그대로 |
| `created_at` | 생성 시각. UTC, 초 단위, ISO 8601 (`Z` 접미사) |

```json
{
  "code": "aB3xY9Q",
  "short_url": "http://localhost:8000/aB3xY9Q",
  "url": "https://example.com/path?q=1",
  "created_at": "2026-10-29T01:23:45Z"
}
```

같은 URL을 여러 번 보내면 요청마다 새 코드가 만들어집니다. 중복을 합치지 않습니다.

#### 실패: `422 Unprocessable Entity`

검증에 실패하면 아무것도 저장하지 않고, 본문 `detail`에 오류 문구를 담아 돌려줍니다.

```json
{
  "detail": "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."
}
```

예: `{"url": "javascript:alert(1)"}`를 보내면 위와 같은 422 응답이 옵니다.

오류 문구 전체 목록은 3절의 "입력 오류 문구" 표를 참고합니다.

### 4.2 리다이렉트: `GET /{code}`

단축 URL의 코드로 접속하면 원래 URL로 보냅니다.

```bash
curl -s -i http://localhost:8000/aB3xY9Q
```

#### 찾음: `302 Found`

```http
HTTP/1.1 302 Found
location: https://example.com/path?q=1
```

`Location` 헤더에는 저장된 URL이 들어갑니다. ASCII 문자는 그대로 두고, 비ASCII 문자만 UTF-8 퍼센트 인코딩합니다.

#### 없음: `404 Not Found`

없는 코드이면 "링크를 찾을 수 없습니다" HTML 화면을 돌려줍니다(JSON이 아닙니다).

```http
HTTP/1.1 404 Not Found
content-type: text/html; charset=utf-8
```

## 5. 참고

- 생성 API와 입력 폼은 같은 저장소에 저장합니다. 화면에서 만든 링크도 `GET /{code}`로 리다이렉트됩니다.
- 사용자가 입력한 값은 HTML에 이스케이프해서 표시합니다.
- 모든 화면은 `<html lang="ko">`와 viewport meta를 갖고, 폭 375px 화면에서도 가로 스크롤 없이 쓸 수 있도록 만들었습니다.
- 이 버전에 없는 기능: 커스텀 별칭, 클릭 통계, 인증, 만료, 삭제, 요청 수 제한, URL 정규화, 중복 URL 합치기, 생성한 링크 목록 조회.
