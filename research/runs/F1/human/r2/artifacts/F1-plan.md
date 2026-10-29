# F1 구현 계획 — 단축 URL 생성과 리다이렉트

- 기능 설계서: `docs/features/F1.md` (v2)
- 화면 목업: `docs/plans/mockups/F1-index.html`
- 작성: 메인 세션(오케스트레이터)

## 1. 구현 범위

- JSON API: `POST /links` (생성), `GET /{code}` (리다이렉트)
- 웹 화면: 홈(`GET /`), 결과와 입력 오류(`POST /`), 찾을 수 없음(없는 코드로 `GET /{code}`)
- 저장: `Settings.db_path`의 SQLite 파일, 표준 라이브러리 `sqlite3`
- 범위 밖: 별칭, 통계, 인증, 만료, 삭제, 요청 수 제한, URL 정규화, 목록 조회

## 2. 모듈 구조

| 파일 | 역할 | 상태 |
|---|---|---|
| `src/shortlink/main.py` | `create_app()`에서 스키마 준비, `LinkStore` 생성, 라우터 등록 | 고정 계약, 확장 |
| `src/shortlink/validation.py` | URL 검증 규칙과 오류 문구 | 스텁 |
| `src/shortlink/codes.py` | 무작위 단축 코드 생성 | 스텁 |
| `src/shortlink/db.py` | SQLite 연결과 스키마 생성 | 스텁 |
| `src/shortlink/links.py` | `Link`, `LinkStore`(생성·조회), `get_store` 의존성 | 스텁 |
| `src/shortlink/api.py` | `POST /links` | 스텁 |
| `src/shortlink/web.py` | `GET /`, `POST /`, `GET /{code}` | 스텁 |
| `src/shortlink/templates/` | `base.html`, `home.html`, `result.html`, `not_found.html` | 새로 작성 |
| `src/shortlink/static/` | `style.css`, `copy.js` | 새로 작성 |

### 라우터 등록 순서

`create_app()`은 `api.router`를 먼저, `web.router`를 나중에 등록한다. `/static` 마운트는 이미 있다.
`GET /{code}`는 경로 매개변수에 `/`가 들어가지 않으므로 `/static/...`, `/docs`, `/openapi.json`과 겹치지 않는다.
`GET /links`는 `/{code}`로 처리되어 404 화면이 나온다(코드 `links`가 없으므로).

## 3. 인터페이스

### validation.py

```python
MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = frozenset({"http", "https"})

MSG_REQUIRED = "URL을 입력해 주세요."
MSG_NOT_STRING = "URL은 문자열이어야 합니다."
MSG_TOO_LONG = "URL은 2,048자 이하여야 합니다."
MSG_INVALID_CHARS = "URL에 공백이나 제어 문자를 넣을 수 없습니다."
MSG_BAD_SCHEME = "http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다."
MSG_NO_HOST = "URL에 도메인이 없습니다. 예: https://example.com"

class InvalidURLError(ValueError):
    message: str  # 사용자에게 보여 줄 한국어 문구

def validate_url(value: object) -> str: ...
```

검사 순서와 문구:

| 순서 | 조건 | 문구 |
|---|---|---|
| 1 | 값이 없음(`None`) 또는 빈 문자열 | `MSG_REQUIRED` |
| 2 | 문자열이 아님 (숫자, 목록, 불리언 등) | `MSG_NOT_STRING` |
| 3 | 길이(`len`)가 2,048 초과 | `MSG_TOO_LONG` |
| 4 | 공백 문자(`str.isspace`) 또는 제어 문자(U+0000–U+001F, U+007F)가 들어 있음 | `MSG_INVALID_CHARS` |
| 5 | `urllib.parse.urlsplit`의 스킴이 `http`/`https`가 아님 (대소문자 무시) | `MSG_BAD_SCHEME` |
| 6 | 호스트(`urlsplit(...).hostname`)가 없거나 빈 값 | `MSG_NO_HOST` |

통과하면 받은 문자열을 **그대로** 돌려준다(정규화 없음). 순서 1과 2는 서로 배타적이라 순서가 바뀌어도 결과가 같다.

### codes.py

```python
CODE_LENGTH = 7
CODE_ALPHABET = string.ascii_letters + string.digits

def generate_code() -> str: ...  # secrets.choice 사용
```

### db.py

```python
def connect(db_path: str) -> sqlite3.Connection: ...
def init_schema(db_path: str) -> None: ...  # CREATE TABLE IF NOT EXISTS
```

스키마:

```sql
CREATE TABLE IF NOT EXISTS links (
    code       TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    created_at TEXT NOT NULL  -- 'YYYY-MM-DDTHH:MM:SSZ'
);
```

연결은 작업마다 열고 닫는다(요청이 스레드 풀에서 처리되므로 연결을 공유하지 않는다). 모든 쿼리는 파라미터 바인딩(`?`)을 쓴다.

