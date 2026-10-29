# F1 구현 계획 — 단축 URL 생성과 리다이렉트

- 기준 설계서: `docs/features/F1.md` v2
- 설계서 해석 결정: `docs/plans/F1-decisions.md`
- 화면 목업: `docs/plans/mockups/F1-index.html`

## 1. 구현 범위

- JSON API: `POST /links`(생성), `GET /{code}`(리다이렉트)
- 웹 화면: `GET /`(홈), `POST /`(결과 또는 입력 오류), 없는 코드의 `GET /{code}`(찾을 수 없음)
- 저장: `Settings.db_path`의 SQLite, 표준 라이브러리 `sqlite3`
- 범위 밖: 별칭, 통계, 인증, 만료, 삭제, 목록 조회, URL 정규화

## 2. 모듈 구조

| 파일 | 역할 |
|---|---|
| `src/shortlink/main.py` | `create_app()`: 저장소 생성과 스키마 준비, 라우터 등록(api → web 순서), `/static` 마운트 |
| `src/shortlink/codes.py` | 단축 코드 생성 (`secrets` 기반) |
| `src/shortlink/validation.py` | URL 검증 규칙 (API와 폼이 같이 씀) |
| `src/shortlink/storage.py` | SQLite 저장소 (`Link`, `LinkRepository`) |
| `src/shortlink/api.py` | JSON API 라우터 (`POST /links`) |
| `src/shortlink/web.py` | 웹 화면 라우터 (`GET /`, `POST /`, `GET /{code}`)와 Jinja2 템플릿 객체 |
| `src/shortlink/templates/base.html` | 공통 레이아웃 (`<html lang="ko">`, viewport meta, CSS 링크) |
| `src/shortlink/templates/home.html` | 홈과 입력 오류 화면 |
| `src/shortlink/templates/result.html` | 결과 화면 |
| `src/shortlink/templates/not_found.html` | 찾을 수 없음 화면 |
| `src/shortlink/static/style.css` | 목업과 같은 스타일 |
| `src/shortlink/static/copy.js` | "복사" 버튼 동작 |

라우터 등록 순서: `/{code}`가 `/links`와 `/static`을 가로채지 않도록 `/static` 마운트와 api 라우터를 먼저 등록하고 web 라우터를 마지막에 등록한다. `GET /{code}`는 경로 매개변수 한 단계만 받는다.

## 3. 인터페이스

### codes.py

```python
CODE_ALPHABET: str  # string.ascii_letters + string.digits (62자)
CODE_LENGTH = 7

def generate_code(length: int = CODE_LENGTH) -> str:
    """secrets.choice로 CODE_ALPHABET에서 length자를 뽑아 돌려준다."""
```

### validation.py

```python
MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = frozenset({"http", "https"})

class URLValidationError(ValueError):
    """검증 실패. message 속성에 사용자에게 보여 줄 한국어 문구를 담는다."""
    message: str

def validate_url(value: object) -> str:
    """검증을 통과하면 value를 바꾸지 않고 그대로 돌려준다. 실패하면 URLValidationError."""
```

검사 순서와 오류 문구 (화면과 API 모두 같은 문구):

| 순서 | 조건 | 문구 |
|---|---|---|
| 1 | 값이 없음(`None`) 또는 빈 문자열 | `URL을 입력해 주세요.` |
| 2 | 문자열이 아님 | `URL은 문자열이어야 합니다.` |
| 3 | 길이 > 2,048 (파이썬 문자 수) | `URL은 2,048자를 넘을 수 없습니다.` |
| 4 | 공백 문자나 제어 문자 포함 (결정 D-2) | `URL에 공백이나 제어 문자를 넣을 수 없습니다.` |
| 4-1 | 서로게이트 문자(U+D800~U+DFFF) 포함 (결정 D-10) | `URL에 쓸 수 없는 문자가 있습니다.` |
| 5 | 스킴이 `http`, `https`가 아님 (대소문자 무시, 결정 D-1) | `http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.` |
| 6 | 호스트가 없음 (`urlsplit(value).hostname`이 비었음) | `URL에 호스트(도메인)가 없습니다.` |

정규화는 하지 않는다. 앞뒤 공백도 지우지 않는다(공백이 있으면 4번으로 거절).

### storage.py

```python
@dataclass(frozen=True)
class Link:
    code: str
    url: str
    created_at: str  # UTC ISO 8601, 초 단위, 'Z' 접미사. 예: 2026-10-29T01:23:45Z

class LinkRepository:
    MAX_CODE_ATTEMPTS = 10

    def __init__(self, db_path: str) -> None: ...
    def init_schema(self) -> None:
        """links 테이블이 없으면 만든다. 여러 번 불러도 안전하다."""
    def create(self, url: str) -> Link:
        """새 코드로 링크를 저장한다. 코드가 겹치면(IntegrityError) 다시 만든다.
        MAX_CODE_ATTEMPTS번 모두 겹치면 RuntimeError."""
    def get(self, code: str) -> Link | None: ...
    def count(self) -> int:
        """저장된 링크 수."""
```

