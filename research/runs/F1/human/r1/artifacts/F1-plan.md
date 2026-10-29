# F1 구현 계획 — 단축 URL 생성과 리다이렉트

- 설계서: `docs/features/F1.md` (v2)
- 화면 목업: `docs/plans/mockups/F1-index.html`
- 실행 모드: human

## 1. 구현 범위

- JSON API: `POST /links` (생성), `GET /{code}` (리다이렉트)
- 웹 화면 4개: 홈(`GET /`), 결과(`POST /` 성공), 입력 오류(`POST /` 실패), 찾을 수 없음(`GET /{code}` 404)
- SQLite 저장 (`sqlite3`, ORM 없음), 앱을 다시 만들어도 데이터 유지
- 범위 밖: 별칭, 통계, 인증, 만료, 삭제, 요청 수 제한, URL 정규화, 목록 조회

## 2. 모듈 구조

| 파일 | 역할 | 상태 |
|---|---|---|
| `src/shortlink/main.py` | `create_app()`: 스키마 준비, `app.state.repository` 설정, `api.router` → `web.router` 순서로 등록 | 연결 완료 (고정 계약 확장) |
| `src/shortlink/validation.py` | `validate_url()`, `InvalidURLError`, 오류 문구 상수 | 스텁 |
| `src/shortlink/codes.py` | `generate_code()`, `build_short_url()`, `CODE_LENGTH=7`, `CODE_ALPHABET` | 스텁 |
| `src/shortlink/db.py` | `connect()`, `init_schema()` | 스텁 |
| `src/shortlink/repository.py` | `Link`, `LinkRepository.create()/get()`, `format_timestamp()` | 스텁 |
| `src/shortlink/dependencies.py` | `get_settings()`, `get_repository()` (app.state에서 꺼냄) | 스텁 |
| `src/shortlink/api.py` | `POST /links`, 응답 모델 `LinkOut` | 스텁 |
| `src/shortlink/web.py` | `GET /`, `POST /`, `GET /{code}`, `location_header_value()` | 스텁 |
| `src/shortlink/templates/` | `base.html`, `home.html`, `result.html`, `not_found.html` | 구현 단계에서 작성 |
| `src/shortlink/static/` | `style.css` (목업 공통 스타일 그대로), `copy.js` | 구현 단계에서 작성 |

라우트 순서: `GET /{code}`가 모든 한 단계 경로를 받으므로 `web.router`를 마지막에 등록한다. `/static`은 마운트이고 `/{code}`는 `/`를 포함한 경로와 맞지 않으므로 충돌하지 않는다.

## 3. 인터페이스

### 3.1 검증 (`validation.validate_url(url: object) -> str`)

규칙을 아래 순서로 검사하고 처음 걸린 규칙의 문구로 `InvalidURLError(message)`를 던진다. 통과하면 입력을 **그대로** 돌려준다(정규화 없음).

| 순서 | 조건 | 문구 상수 | 문구 |
|---|---|---|---|
| 1 | 문자열이 아님 | `MSG_NOT_STRING` | url은 문자열이어야 합니다. |
| 2 | 빈 문자열 | `MSG_EMPTY` | URL을 입력해 주세요. |
| 3 | 2,048자 초과 (문자 수 기준) | `MSG_TOO_LONG` | URL은 2,048자 이하여야 합니다. |
| 4 | 공백 또는 ASCII 제어 문자(≤0x20, 0x7F) 포함 | `MSG_INVALID_CHAR` | URL에 공백이나 제어 문자를 넣을 수 없습니다. |
| 5 | UTF-8로 인코딩할 수 없는 문자(짝 없는 서로게이트 U+D800–U+DFFF) 포함 (D-9) | `MSG_INVALID_ENCODING` | URL에 올바르지 않은 문자가 있습니다. |
| 6 | 스킴이 http/https가 아님 (대소문자 무시) | `MSG_SCHEME` | http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다. |
| 7 | 호스트 없음 (`https://`, `https://:80`) | `MSG_NO_HOST` | URL에 호스트(도메인)가 없습니다. 예: https://example.com |

