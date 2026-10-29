# F1 구현 계획 — 단축 URL 생성과 리다이렉트

- 설계서: `docs/features/F1.md` (v2)
- 해석 결정: `docs/plans/F1-decisions.md`
- 화면 목업: `docs/plans/mockups/F1-index.html`

## 1. 구현 범위

- JSON API: `POST /links`(생성), `GET /{code}`(리다이렉트)
- 웹 화면: `GET /`(홈), `POST /`(결과 또는 입력 오류), 없는 코드의 `GET /{code}`(찾을 수 없음)
- SQLite 저장(`sqlite3`, ORM 없음), `create_app()`에서 스키마 준비
- 범위 밖: 별칭, 통계, 인증, 만료, 삭제, 요청 수 제한, URL 정규화, 링크 목록

## 2. 모듈 구조

```
src/shortlink/
  main.py         (고정 계약) create_app: StaticFiles 마운트, init_db, 라우터 등록
  config.py       (고정 계약) 변경 없음
  db.py           스키마 준비와 연결
  codes.py        무작위 7자 코드 생성
  validation.py   URL 검증 규칙(API와 웹이 공유)
  links.py        링크 저장/조회 서비스
  api.py          JSON API 라우터 (POST /links)
  web.py          웹 화면 라우터 (GET /, POST /, GET /{code})
  templates/
    base.html       공통 레이아웃 (<html lang="ko">, viewport meta, /static/style.css)
    home.html       홈 + 입력 오류
    result.html     결과
    not_found.html  찾을 수 없음
  static/
    style.css       목업의 CSS를 옮긴 것
    copy.js         "복사" 버튼 동작
```

### 라우트 등록 순서 (중요)

`GET /{code}`는 경로 한 단계를 모두 받으므로 마지막에 등록한다. 순서:
`/static` 마운트 → api 라우터(`POST /links`) → web 라우터(`GET /`, `POST /`, `GET /{code}`).
FastAPI 기본 경로(`/openapi.json`, `/docs`, `/redoc`)는 앱 생성 시 먼저 등록되므로 가려지지 않는다.

## 3. 인터페이스

### db.py

```python
SCHEMA: str  # CREATE TABLE IF NOT EXISTS links (...)
def init_db(db_path: str) -> None: ...          # 스키마 준비(멱등)
def connect(db_path: str) -> sqlite3.Connection: ...  # 새 연결, 호출자가 닫음
```

스키마 (테스트가 AC-9 확인에 직접 사용하므로 이름 고정):

```sql
CREATE TABLE IF NOT EXISTS links (
    code       TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

- 모든 쿼리는 `?` 파라미터 바인딩을 쓴다.
- 요청마다 연결을 열고 닫는다(스레드 공유 없음).

### codes.py

```python
CODE_ALPHABET = string.ascii_letters + string.digits  # 62자
CODE_LENGTH = 7
def generate_code(length: int = CODE_LENGTH) -> str: ...  # secrets.choice 사용
```

### validation.py

```python
MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = frozenset({"http", "https"})
class InvalidURLError(ValueError):
    message: str   # 사용자에게 보여 줄 한국어 메시지
def validate_url(value: object) -> str: ...  # 통과하면 value를 그대로 반환, 아니면 InvalidURLError
```

검사 순서와 메시지 (API `detail`과 웹 오류 화면이 같은 문구를 쓴다):

| 순서 | 조건 | 메시지 |
|---|---|---|
| 1 | 값이 없음(None) 또는 빈 문자열 | `URL을 입력해 주세요.` |
| 2 | 문자열이 아님 | `URL은 문자열이어야 합니다.` |
| 3 | 길이 > 2048 | `URL은 2,048자 이하여야 합니다.` |
| 4 | 공백 또는 제어 문자(0x00–0x20, 0x7F) 포함 | `URL에 공백이나 제어 문자를 넣을 수 없습니다.` |
| 5 | `urlsplit` 실패(ValueError), 잘못된 포트 | `올바른 URL 형식이 아닙니다.` |
| 6 | 스킴이 http/https가 아님(대소문자 무시) | `http:// 또는 https://로 시작하는 URL만 줄일 수 있습니다.` |
| 7 | 호스트 없음(`hostname`이 비었음) | `URL에 호스트(도메인)가 없습니다.` |

- 정규화하지 않는다. 통과한 문자열을 그대로 저장한다.

### links.py

```python
@dataclass(frozen=True)
class Link:
    code: str
    url: str
    created_at: str   # "YYYY-MM-DDTHH:MM:SSZ" (UTC, 초 단위)

MAX_CODE_ATTEMPTS = 10
class CodeGenerationError(RuntimeError): ...
def utc_now_iso() -> str: ...
def create_link(db_path: str, url: str) -> Link: ...   # 검증은 호출 전에 끝낸 상태
def get_link(db_path: str, code: str) -> Link | None: ...
def short_url_for(base_url: str, code: str) -> str: ...  # f"{base_url}/{code}"
```

- 코드 충돌은 `INSERT`의 `IntegrityError`로 감지해 다시 만든다(최대 10회, 넘으면 `CodeGenerationError`).
- `get_link`는 코드 형식(영숫자 7자)이 아니면 DB 조회 없이 `None`.