### links.py

```python
MAX_CODE_ATTEMPTS = 10

@dataclass(frozen=True)
class Link:
    code: str
    url: str
    created_at: str  # UTC ISO 8601, 초 단위, 'Z' 접미사

class LinkStore:
    def __init__(self, db_path: str) -> None: ...
    def create(self, url: str) -> Link: ...       # 코드 충돌(IntegrityError) 시 최대 10번 재시도
    def get(self, code: str) -> Link | None: ...

def get_store(request: Request) -> LinkStore: ...  # request.app.state.store
def short_url_for(base_url: str, code: str) -> str: ...  # f"{base_url}/{code}"
```

`LinkStore.create`는 검증된 URL만 받는다. 검증은 호출하는 쪽(api, web)이 `validate_url`로 먼저 한다.

### api.py — `POST /links`

- 본문을 직접 JSON으로 읽는다(Pydantic 모델의 자동 형 변환을 피하려고). 본문이 JSON이 아니거나 객체가 아니면 422.
- `validate_url(body.get("url"))` 실패 시 `422`, 본문 `{"detail": "<문구>"}`.
- 성공 시 `201`, 본문 `{"code", "short_url", "url", "created_at"}`.

### web.py

| 함수 | 경로 | 응답 |
|---|---|---|
| `home` | `GET /` | `200`, `home.html` |
| `shorten_form` | `POST /` (폼 필드 `url`, 없어도 됨) | 성공 `200` `result.html`, 실패 `422` `home.html`(오류 문구와 입력값) |
| `follow_link` | `GET /{code}` | 있으면 `302` + `Location`, 없으면 `404` `not_found.html` |

템플릿은 Jinja2 자동 이스케이프를 켠 상태로 쓰고, `|safe`나 `Markup`으로 사용자 입력을 넣지 않는다.

### Location 헤더

저장된 URL을 그대로 넣는다. 단, HTTP 헤더에 넣을 수 없는 비ASCII 문자만 UTF-8 퍼센트 인코딩한다(ASCII URL은 글자 그대로 같음). 공백과 제어 문자는 검증에서 이미 거절되므로 헤더 주입이 생기지 않는다. Starlette `RedirectResponse`는 `<`, `>`, `"` 같은 ASCII 문자까지 인코딩하므로 쓰지 않고 `Response(status_code=302, headers={"Location": ...})`로 응답한다.

## 4. 화면 목록

| 화면 | 경로 | 상태 코드 | 템플릿 | 목업 |
|---|---|---|---|---|
| 홈 | `GET /` | 200 | `home.html` | `mockups/F1-home.html` |
| 결과 | `POST /` 성공 | 200 | `result.html` | `mockups/F1-result.html` |
| 입력 오류 | `POST /` 실패 | 422 | `home.html` | `mockups/F1-input-error.html` |
| 찾을 수 없음 | 없는 코드로 `GET /{code}` | 404 | `not_found.html` | `mockups/F1-not-found.html` |

공통: `<html lang="ko">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<link rel="stylesheet" href="/static/style.css">`, 페이지 제목(`<title>`)은 `ShortLink` 또는 `<화면 이름> · ShortLink`.

화면별 고정 문구(테스트 기준):

- 홈: 제목 `ShortLink`, 설명 `긴 URL을 짧고 공유하기 쉬운 링크로 바꿔 드립니다.`, 라벨 `줄일 URL`(`<label for="url">`), 입력칸 `id="url" name="url" type="text" inputmode="url"`, 제출 버튼 `줄이기`
- 결과: 제목 `단축 URL을 만들었습니다`, 항목명 `단축 URL`·`원래 URL`, 단축 URL 링크(`<a class="short-url" href="<short_url>">`), 버튼 `복사`(`type="button"`, `data-copy="<short_url>"`), 링크 `다른 URL 줄이기`(`href="/"`)
- 입력 오류: 홈 화면 + `<p class="error" id="url-error" role="alert">` 안에 검증 문구, 입력칸에 `value="<제출한 값>"`과 `aria-invalid="true"`
- 찾을 수 없음: 제목 `링크를 찾을 수 없습니다`, 설명 `주소가 정확한지 확인해 주세요.`, 링크 `홈으로 가기`(`href="/"`)

"복사" 버튼은 `static/copy.js`가 `navigator.clipboard.writeText`로 처리하고, 성공하면 2초 동안 문구를 `복사됨`으로 바꾼다. JavaScript가 꺼져 있어도 단축 URL 링크는 HTML에 그대로 보인다.

## 5. 수용 기준과 테스트 대응

