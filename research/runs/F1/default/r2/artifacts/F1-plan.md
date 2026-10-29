# F1 구현 계획 — 단축 URL 생성과 리다이렉트

- 기준 설계서: `docs/features/F1.md` v2 (2026-10-29 확정)
- 화면 목업: `docs/plans/mockups/F1-index.html` (구현과 테스트의 문구·배치·색 기준)
- 설계서 해석 결정: 이 문서 7절 (실행 중 생기는 결정은 `docs/plans/F1-decisions.md`)

## 1. 구현 범위

| 구분 | 내용 |
|---|---|
| JSON API | `POST /links` 생성 (201 / 422) |
| 리다이렉트 | `GET /{code}` → 302 `Location` / 없으면 404 HTML 화면 |
| 웹 화면 | `GET /` 홈, `POST /` 결과(200)·입력 오류(422), 찾을 수 없음(404) |
| 저장 | SQLite 파일(`Settings.db_path`), 표준 라이브러리 `sqlite3`, ORM 없음 |

범위 밖: 별칭, 통계, 인증, 만료, 삭제, 요청 수 제한, URL 정규화, 중복 합치기, 목록 조회.

## 2. 모듈 구조

```
src/shortlink/
  main.py          (고정 계약) create_app: DB 스키마 준비, 저장소 생성, 라우터 등록
  config.py        (고정 계약) 변경 없음
  codes.py         단축 코드 생성, 단축 URL 조립
  validation.py    URL 검증 규칙 (API와 화면이 함께 씀)
  db.py            SQLite 연결과 스키마
  repository.py    Link 데이터 클래스, LinkRepository (저장·조회·충돌 재시도)
  schemas.py       API 요청/응답 Pydantic 모델
  deps.py          app.state에서 Settings, LinkRepository를 꺼내는 의존성
  api.py           APIRouter: POST /links
  web.py           APIRouter: GET /, POST /, GET /{code}
  templates/
    base.html      공통 뼈대 (lang="ko", viewport, CSS, 헤더)
    home.html      홈 + 입력 오류 (error, url 변수)
    result.html    결과
    not_found.html 찾을 수 없음
  static/
    style.css      목업의 CSS를 옮긴 것
    copy.js        "복사" 버튼 동작
```

라우터 등록 순서: `/static` 마운트 → `api.router` → `web.router`. `GET /{code}`는 마지막에 등록되어 다른 경로를 가리지 않게 한다.

## 3. 인터페이스

스켈레톤은 `src/shortlink/`에 시그니처와 docstring만 있는 스텁으로 만들어 두었다. 요약:

### codes.py
- `CODE_LENGTH = 7`, `CODE_ALPHABET = string.ascii_letters + string.digits`
- `generate_code() -> str`: `secrets`로 만든 7자 무작위 코드
- `is_valid_code(code: str) -> bool`: 7자 영숫자인지
- `build_short_url(base_url: str, code: str) -> str`: `f"{base_url}/{code}"` (base_url은 Settings가 끝 `/`를 이미 제거)

### validation.py
- `MAX_URL_LENGTH = 2048`, `ALLOWED_SCHEMES = frozenset({"http", "https"})`
- `class InvalidURLError(ValueError)`: `message` 속성에 화면/API에 보일 한국어 문구
- `validate_url(value: object) -> str`: 검증 통과 시 **받은 값 그대로** 반환, 실패 시 `InvalidURLError`
- 검사 순서와 문구 (화면 오류 메시지로도 그대로 씀):

  | 순서 | 조건 | 문구 |
  |---|---|---|
  | 1 | 문자열이 아님 | `URL은 문자열이어야 합니다.` |
  | 2 | 빈 문자열 | `URL을 입력해 주세요.` |
  | 3 | 2,048자 초과 (`len(value) > 2048`) | `URL은 2,048자 이하여야 합니다.` |
  | 4 | 공백·제어 문자 포함 (결정 D-3) | `URL에 공백이나 제어 문자를 넣을 수 없습니다.` |
  | 5 | 스킴이 http/https 아님 (대소문자 무시) | `http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.` |
  | 6 | 호스트 없음 (`urlsplit(value).hostname`이 비어 있음) | `URL에 호스트(도메인)가 없습니다.` |