### 3.2 코드와 저장

- `generate_code()`: `secrets.choice`로 `[A-Za-z0-9]` 7자.
- `build_short_url(base_url, code)`: `f"{base_url}/{code}"`.
- 테이블: `links(code TEXT PRIMARY KEY, url TEXT NOT NULL, created_at TEXT NOT NULL)`.
- `LinkRepository.create(url)`: 코드를 만들어 INSERT, PRIMARY KEY 충돌(`sqlite3.IntegrityError`)이면 새 코드로 재시도, 최대 10회 후 `RuntimeError`. 같은 URL이어도 매번 새 행.
- `LinkRepository.get(code)`: 없으면 `None`.
- 연결은 호출마다 열고 반드시 닫는다(`sqlite3.connect`의 `with`는 닫지 않으므로 `contextlib.closing` 등 사용). SQL은 모두 파라미터 바인딩.
- `created_at`: 생성 시점 UTC, 초 단위, `"YYYY-MM-DDTHH:MM:SSZ"` 문자열로 저장하고 그대로 응답.
- `code_factory` 인자로 코드 생성기를 바꿔 넣을 수 있다(충돌 재시도 테스트용).

### 3.3 JSON API

`POST /links`, 본문 `{"url": "..."}`

- 201: `{"code", "short_url", "url", "created_at"}`
- 422: `url` 없음, 문자열 아님(숫자, null, 배열 등), 검증 실패, JSON 형식 오류, 본문이 객체가 아님. 검증 실패 본문은 `{"detail": "<문구>"}`, 그 밖의 형식 오류는 FastAPI 기본 422 본문. 어떤 경우든 저장하지 않는다.

`GET /{code}`

- 있으면 `302`, `Location: location_header_value(url)`.
  - ASCII URL은 한 글자도 바꾸지 않는다. 비ASCII 문자만 UTF-8 퍼센트 인코딩한다(헤더 값은 latin-1이어야 하므로).
  - Starlette `RedirectResponse`는 `<`, `>`, `"` 등 일부 ASCII를 인코딩하므로 쓰지 않고 `Response(status_code=302, headers={"Location": ...})`로 만든다.
- 없으면 `404`, `not_found.html` (HTML). API 클라이언트도 같은 404 HTML을 받는다(설계서는 상태 코드만 요구).

### 3.4 웹 화면

| 화면 | 요청 | 상태 | 템플릿 | 목업 |
|---|---|---|---|---|
| 홈 | `GET /` | 200 | `home.html` | `F1-home.html` |
| 결과 | `POST /` (form `url`) 성공 | 200 | `result.html` | `F1-result.html` |
| 입력 오류 | `POST /` 실패 | 422 | `home.html` (오류 문구 + 입력값 유지) | `F1-error.html` |
| 찾을 수 없음 | `GET /{code}` 없음 | 404 | `not_found.html` | `F1-not-found.html` |

- 폼: `<form method="post" action="/">`, `<label for="url">줄일 URL</label>`, `<input type="text" id="url" name="url" inputmode="url">`, `<button type="submit">줄이기</button>`.
  - `type="url"`이나 `required`는 쓰지 않는다. 브라우저 검증이 서버 오류 화면을 가리지 않도록 검증은 서버 한 곳에서 한다.