스키마:

```sql
CREATE TABLE IF NOT EXISTS links (
    code TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    created_at TEXT NOT NULL
)
```

- 연결은 메서드 호출마다 열고 닫는다(`contextlib.closing(sqlite3.connect(db_path))`, 쓰기는 커밋). 모든 쿼리는 `?` 파라미터 바인딩을 쓴다.
- `create_app()`은 `LinkRepository(settings.db_path)`를 만들어 `init_schema()`를 부르고 `app.state.repository`에 둔다.

### api.py

```python
router = APIRouter()

@router.post("/links", status_code=201)
async def create_link(request: Request) -> JSONResponse: ...
```

- 본문을 직접 읽는다(`await request.json()`). JSON이 아니거나 객체가 아니면 422.
- `body.get("url")`을 `validate_url`에 넘긴다. 실패하면 422 `{"detail": "<오류 문구>"}`.
- 성공하면 201 `{"code", "short_url", "url", "created_at"}`. `short_url = f"{settings.base_url}/{code}"`.

### web.py

```python
router = APIRouter()
templates: Jinja2Templates  # directory=TEMPLATES_DIR, 자동 이스케이프 켜짐(기본값)

@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse: ...

@router.post("/", response_class=HTMLResponse)
async def shorten_from_form(request: Request) -> HTMLResponse: ...

@router.get("/{code}")
async def follow(request: Request, code: str) -> Response: ...
```

- `POST /`: `await request.form()`에서 `url`을 꺼낸다(없으면 `None`). 검증 실패면 `home.html`을 422로, `error`와 `url_value`(제출한 값, 없으면 빈 문자열)를 넘긴다. 성공하면 `result.html`을 200으로, `short_url`과 `url`을 넘긴다.
- `GET /{code}`: 있으면 `302`, `Location`은 저장된 URL. 비ASCII 문자만 UTF-8 퍼센트 인코딩하고 ASCII 문자는 그대로 둔다(결정 D-3). `RedirectResponse`의 기본 인용(`quote`)은 쓰지 않는다. 없으면 `not_found.html`을 404로.
- 템플릿 컨텍스트 이름: `home.html`(`error: str | None`, `url_value: str`), `result.html`(`short_url`, `url`), `not_found.html`(없음).
- `|safe`, `Markup`은 쓰지 않는다.

## 4. 화면 목록

목업이 문구, 배치, 색의 기준이다. 템플릿은 목업의 마크업 구조(클래스 이름 포함)와 문구를 그대로 따른다.

| 화면 | 경로와 상태 | 목업 | 템플릿 |
|---|---|---|---|
| 홈 | `GET /` → 200 | `mockups/F1-home.html` | `home.html` |
| 결과 | `POST /` 성공 → 200 | `mockups/F1-result.html` | `result.html` |
| 입력 오류 | `POST /` 실패 → 422 | `mockups/F1-error.html` | `home.html` (error 포함) |
| 찾을 수 없음 | 없는 코드 `GET /{code}` → 404 | `mockups/F1-not-found.html` | `not_found.html` |

고정 문구:

| 위치 | 문구 |
|---|---|
| 서비스 이름 (헤더, 모든 화면) | `ShortLink` (홈으로 가는 링크) |
| 홈 한 줄 설명 | `긴 URL을 짧고 공유하기 쉬운 링크로 바꿔 드립니다.` |
| 입력칸 label | `줄일 URL` |
| 입력칸 placeholder | `https://example.com/very/long/path` |
| 제출 버튼 | `줄이기` |
| 결과 제목 | `단축 URL을 만들었습니다` |
| 결과 항목 이름 | `단축 URL`, `원래 URL` |
| 복사 버튼 | `복사` (복사 후 2초 동안 `복사됨`) |
| 결과 하단 링크 | `다른 URL 줄이기` (`href="/"`) |
| 찾을 수 없음 제목 | `링크를 찾을 수 없습니다` |
| 찾을 수 없음 설명 | `주소가 잘못되었거나 없는 단축 코드입니다.` |
| 찾을 수 없음 링크 | `홈으로 가기` (`href="/"`) |
| `<title>` | 홈·오류 `ShortLink`, 결과 `단축 URL 결과 - ShortLink`, 없음 `링크를 찾을 수 없음 - ShortLink` |