### db.py
- `SCHEMA`: `CREATE TABLE IF NOT EXISTS links (code TEXT PRIMARY KEY, url TEXT NOT NULL, created_at TEXT NOT NULL)`
- `connect(db_path: str) -> sqlite3.Connection`
- `init_db(db_path: str) -> None`: 스키마 준비 (여러 번 호출해도 안전)

### repository.py
- `@dataclass(frozen=True) Link(code: str, url: str, created_at: datetime)` — `created_at`은 UTC aware datetime
- `format_timestamp(dt: datetime) -> str`: `YYYY-MM-DDTHH:MM:SSZ` (초 단위, UTC)
- `class CodeGenerationError(RuntimeError)`
- `class LinkRepository(db_path: str, code_generator: Callable[[], str] = generate_code, max_attempts: int = 10)`
  - `create(url: str) -> Link`: 코드를 만들어 저장. PK 충돌(`sqlite3.IntegrityError`)이면 새 코드로 재시도, `max_attempts`번 모두 충돌하면 `CodeGenerationError`. 검증은 하지 않는다(호출 측 책임).
  - `get(code: str) -> Link | None`
  - `count() -> int`: 저장된 링크 수 (AC-9 검증용)
- 모든 쿼리는 파라미터 바인딩(`?`)을 쓴다. 호출마다 연결을 열고 닫는다.

### schemas.py
- `LinkCreate(BaseModel)`: `url: StrictStr`, `field_validator("url")`에서 `validate_url` 호출 → 실패 시 `ValueError(message)`. 결과적으로 모든 API 검증 실패는 FastAPI 표준 422(`{"detail": [...]}`)로 나간다.
- `LinkOut(BaseModel)`: `code`, `short_url`, `url`, `created_at: str`

### api.py
- `router = APIRouter()`
- `POST /links` → `create_link(payload: LinkCreate, request: Request) -> LinkOut`, `status_code=201`

### web.py
- `router = APIRouter()`, `templates = Jinja2Templates(directory=TEMPLATES_DIR)` (자동 이스케이프 켜짐)
- `GET /` → `home(request)`: `home.html`, 200
- `POST /` → `submit(request, url: str = Form(""))`: 성공 시 `result.html` 200, 실패 시 `home.html` 422 (`error`, `url` 전달)
- `GET /{code}` → `follow(request, code)`: 있으면 `RedirectResponse(url, status_code=302)`, 없으면 `not_found.html` 404. `is_valid_code`가 거짓이면 DB 조회 없이 404.

### main.py (확장)
- `create_app`: `init_db(settings.db_path)` → `app.state.repository = LinkRepository(settings.db_path)` → `include_router(api.router)` → `include_router(web.router)`
- `app.state.settings`와 `app.state.repository`는 라우터에서 `deps.py`의 의존성 함수로 꺼낸다 (순환 import 방지).

### deps.py
- `get_settings(request: Request) -> Settings`
- `get_repository(request: Request) -> LinkRepository`
- 타입 별칭 `SettingsDep`, `RepositoryDep` (`Annotated[..., Depends(...)]`, ruff B008 회피)

참고: 검증 문구는 `validation.py`의 상수 `MSG_NOT_STRING`, `MSG_EMPTY`, `MSG_TOO_LONG`, `MSG_WHITESPACE`, `MSG_SCHEME`, `MSG_NO_HOST`로 둔다. 테스트는 이 상수나 위 표의 문구로 확인한다.

## 4. 화면 목록