- 폼에 `url` 필드가 없으면 빈 문자열로 보고 "URL을 입력해 주세요." 오류.
- 결과 화면: `<a class="short-url" href="{{ short_url }}">{{ short_url }}</a>`, `<button type="button" class="copy-button" data-copy="{{ short_url }}">복사</button>`, 원래 URL, `<a href="/">다른 URL 줄이기</a>`.
- 복사: `/static/copy.js`(`defer`)에서 `navigator.clipboard.writeText`, 결과를 `#copy-status`(aria-live)에 "복사했습니다." / "복사하지 못했습니다. 링크를 직접 선택해 복사해 주세요."로 표시.
- 찾을 수 없음: 제목 "링크를 찾을 수 없습니다", 안내 문장, `<a href="/">홈으로 가기</a>`.
- 공통: `base.html`이 `<html lang="ko">`, `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `/static/style.css`, 헤더의 "ShortLink" 로고 링크를 담는다.
- 이스케이프: Jinja2 자동 이스케이프(`Jinja2Templates` 기본, `.html` 템플릿) 유지. `|safe`, `Markup` 금지.
- 문구, 배치, 색은 목업 그대로. CSS는 목업의 공통 스타일 블록을 `style.css`로 옮긴다.

## 4. 수용 기준과 테스트 대응

| AC | 내용 | 테스트 파일 | 확인할 것 |
|---|---|---|---|
| AC-1 | 생성 201과 네 필드 | `tests/test_api_links.py` | 상태 201, 키 4개 |
| AC-2 | 코드 7자 영숫자, short_url 형식 | `tests/test_api_links.py` | 정규식 `^[A-Za-z0-9]{7}$`, `short_url == settings.base_url + "/" + code` |
| AC-3 | url 원문 그대로 | `tests/test_api_links.py` | 쿼리, 대문자, 퍼센트 인코딩이 든 URL이 그대로 |
| AC-4 | http 허용 | `tests/test_api_links.py` | `http://example.com` 201 |
| AC-5 | 다른 스킴 거절 | `tests/test_api_links.py` | 설계서 예시 4개 각각 422 (parametrize) |
| AC-6 | 필드 없음, 문자열 아님, 빈 문자열 | `tests/test_api_links.py` | `{}`, `{"url": 123}`, `{"url": ""}` 422 |
| AC-7 | 호스트 없음 | `tests/test_api_links.py` | `https://` 422 |
| AC-8 | 길이 경계 | `tests/test_api_links.py` | 정확히 2,048자 201, 2,049자 422 |
| AC-9 | 거절 시 저장 없음 | `tests/test_api_links.py` | 거절 요청 뒤 DB `links` 행 수 0 (sqlite3로 직접 확인) |
| AC-10 | 302와 Location | `tests/test_redirect.py` | `follow_redirects=False`, Location == 원래 URL |
| AC-11 | 없는 코드 404 | `tests/test_redirect.py` | 404 |
| AC-12 | 같은 URL 두 번 → 다른 코드, 둘 다 리다이렉트 | `tests/test_redirect.py` | |
| AC-13 | 100번 생성 코드 모두 다름 | `tests/test_api_links.py` | `len(set(codes)) == 100` |
| AC-14 | 앱 재생성 후 리다이렉트 | `tests/test_redirect.py` | 같은 `settings`로 `create_app` 두 번 |
| AC-15 | created_at UTC ISO 8601, 1분 이내 | `tests/test_api_links.py` | 형식 `^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$`, 요청 전후 시각과 비교 |
| AC-16 | 홈 화면 폼 | `tests/test_web.py` | 200, `text/html`, form method/action, label for=url, name="url", "줄이기" |
| AC-17 | 결과 화면 링크와 원래 URL | `tests/test_web.py` | 200, `href="<short_url>"`, 원래 URL 표시 |
| AC-18 | 복사 버튼, 다른 URL 줄이기 | `tests/test_web.py` | "복사" 버튼, `href="/"`인 "다른 URL 줄이기" |
| AC-19 | 입력 오류 화면 | `tests/test_web.py` | 422, `text/html`, 오류 문구, `value="<입력값>"`, 행 수 0 |
| AC-20 | 이스케이프 | `tests/test_web.py` | `https://example.com/<script>alert(1)</script>`(결과), `<script>alert(1)</script>`(오류) 제출 시 HTML에 `<script>alert(1)` 원문 없음, `&lt;script&gt;` 있음 |
| AC-21 | 404 화면 | `tests/test_web.py` | 404, `text/html`, "링크를 찾을 수 없습니다", `href="/"` |
| AC-22 | lang, viewport | `tests/test_web.py` | 네 화면 모두 `<html lang="ko">`, `name="viewport"` |
| AC-23 | 폼으로 만든 코드 리다이렉트 | `tests/test_web.py` | 결과 HTML에서 코드 추출 → `GET /{code}` 302 |