| 수용 기준 | 테스트 파일 | 확인 내용 |
|---|---|---|
| AC-1 | `tests/test_api_links.py` | 201과 네 필드 |
| AC-2 | `tests/test_api_links.py` | `^[A-Za-z0-9]{7}$`, `short_url == f"{settings.base_url}/{code}"` |
| AC-3 | `tests/test_api_links.py` | 쿼리, 대문자, 프래그먼트가 든 URL이 글자 그대로 |
| AC-4 | `tests/test_api_links.py` | `http://` URL 201 |
| AC-5 | `tests/test_api_links.py` | 네 가지 스킴 각각 422 (parametrize) |
| AC-6 | `tests/test_api_links.py` | 필드 없음, 숫자, `null`, 빈 문자열 422 |
| AC-7 | `tests/test_api_links.py` | `https://` 422 |
| AC-8 | `tests/test_api_links.py` | 2,048자 201, 2,049자 422 |
| AC-9 | `tests/test_api_links.py` | 거절 뒤 DB `links` 행 수가 0 |
| AC-10 | `tests/test_redirect.py` | 302, `Location == 원래 URL` (`follow_redirects=False`) |
| AC-11 | `tests/test_redirect.py` | 없는 코드 404 |
| AC-12 | `tests/test_redirect.py` | 같은 URL 두 번 → 코드 다름, 둘 다 리다이렉트 |
| AC-13 | `tests/test_api_links.py` | 100번 생성한 코드가 모두 다름 |
| AC-14 | `tests/test_redirect.py` | 같은 `settings`로 `create_app`을 다시 만든 뒤 리다이렉트 |
| AC-15 | `tests/test_api_links.py` | `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`, 요청 시각과 60초 이내 |
| AC-16 | `tests/test_web.py` | 200, `text/html`, 폼, 라벨, 입력칸, `줄이기` 버튼 |
| AC-17 | `tests/test_web.py` | 200, 단축 URL `href`, 원래 URL 표시 |
| AC-18 | `tests/test_web.py` | `복사` 버튼, `href="/"`인 `다른 URL 줄이기` 링크 |
| AC-19 | `tests/test_web.py` | 422, 오류 문구, 입력값 유지, DB 행 수 0 |
| AC-20 | `tests/test_web.py` | 결과·오류 화면에 `<script>` 원문 없음, `&lt;script&gt;` 있음 |
| AC-21 | `tests/test_web.py` | 404, `text/html`, `링크를 찾을 수 없습니다`, `href="/"` |
| AC-22 | `tests/test_web.py` | 네 화면 모두 `lang="ko"`와 viewport meta |
| AC-23 | `tests/test_web.py` | 폼으로 만든 코드 → 302 리다이렉트 |

DB 행 수 확인은 `settings.db_path`에 `sqlite3`로 직접 연결해 `SELECT COUNT(*) FROM links`로 한다(테이블 이름 `links`는 이 계획의 인터페이스다).
`tests/test_validation.py`, `tests/test_codes.py`에서 `validate_url`, `generate_code`를 단위 테스트할 수 있다.

## 6. 설계서 해석 결정 (H1에서 함께 확인)

| # | 설계서 문장 | 해석 |
|---|---|---|
| D-1 | "URL은 받은 그대로 저장… 앞뒤 공백 제거… 정규화는 하지 않습니다" | 공백이나 제어 문자가 든 URL은 422로 거절한다. 공백을 지우지 않으므로 `" https://a.com"`은 원문 기준으로 스킴이 `http(s)`가 아니고, 제어 문자는 `Location` 헤더 주입 위험이 있기 때문이다. |
| D-2 | "스킴이 `http` 또는 `https`가 아님" | 스킴은 대소문자를 무시하고 비교한다(`HTTPS://example.com` 허용, 저장은 원문 그대로). |
| D-3 | 길이 2,048자 | Python `len()` 기준 문자 수. |
| D-4 | "`url` 필드가… 문자열이 아니거나" | JSON `null`도 422. 본문이 JSON 객체가 아니어도 422. 오류 본문은 `{"detail": "<한국어 문구>"}`. |
| D-5 | `created_at` 형식 | 초 단위, `Z` 접미사: `2026-10-29T01:23:45Z`. |
| D-6 | `GET /{code}`의 `Location` | ASCII URL은 글자 그대로, 비ASCII 문자만 퍼센트 인코딩. |
| D-7 | 웹 입력칸 형식 | `type="text" inputmode="url"`. `type="url"`/`required`를 쓰면 브라우저가 먼저 막아 서버 오류 화면이 보이지 않으므로, 검증은 서버가 맡는다. |
| D-8 | 없는 코드 404 | API(AC-11)와 화면(AC-21)이 같은 경로이므로 404 응답은 항상 HTML 화면이다. |
| D-9 | 코드 충돌 | 충돌 시 재생성, 최대 10번. 10번 모두 충돌하면 500(현실적으로 일어나지 않음). |