| 화면 | 경로/상태 | 템플릿 | 목업 |
|---|---|---|---|
| 홈 | `GET /` 200 | `home.html` | `mockups/F1-home.html` |
| 결과 | `POST /` 성공 200 | `result.html` | `mockups/F1-result.html` |
| 입력 오류 | `POST /` 실패 422 | `home.html` (error 있음) | `mockups/F1-input-error.html` |
| 찾을 수 없음 | 없는 코드 `GET /{code}` 404 | `not_found.html` | `mockups/F1-not-found.html` |

화면 공통 규칙 (목업과 동일하게 구현):

- `<html lang="ko">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<meta charset="utf-8">`
- 헤더: `<a href="/" class="brand">ShortLink</a>`
- 본문 카드 최대 폭 560px, 좌우 여백 16px. 긴 URL은 `overflow-wrap: anywhere`로 줄바꿈해 375px에서도 가로 스크롤 없음
- 홈 문구: 제목 `ShortLink`, 설명 `긴 URL을 짧고 공유하기 쉬운 링크로 바꿔 드립니다.`, 라벨 `줄일 URL`, 도움말 `http:// 또는 https://로 시작하는 2,048자 이하의 주소를 넣어 주세요.`, 버튼 `줄이기`
- 입력칸: `<input id="url" name="url" type="text" inputmode="url" autocomplete="off">` (브라우저 검증 대신 서버 검증 문구를 보이기 위해 `type="url"`과 `required`를 쓰지 않음)
- 입력 오류: 폼 위 `<p class="error" id="url-error" role="alert">문구</p>`, 입력칸에 `aria-invalid="true" aria-describedby="url-error"`, `value`에 제출 값
- 결과: 제목 `단축 URL을 만들었습니다`, `<a id="short-url" href="{short_url}">{short_url}</a>`, `<button type="button" class="copy-button" data-copy="{short_url}">복사</button>`, 라벨 `원래 URL`과 원래 URL(텍스트, 링크 아님), `<a href="/">다른 URL 줄이기</a>`. 복사 성공 시 버튼 문구가 2초간 `복사됨`, 실패 시 `복사 실패`
- 찾을 수 없음: 제목 `링크를 찾을 수 없습니다`, 설명 `주소가 정확한지 확인해 주세요. 단축 코드는 대소문자를 구분합니다.`, `<a href="/">홈으로 가기</a>`
- `<title>`: 홈·입력 오류 `ShortLink`, 결과 `단축 URL 결과 - ShortLink`, 찾을 수 없음 `링크를 찾을 수 없음 - ShortLink`

## 5. 수용 기준과 테스트 대응