보조 단위 테스트: `tests/test_validation.py`(규칙 순서와 문구, 대문자 스킴, 공백 거절), `tests/test_repository.py`(충돌 재시도: `code_factory`가 같은 코드를 먼저 돌려줄 때 새 코드로 저장, 계속 충돌하면 `RuntimeError`).

## 5. 설계서 해석 결정 (H1에서 확인 요청)

| # | 설계서 | 해석 | 이유 |
|---|---|---|---|
| D-1 | 스킴이 http/https가 아님 | 대소문자 무시(`HTTPS://example.com` 허용), 저장은 원문 그대로 | RFC 3986상 스킴은 대소문자를 구분하지 않음 |
| D-2 | 거절 조건 목록 | 공백, 제어 문자(줄바꿈 등)가 든 URL도 422로 거절 | 앞 공백은 파이썬 URL 파서가 몰래 무시하고, 줄바꿈은 `Location` 헤더를 깨뜨림. 정규화(제거)가 아니라 거절이므로 "그대로 저장" 원칙과 충돌하지 않음 |
| D-3 | 2,048자 | 문자(code point) 수 기준 | 설계서가 "자"라고 씀 |
| D-4 | `Location: <원래 URL>` | ASCII는 그대로, 비ASCII만 UTF-8 퍼센트 인코딩 | HTTP 헤더는 latin-1만 허용. 한글 URL로 500이 나지 않게 함 |
| D-5 | 422 응답 본문 | 형식은 설계서에 없음. 검증 실패는 `{"detail": "<한국어 문구>"}` | 화면과 API가 같은 문구를 씀 |
| D-6 | 없는 코드 404 | API와 화면 구분 없이 HTML 404 | 같은 경로 `GET /{code}`이고 AC-11은 상태 코드만 요구 |
| D-7 | 폼 입력칸 | `type="text"` + `inputmode="url"`, `required` 없음 | 브라우저가 먼저 막으면 서버 오류 화면(AC-19)을 볼 수 없음 |
| D-8 | `created_at` | 초 단위, `Z` 접미사 | 설계서 예시 `2026-10-29T01:23:45Z`와 같은 형식 |
| D-9 | 거절 조건 목록 (리뷰 1라운드 M-1 = R-1/S-1/Q-1 통합, 사람 결정) | 짝 없는 서로게이트처럼 UTF-8로 인코딩할 수 없는 문자가 든 URL은 새 문구 `MSG_INVALID_ENCODING`으로 422 | JSON `\ud800`이 검증을 통과해 SQLite 바인딩에서 500이 남. 422로 거절해야 계약에 맞음 |
| D-10 | (설계서에 없음, 리뷰 1라운드 S-3, 사람 결정) | 우리 HTML 화면에 CSP `default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`, 모든 응답에 `X-Content-Type-Options: nosniff` | 방어 심화. `/docs`, `/redoc`은 CDN 자원을 쓰므로 CSP를 붙이지 않음 |
| D-11 | 복사 실패 안내 (리뷰 1라운드 R-2, 사람 결정) | `navigator.clipboard`가 없으면 바로 실패 문구 표시 | 비보안 HTTP 배포에서 안내가 사라지는 문제 방지 |

## 6. 작업 분담

- implementer: `src/shortlink/**` 스텁 구현, 템플릿 4개, `style.css`, `copy.js`.
- test-writer: 4절의 테스트 파일. `conftest.py`는 확장만(예: DB 행 수를 세는 헬퍼 픽스처).
