# F1 구현 계획 — 단축 URL 생성과 리다이렉트

- 설계서: `docs/features/F1.md` (v1 확정)
- 실행 모드: default
- 해석 결정 기록: `docs/plans/F1-decisions.md`

## 1. 구현 범위

- `POST /links`: URL 검증 후 무작위 7자 코드로 저장, `201`과 `code`, `short_url`, `url`, `created_at` 반환
- `GET /{code}`: 있으면 `302` + `Location`, 없으면 `404`
- SQLite(`sqlite3`) 영속화, `create_app()`에서 스키마 준비와 라우터 등록
- 범위 밖: 별칭, 통계, 인증, 만료, 삭제, rate limit, 정규화, 목록 조회, HTML 화면

## 2. 모듈 구조

| 파일 | 역할 | 상태 |
|---|---|---|
| `src/shortlink/main.py` | `create_app()`에서 `init_schema()` 호출과 `router` 등록 (확장만) | 스켈레톤에서 배선 완료 |
| `src/shortlink/config.py` | 변경 없음 | — |
| `src/shortlink/db.py` | SQLite 연결과 스키마 생성 | 스텁 |
| `src/shortlink/codes.py` | 무작위 코드 생성 | 스텁 |
| `src/shortlink/validation.py` | URL 검증 규칙 | 스텁 |
| `src/shortlink/repository.py` | `Link` 레코드, 저장과 조회 | 스텁 |
| `src/shortlink/routes.py` | 요청/응답 모델과 두 엔드포인트 | 스텁 |

의존 방향: `routes → repository → db, codes`, `routes → validation`. `main → db, routes`.

## 3. 인터페이스

### `db.py`

```python
SCHEMA: str  # CREATE TABLE IF NOT EXISTS links (...)
def connect(db_path: str) -> sqlite3.Connection
def init_schema(db_path: str) -> None
```

테이블 (테스트에서 직접 조회해도 되는 공개 사항):

```sql
CREATE TABLE IF NOT EXISTS links (
    code       TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    created_at TEXT NOT NULL   -- 'YYYY-MM-DDTHH:MM:SSZ' (UTC)
)
```

- 연결은 작업마다 열고 닫는다 (요청 간 공유하지 않음). 엔드포인트는 동기 `def`로 만들어 스레드 풀에서 돈다.
- 모든 쿼리는 `?` 파라미터 바인딩만 쓴다.

### `codes.py`

```python
CODE_LENGTH = 7
CODE_ALPHABET = string.ascii_letters + string.digits  # 62자
def generate_code() -> str  # secrets.choice 기반
```

### `validation.py`

```python
MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = frozenset({"http", "https"})
def validate_url(url: str) -> None  # 위반 시 ValueError
```

거절 조건 (하나라도 해당하면 `ValueError`):

1. 빈 문자열
2. `len(url) > 2048` (문자 수 기준)
3. 공백(스페이스 포함)이나 ASCII 제어 문자(0x00–0x20, 0x7F)를 포함 — 결정 D-3
4. `urllib.parse.urlsplit` 결과의 스킴이 `http`/`https`가 아님 (대소문자 무시) — 결정 D-2
5. `urlsplit(url).hostname`이 비어 있음 (`https://`, `https://:80` 등)

### `repository.py`

```python
@dataclass(frozen=True)
class Link:
    code: str
    url: str
    created_at: str  # 'YYYY-MM-DDTHH:MM:SSZ'

MAX_CODE_ATTEMPTS = 10

class LinkRepository:
    def __init__(self, db_path: str) -> None
    def create(self, url: str) -> Link   # 코드 생성, PK 충돌(IntegrityError) 시 재생성, 한도 초과 시 RuntimeError
    def get(self, code: str) -> Link | None
```

### `routes.py`

```python
router = APIRouter()

class CreateLinkRequest(BaseModel):
    url: StrictStr            # 숫자 등 비문자열은 422
    # field_validator("url")에서 validate_url 호출 → ValueError는 422로 변환

class LinkResponse(BaseModel):
    code: str
    short_url: str
    url: str
    created_at: str

@router.post("/links", status_code=201, response_model=LinkResponse)
def create_link(body: CreateLinkRequest, request: Request) -> LinkResponse

@router.get("/{code}")
def follow_link(code: str, request: Request) -> Response
```