마크업 요점:

- 폼: `<form method="post" action="/">`, `<label for="url">줄일 URL</label>`, `<input id="url" name="url" type="text" ...>`(브라우저 자체 검증이 서버 오류 화면을 가리지 않도록 `type="url"`과 `required`를 쓰지 않는다), `<button type="submit">줄이기</button>`
- 오류: 입력칸 위에 `<p class="error" role="alert">…</p>`, 입력칸에 `aria-invalid="true"`와 `aria-describedby`
- 결과: 단축 URL은 `<a class="short-url" href="{{ short_url }}">{{ short_url }}</a>`, 원래 URL은 링크가 아닌 텍스트(`<p class="original-url">`, 긴 URL은 줄바꿈). 복사 버튼은 `<button type="button" class="copy-button" data-copy="{{ short_url }}">복사</button>`. 스크립트는 `<script src="/static/copy.js" defer></script>`
- 모든 화면: `<html lang="ko">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<link rel="stylesheet" href="/static/style.css">`
- 375px 폭에서 가로 스크롤 없음: `box-sizing: border-box`, 긴 URL에 `overflow-wrap: anywhere`

## 5. 수용 기준과 테스트 대응

테스트 파일 제안: `tests/test_api.py`(AC-1~AC-15), `tests/test_web.py`(AC-16~AC-23). 저장 여부(AC-9, AC-19)는 `settings.db_path`의 `links` 테이블 행 수를 `sqlite3`로 직접 세어 확인한다.

| 수용 기준 | 검증 방법 |
|---|---|
| AC-1 | `POST /links` 정상 URL → 201, 네 필드 존재 |
| AC-2 | `code`가 `^[A-Za-z0-9]{7}$`, `short_url == "http://testserver/" + code` |
| AC-3 | 응답 `url` == 요청 URL (쿼리 포함, 대문자 섞인 URL 포함) |
| AC-4 | `http://example.com` → 201 |
| AC-5 | `ftp://example.com`, `javascript:alert(1)`, `data:text/html,hi`, `mailto:a@example.com` 각각 422 (parametrize) |
| AC-6 | 본문 `{}`, `{"url": 123}`, `{"url": ""}` 각각 422 |
| AC-7 | `https://` → 422 |
| AC-8 | 정확히 2,048자 URL → 201, 2,049자 → 422 |
| AC-9 | AC-5~AC-8 거절 요청 뒤 행 수 0 |
| AC-10 | 생성 후 `GET /{code}`(리다이렉트 따라가지 않음) → 302, `Location` == 원래 URL |
| AC-11 | `GET /zzzzzzz` → 404 |
| AC-12 | 같은 URL 두 번 → 코드 다름, 둘 다 302와 같은 `Location` |
| AC-13 | 100번 생성 → 코드 100개 모두 다름 |
| AC-14 | 같은 `settings`로 `create_app`을 다시 불러 새 클라이언트로 `GET /{code}` → 302 |
| AC-15 | `created_at`이 `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`, 파싱한 값과 현재 UTC 차이 < 60초 |
| AC-16 | `GET /` → 200, `text/html`, `<form method="post" action="/">`, `<label for="url">`, `name="url"`, `줄이기` 버튼 |
| AC-17 | 폼 제출 → 200, `href="<short_url>"` 링크, 원래 URL 텍스트 |
| AC-18 | 결과 화면에 `복사` 버튼, `href="/"`인 `다른 URL 줄이기` 링크 |
| AC-19 | 잘못된 URL 폼 제출 → 422 HTML, 오류 문구, `value="<제출값>"`, 행 수 0 |
| AC-20 | `https://example.com/?q=<script>alert(1)</script>` 결과 화면, `javascript:<script>alert(1)</script>` 오류 화면 → 응답에 `<script>alert(1)</script>` 원문 없음, `&lt;script&gt;` 있음 |
| AC-21 | 없는 코드 → 404, `text/html`, `링크를 찾을 수 없습니다`, `href="/"` |
| AC-22 | 홈, 결과, 오류, 없음 화면 모두 `<html lang="ko">`와 `name="viewport"` |
| AC-23 | 폼 결과 HTML에서 코드를 꺼내 `GET /{code}` → 302, 원래 URL |

추가로 결정 사항(D-1~D-3) 확인 테스트: 대문자 스킴(`HTTPS://example.com`) 허용, 공백 포함 URL 422, 비ASCII URL 리다이렉트 시 퍼센트 인코딩.

## 6. 작업 분담

- implementer: `src/shortlink/**` 스텁 채우기, 템플릿, CSS, JS
- test-writer: `tests/test_api.py`, `tests/test_web.py` (필요하면 `conftest.py` 확장)
