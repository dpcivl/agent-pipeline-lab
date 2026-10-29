# F1 구현 계획 — 단축 URL 생성과 리다이렉트

- 설계서: `docs/features/F1.md` (v2)
- 해석 결정: `docs/plans/F1-decisions.md`
- 화면 목업: `docs/plans/mockups/F1-index.html`

## 1. 구현 범위

- JSON API: `POST /links` (생성), `GET /{code}` (리다이렉트, 없으면 404 HTML 화면)
- 웹 화면: `GET /` (홈), `POST /` (결과 또는 입력 오류), 찾을 수 없음 화면
- SQLite 저장(`sqlite3`, ORM 없음), `create_app()`에서 스키마 준비
- 범위 밖: 별칭, 통계, 인증, 만료, 삭제, 요청 수 제한, 정규화, 목록 조회

## 2. 모듈 구조

| 파일 | 역할 |
|---|---|
| `src/shortlink/main.py` | (고정 계약, 확장) `create_app()`에서 `db.init_db()` 호출, `api.router` 다음에 `web.router` 등록 |
| `src/shortlink/db.py` | SQLite 연결과 스키마 |
| `src/shortlink/validation.py` | URL 검증 규칙 (API와 웹이 함께 씀) |
| `src/shortlink/links.py` | 코드 생성, 링크 저장과 조회 (서비스 계층) |
| `src/shortlink/api.py` | `POST /links` JSON API |
| `src/shortlink/web.py` | `GET /`, `POST /`, `GET /{code}` (라우터에 마지막으로 등록) |
| `src/shortlink/templates/` | `base.html`, `home.html`, `result.html`, `not_found.html` |
| `src/shortlink/static/` | `style.css`, `copy.js` |

라우트 순서: `/static` 마운트 → `POST /links` → `GET /`, `POST /` → `GET /{code}`. `/{code}`가 다른 경로를 가리지 않도록 반드시 마지막에 등록한다.

## 3. 인터페이스

### 3.1 DB (`db.py`)

```sql
CREATE TABLE IF NOT EXISTS links (
    code       TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    created_at TEXT NOT NULL      -- 'YYYY-MM-DDTHH:MM:SSZ' (UTC)
);
```

- `connect(db_path: str) -> sqlite3.Connection`: 요청마다 새 연결을 열고 쓰고 닫는다.
- `init_db(db_path: str) -> None`: 위 스키마를 만든다. 여러 번 불러도 안전하다.
- 모든 쿼리는 파라미터 바인딩(`?`)을 쓴다.
- 테스트는 `settings.db_path`의 `links` 테이블 행 수를 직접 세어 "아무것도 저장하지 않음"(AC-9, AC-19)을 확인할 수 있다.

### 3.2 검증 (`validation.py`)

- `MAX_URL_LENGTH = 2048`
- `class InvalidURLError(ValueError)`: `message` 속성에 사용자에게 보여 줄 한국어 문구를 담는다.
- `validate_url(value: object) -> str`: 통과하면 `value`를 **그대로** 돌려주고, 아니면 `InvalidURLError`를 던진다.

검사 순서와 오류 문구 (API의 `detail`과 화면의 오류 메시지가 같은 문구를 쓴다):

| 순서 | 조건 | 문구 |
|---|---|---|
| 1 | 값이 없음(`None`) 또는 빈 문자열 | `URL을 입력해 주세요.` |
| 2 | 문자열이 아님 | `URL은 문자열이어야 합니다.` |
| 3 | 길이 > 2,048 | `URL은 2,048자 이하여야 합니다.` |
| 4a | 짝 없는 서로게이트(U+D800–U+DFFF) 포함 (D-8) | `URL에 쓸 수 없는 문자가 들어 있습니다.` |
| 4b | 공백(스페이스)이나 제어 문자(U+0000–U+001F, U+007F) 포함 | `URL에 공백이나 제어 문자를 넣을 수 없습니다.` |
| 5 | 스킴이 `http`/`https`가 아님 (대소문자 무시) | `http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.` |
| 6 | 호스트 없음 (`urlsplit(value).hostname`이 비어 있음) | `URL에 호스트(도메인)가 없습니다.` |

빈 문자열 검사는 1번이 2번보다 먼저다(숫자 `0`처럼 falsy한 비문자열은 2번 문구). 구현은 `value is None or value == ""` → 1번, `not isinstance(value, str)` → 2번 순서로 한다.

### 3.3 서비스 (`links.py`)