- 설정은 `request.app.state.settings`에서 읽는다 (`db_path`, `base_url`).
- `short_url = f"{settings.base_url}/{code}"` (`Settings`가 끝 `/`를 이미 제거함).
- 리다이렉트는 `RedirectResponse`가 아니라 `Response(status_code=302, headers={"Location": ...})`로 만든다. `RedirectResponse`는 URL을 다시 퍼센트 인코딩해서 원래 URL과 글자가 달라질 수 있다 — 결정 D-4.
- 7자 영숫자 형식이 아닌 `code`는 DB 조회 없이 `404`.
- 404 본문은 FastAPI 기본 형식 `{"detail": "Not Found"}`.

### `main.py` (확장)

```python
def create_app(settings=None):
    settings = settings or Settings.from_env()
    init_schema(settings.db_path)
    app = FastAPI(title="ShortLink")
    app.state.settings = settings
    app.include_router(router)
    return app
```

## 4. 수용 기준과 테스트 대응

테스트 파일은 `tests/test_links.py` 하나를 기본으로 하고, 필요하면 나눈다. 모든 HTTP 검증은 `client` 픽스처를 쓴다.

| 수용 기준 | 검증 내용 | 테스트 (예정 이름) |
|---|---|---|
| AC-1 | `https://example.com/path?q=1` → 201, 네 필드 존재 | `test_create_returns_201_with_fields` |
| AC-2 | `code`가 `^[A-Za-z0-9]{7}$`, `short_url == "http://testserver/" + code` | `test_code_format_and_short_url` |
| AC-3 | 응답 `url`이 요청과 글자 그대로 같음 (대문자·쿼리·프래그먼트 포함 URL로도) | `test_url_returned_verbatim` |
| AC-4 | `http://example.com` → 201 | `test_http_scheme_accepted` |
| AC-5 | `ftp://example.com`, `javascript:alert(1)`, `data:text/html,hi`, `mailto:a@example.com` → 422 (parametrize) | `test_disallowed_scheme_rejected` |
| AC-6 | 본문 `{}`, `{"url": 123}`, `{"url": ""}` → 422 | `test_missing_non_string_empty_rejected` |
| AC-7 | `https://` → 422 | `test_url_without_host_rejected` |
| AC-8 | 정확히 2,048자 URL → 201, 2,049자 → 422 | `test_length_boundary` |
| AC-9 | 거절 요청 뒤 `links` 테이블 행 수 0 (sqlite3로 `settings.db_path` 직접 조회) | `test_rejected_requests_store_nothing` |
| AC-10 | 생성 후 `GET /{code}` (`follow_redirects=False`) → 302, `Location == url` | `test_redirect_to_original` |
| AC-11 | 없는 코드 `GET /ZZZZZZZ` → 404 | `test_unknown_code_404` |
| AC-12 | 같은 URL 두 번 → 코드 다름, 둘 다 302 + 같은 `Location` | `test_same_url_twice_new_codes` |
| AC-13 | 100회 생성 코드 집합 크기 100 | `test_hundred_codes_unique` |
| AC-14 | 같은 `settings`로 `create_app()`을 다시 만들어 새 `TestClient`로 302 확인 | `test_persists_across_app_instances` |
| AC-15 | `created_at`이 `%Y-%m-%dT%H:%M:%SZ`로 파싱되고 요청 시각(UTC)과 60초 이내 | `test_created_at_utc_iso8601` |

추가로 단위 테스트 권장 (선택): `generate_code()` 형식, `validate_url()` 경계, 코드 충돌 시 재생성(`generate_code`를 monkeypatch로 같은 값 → 다른 값 순서로 돌려주게 해서 `create()`가 성공하는지).

2,048자 URL 만들기 예: `"https://example.com/" + "a" * (2048 - len("https://example.com/"))`.

## 5. 해석 결정 요약

자세한 근거는 `docs/plans/F1-decisions.md`.

- D-1 `created_at`은 초 단위, `Z` 접미사 (`YYYY-MM-DDTHH:MM:SSZ`)
- D-2 스킴 비교는 대소문자를 무시 (`HTTPS://example.com` 허용, 저장은 그대로)
- D-3 공백·제어 문자가 든 URL은 422 (헤더 주입 방지, 정규화하지 않는다는 원칙과 충돌하지 않도록 고치지 않고 거절)
- D-4 `Location`은 저장한 URL 그대로. 비ASCII 문자만 UTF-8 퍼센트 인코딩 (HTTP 헤더는 latin-1만 담을 수 있음)
- D-5 422 본문은 FastAPI 기본 검증 오류 형식, 404 본문은 `{"detail": "Not Found"}`
- D-6 코드 생성은 `secrets`, 충돌 시 최대 10회 재시도 후 500
- D-7 길이 2,048은 파이썬 문자 수(`len`) 기준