### api.py

```python
router = APIRouter()
@router.post("/links", status_code=201)  # 성공: {"code","short_url","url","created_at"}
```

- 본문을 직접 JSON으로 읽는다(`await request.json()`). JSON이 깨졌거나 객체가 아니면 422.
- 422 응답 본문: `{"detail": "<위 표의 메시지>"}` (JSON이 깨졌거나 객체가 아니면 `요청 본문은 JSON 객체여야 합니다.`)
- 거절 시 아무것도 저장하지 않는다.

### web.py

```python
router = APIRouter()
templates: Jinja2Templates  # TEMPLATES_DIR, autoescape 켜짐(기본값)
@router.get("/", response_class=HTMLResponse)          # home.html, 200
@router.post("/", response_class=HTMLResponse)         # 성공 result.html 200, 실패 home.html 422
@router.get("/{code}")                                 # 302 RedirectResponse 또는 not_found.html 404
```

- 폼 필드 `url`이 없으면 빈 문자열로 보고 검증(→ "URL을 입력해 주세요.").
- 리다이렉트 `Location`: 저장된 URL. ASCII가 아닌 문자가 있으면 그 문자만 UTF-8 퍼센트 인코딩한다(HTTP 헤더는 latin-1만 허용). ASCII URL은 글자 그대로.
- 없는 코드는 API·브라우저 구분 없이 `404` HTML(찾을 수 없음 화면).
- 템플릿에는 `|safe`, `Markup`을 쓰지 않는다.

## 4. 화면 목록

| 화면 | 경로 | 템플릿 | 상태 | 목업 |
|---|---|---|---|---|
| 홈 | `GET /` | home.html | 200 | `mockups/F1-home.html` |
| 결과 | `POST /` 성공 | result.html | 200 | `mockups/F1-result.html` |
| 입력 오류 | `POST /` 실패 | home.html (error, 입력값 유지) | 422 | `mockups/F1-error.html` |
| 찾을 수 없음 | 없는 코드 `GET /{code}` | not_found.html | 404 | `mockups/F1-not-found.html` |

목업의 문구, 요소 구조(class, id, aria 속성), 색을 그대로 따른다. CSS는 목업의 `<style>` 내용을 `static/style.css`로 옮긴다. "복사" 버튼 스크립트는 인라인이 아니라 `static/copy.js`로 둔다.

## 5. 수용 기준과 테스트 대응

테스트 파일: `tests/test_api.py`(AC-1~15), `tests/test_web.py`(AC-16~23), 필요하면 `tests/test_validation.py`(단위).

| AC | 내용 | 테스트(예정) |
|---|---|---|
| AC-1 | POST /links 201과 4개 필드 | test_api: 생성 성공 응답 필드 |
| AC-2 | code 영숫자 7자, short_url = base_url/code | test_api: code 형식, short_url |
| AC-3 | url 글자 그대로 | test_api: 쿼리·대소문자·인코딩 포함 URL 그대로 반환 |
| AC-4 | http:// 허용 | test_api: http URL 201 |
| AC-5 | ftp/javascript/data/mailto 422 | test_api: parametrize 4건 |
| AC-6 | 필드 없음/숫자/빈 문자열 422 | test_api: parametrize (+null, 리스트, 깨진 JSON) |
| AC-7 | `https://` 422 | test_api |
| AC-8 | 2048자 201, 2049자 422 | test_api: 경계값 |
| AC-9 | 거절 시 저장 없음 | test_api: 거절 후 `links` 행 수 0 (sqlite3 직접 조회) |
| AC-10 | 302 + Location | test_api: `follow_redirects=False` |
| AC-11 | 없는 코드 404 | test_api |
| AC-12 | 같은 URL 두 번 → 다른 코드, 둘 다 리다이렉트 | test_api |
| AC-13 | 100회 연속 생성 코드 모두 다름 | test_api |
| AC-14 | 같은 db_path로 앱 재생성 후 리다이렉트 | test_api: `create_app(settings)` 두 번 |
| AC-15 | created_at UTC ISO 8601, 1분 이내 | test_api: 정규식 `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` + 시각 차 |
| AC-16 | GET / 폼, label, name=url, "줄이기" | test_web |
| AC-17 | 폼 제출 성공 200, 단축 URL href 링크, 원래 URL | test_web |
| AC-18 | "복사" 버튼, "다른 URL 줄이기" href="/" | test_web |
| AC-19 | 잘못된 URL 422 HTML, 오류 메시지, 입력값 유지, 저장 없음 | test_web |
| AC-20 | `<script>` 이스케이프 (결과·오류 화면) | test_web |
| AC-21 | 없는 코드 404 HTML, 안내 문구, 홈 링크 | test_web |
| AC-22 | 모든 화면 `lang="ko"` + viewport meta | test_web: 4개 화면 |
| AC-23 | 폼으로 만든 코드도 리다이렉트 | test_web |

## 6. 작업 분담

- implementer: `src/shortlink/**` (스텁 구현, `main.py` 확장, 템플릿, CSS, JS)
- test-writer: `tests/**` (위 대응표 기준, 스텁 인터페이스와 목업 문구 기준)