- `CODE_LENGTH = 7`, `CODE_ALPHABET = string.ascii_letters + string.digits`
- `@dataclass(frozen=True) class Link: code: str; url: str; created_at: str`
- `generate_code() -> str`: `secrets.choice`로 7자를 만든다.
- `create_link(db_path: str, url: str) -> Link`: 이미 검증된 URL을 저장한다. 코드가 겹치면(`sqlite3.IntegrityError`) 새 코드로 다시 시도하고, 10번 실패하면 `RuntimeError`.
- `get_link(db_path: str, code: str) -> Link | None`
- `utc_now_iso() -> str`: `datetime.now(UTC)`를 `%Y-%m-%dT%H:%M:%SZ`로.
- `short_url(base_url: str, code: str) -> str`: `f"{base_url}/{code}"` (`Settings.base_url`은 끝 슬래시가 이미 제거되어 있다).

### 3.4 JSON API (`api.py`)

`POST /links`
- 본문을 직접 JSON으로 읽는다(`await request.json()`). Pydantic 모델의 자동 형 변환에 기대지 않는다.
- JSON이 아니거나 객체가 아니면 `422` `{"detail": "요청 본문은 JSON 객체여야 합니다."}`
- `validate_url(body.get("url"))` 실패 → `422` `{"detail": "<문구>"}`
- 성공 → `201` `{"code", "short_url", "url", "created_at"}`

### 3.5 웹 (`web.py`)

- `Jinja2Templates(directory=TEMPLATES_DIR)` (자동 이스케이프 켜짐. `|safe`, `Markup` 사용 금지)
- `GET /` → `200` `home.html` (`error=None`, `value=""`)
- `POST /` (폼 `url`, 기본값 `""`으로 받아 필드가 없어도 HTML 422 화면이 되게 함)
  - 성공 → `200` `result.html` (`short_url`, `url`)
  - 실패 → `422` `home.html` (`error=<문구>`, `value=<제출값>`)
- `GET /{code}` → 있으면 `302`, `Location`은 원래 URL에서 비ASCII 문자만 퍼센트 인코딩한 값(D-3), 없으면 `404` `not_found.html`

### 3.6 화면

목업이 문구, 배치, 색의 기준이다. CSS는 목업의 `<style>`을 `static/style.css`로 옮기고, 복사 스크립트는 `static/copy.js`로 옮긴다.

| 화면 | 목업 | 템플릿 | 상태 코드 |
|---|---|---|---|
| 홈 | `mockups/F1-home.html` | `home.html` | 200 |
| 결과 | `mockups/F1-result.html` | `result.html` | 200 |
| 입력 오류 | `mockups/F1-error.html` | `home.html` (+ error) | 422 |
| 찾을 수 없음 | `mockups/F1-not-found.html` | `not_found.html` | 404 |

화면 고정 요소 (테스트가 확인하는 문자열):
- 모든 화면: `<html lang="ko">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `/static/style.css`
- 홈: `<h1>ShortLink</h1>`, 설명 `긴 URL을 붙여 넣으면 짧은 링크로 바꿔 드립니다.`, `<form method="post" action="/">`, `<label for="url">줄일 URL</label>`, `<input id="url" name="url" type="text" ...>`, `<button type="submit" ...>줄이기</button>`
- 결과: `<h1>단축 URL을 만들었습니다</h1>`, `<a ... href="<short_url>">`, 원래 URL 표시, `<button type="button" ... data-copy="<short_url>">복사</button>`, `<a href="/">다른 URL 줄이기</a>`
- 입력 오류: 홈 화면 + `<p class="alert" role="alert" id="url-error">문구</p>`, 입력칸에 `value="<제출값>"`과 `aria-invalid="true"`
- 찾을 수 없음: `<h1>링크를 찾을 수 없습니다</h1>`, `<a href="/">홈으로 가기</a>`

## 4. 수용 기준과 테스트 대응

| AC | 내용 | 테스트 파일(예정) |
|---|---|---|
| AC-1~AC-4 | 생성 응답 형식, 코드 형식, URL 그대로, http 허용 | `tests/test_api_create.py` |
| AC-5~AC-9 | 스킴/필드/호스트/길이 거절, 거절 시 저장 없음 | `tests/test_api_validation.py` |
| AC-10, AC-11 | 302 리다이렉트, 404 | `tests/test_redirect.py` |
| AC-12, AC-13 | 같은 URL 다른 코드, 100개 고유 | `tests/test_api_create.py` |
| AC-14 | 앱 재생성 후 리다이렉트 | `tests/test_persistence.py` |
| AC-15 | `created_at` UTC ISO 8601, 1분 이내 | `tests/test_api_create.py` |
| AC-16~AC-18 | 홈, 결과 화면 | `tests/test_web.py` |
| AC-19~AC-20 | 입력 오류 화면, 이스케이프 | `tests/test_web.py` |
| AC-21~AC-23 | 404 화면, lang/viewport, 폼으로 만든 코드 리다이렉트 | `tests/test_web.py` |

추가로 `validate_url` 단위 테스트(`tests/test_validation.py`)로 경계값(2,048/2,049자, 대문자 스킴, 공백)을 확인한다.