| 수용 기준 | 테스트 파일 | 검증 내용 |
|---|---|---|
| AC-1 | `tests/test_api_links.py` | 201, 네 필드 존재 |
| AC-2 | `tests/test_api_links.py` | 코드 `^[A-Za-z0-9]{7}$`, `short_url == f"{settings.base_url}/{code}"` |
| AC-3 | `tests/test_api_links.py` | 쿼리·대소문자·끝 공백 없는 특수문자 포함 URL이 글자 그대로 돌아옴 |
| AC-4 | `tests/test_api_links.py` | `http://` 201 |
| AC-5 | `tests/test_api_links.py` | 네 스킴 각각 422 (parametrize) |
| AC-6 | `tests/test_api_links.py` | 필드 없음, 숫자, `null`, 빈 문자열 422 |
| AC-7 | `tests/test_api_links.py` | `https://` 422 |
| AC-8 | `tests/test_api_links.py` | 정확히 2,048자 201, 2,049자 422 |
| AC-9 | `tests/test_api_links.py`, `tests/test_web.py` | 거절 뒤 저장 수 0 (`app.state.repository.count()` 또는 sqlite 직접 조회) |
| AC-10 | `tests/test_redirect.py` | 302, `Location` 같음 (`follow_redirects=False`) |
| AC-11 | `tests/test_redirect.py` | 없는 코드 404 |
| AC-12 | `tests/test_redirect.py` | 같은 URL 두 번 → 코드 다름, 둘 다 302 |
| AC-13 | `tests/test_api_links.py` | 100회 생성 코드 모두 다름 |
| AC-14 | `tests/test_redirect.py` | 같은 settings로 `create_app` 다시 만들어 302 |
| AC-15 | `tests/test_api_links.py` | `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`, 요청 시각과 60초 이내 |
| AC-16 | `tests/test_web.py` | 200, `text/html`, form method/action, label for=url, name="url", "줄이기" |
| AC-17 | `tests/test_web.py` | 200, `href="<short_url>"`, 원래 URL 표시 |
| AC-18 | `tests/test_web.py` | "복사" 버튼, `href="/"` "다른 URL 줄이기" |
| AC-19 | `tests/test_web.py` | 422 HTML, 오류 문구, `value`에 제출 값, 저장 수 0 |
| AC-20 | `tests/test_web.py` | `https://example.com/<script>alert(1)</script>` 결과·오류 화면 모두 `<script>alert(1)` 원문 없음, `&lt;script&gt;` 있음 |
| AC-21 | `tests/test_web.py` | 404 HTML, `링크를 찾을 수 없습니다`, `href="/"` |
| AC-22 | `tests/test_web.py` | 네 화면 모두 `<html lang="ko">`, viewport meta |
| AC-23 | `tests/test_web.py` | 폼으로 만든 코드 → `GET /{code}` 302 |
| 보조 | `tests/test_validation.py` | `validate_url` 단위 테스트 (문구 포함) |
| 보조 | `tests/test_repository.py` | 충돌 재시도(고정 코드 생성기 주입), 재시도 한도 초과 시 `CodeGenerationError` |

## 6. 작업 분담

- implementer: `src/shortlink/**` (스텁 구현, 템플릿, `static/style.css`, `static/copy.js`)
- test-writer: `tests/**` (위 5절 대응표 기준)

## 7. 설계서 해석 결정

| id | 설계서 문장 | 결정 | 이유 |
|---|---|---|---|
| D-1 | API 422 응답 본문 형식 미지정 | FastAPI 표준 `{"detail": [...]}` 형식 하나로 통일 (`LinkCreate` 검증기에서 처리) | 필드 누락·타입 오류와 규칙 위반이 같은 형식이 됨 |
| D-2 | `GET /{code}` 404 형식 | 항상 HTML 화면(찾을 수 없음)으로 응답 | 설계서 화면 표가 이 경로를 HTML 화면으로 정의 |
| D-3 | "정규화는 하지 않는다" | 공백(스페이스 포함)이나 ASCII 제어 문자가 든 URL은 422로 거절. 앞뒤 공백도 잘라내지 않고 거절 | 정규화가 아니라 거절이므로 설계서와 충돌하지 않음. 그런 값은 유효한 URL이 아니고 `Location` 헤더에 안전하게 넣을 수 없음 |
| D-4 | 스킴 비교 | 대소문자 무시 (`HTTPS://example.com` 허용, 저장은 받은 그대로) | RFC 3986에서 스킴은 대소문자를 구분하지 않음 |
| D-5 | 길이 단위 | Python `len()` 기준 문자 수 | 설계서가 "자"로 표현 |
| D-6 | `created_at` 정밀도 | 초 단위, `Z` 접미사 (`2026-10-29T01:23:45Z`) | 설계서 예시 형식과 같음 |
| D-7 | 비ASCII 문자가 든 URL | 허용. 리다이렉트 시 Starlette `RedirectResponse`가 `Location`을 퍼센트 인코딩 | HTTP 헤더는 ASCII만 안전. ASCII URL은 그대로 나감(AC-10) |
| D-8 | 폼 필드 누락 | `url` 필드가 없으면 빈 문자열로 보고 `URL을 입력해 주세요.` 422 | API와 같은 규칙 |
| D-9 | 코드 형식이 아닌 `/{code}` (예: `/favicon.ico`) | DB 조회 없이 404 화면 | 7자 영숫자만 코드가 될 수 있음 |
