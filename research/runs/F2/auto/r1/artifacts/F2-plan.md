# F2 구현 계획 — 클릭 통계와 커스텀 별칭

- 설계서: `docs/features/F2.md` (v1)
- 선행: F1 (`docs/plans/F1-plan.md`의 결정 D-1~D-11은 그대로 유지)
- 해석 결정: `docs/plans/F2-decisions.md` (E-1~)
- 화면 목업: `docs/plans/mockups/F2-index.html`
- 실행 모드: auto

## 1. 구현 범위

- 별칭: `POST /links`의 선택 필드 `alias`, 홈 화면 폼의 선택 입력칸 `alias`
- 클릭 통계: `GET /{code}` 성공 시 클릭 수 +1과 마지막 접근 시각 기록
- 통계 API `GET /links/{code}/stats`, 통계 화면 `GET /stats/{code}`
- 결과 화면에 "통계 보기" 링크
- F1 DB 파일 자동 이전(열 추가)
- 범위 밖: 인증, 만료, 삭제, 요청 수 제한, 관리 화면, 상세 통계·그래프, 별칭 수정

## 2. 모듈 구조와 변경

| 파일 | 변경 | 상태 |
|---|---|---|
| `src/shortlink/validation.py` | `validate_alias()`, `InvalidAliasError`, 별칭 상수와 문구 추가 | 스텁 추가 |
| `src/shortlink/db.py` | 스키마에 `clicks`, `last_accessed_at` 추가, F1 DB 이전 `migrate_schema()` | 스텁 추가 (`init_schema`는 구현 단계에서 수정) |
| `src/shortlink/repository.py` | `Link`에 `clicks`, `last_accessed_at` 추가. `create(url, alias=None)`, `record_click(code)`, `AliasConflictError` | 스텁 추가 |
| `src/shortlink/api.py` | `LinkIn.alias`, 409 처리, `GET /links/{code}/stats`, 응답 모델 `LinkStatsOut` | 스텁 추가 |
| `src/shortlink/web.py` | 폼 `alias` 처리(422/409), `GET /{code}`에서 `record_click`, `GET /stats/{code}` | 스텁 추가 |
| `src/shortlink/templates/home.html` | 별칭 입력칸, 오류 표시 위치 일반화 | 구현 단계 |
| `src/shortlink/templates/result.html` | "통계 보기" 링크 | 구현 단계 |
| `src/shortlink/templates/stats.html` | 새 통계 화면 | 구현 단계 |
| `src/shortlink/static/style.css` | 목업의 "F2 추가 스타일" 블록 추가 | 구현 단계 |
| `main.py`, `config.py` | 변경 없음 (고정 계약) | — |

라우트: `GET /links/{code}/stats`(api.router)와 `GET /stats/{code}`(web.router)는 두 단계 경로라서 한 단계 경로인 `GET /{code}`와 겹치지 않는다. 등록 순서는 F1과 같이 api → web.

## 3. 인터페이스

### 3.1 별칭 검증 (`validation.validate_alias(alias: object) -> str`)

처음 걸린 규칙의 문구로 `InvalidAliasError(message)`를 던진다. 통과하면 입력을 그대로 돌려준다(공백 제거, 대소문자 변경 없음, E-5).

| 순서 | 조건 | 문구 상수 | 문구 |
|---|---|---|---|
| 1 | 문자열이 아님 | `MSG_ALIAS_NOT_STRING` | alias는 문자열이어야 합니다. |
| 2 | 길이가 4자 미만 또는 30자 초과 (문자 수) | `MSG_ALIAS_LENGTH` | 별칭은 4자 이상 30자 이하여야 합니다. |
| 3 | `[A-Za-z0-9-]` 밖의 문자 포함 | `MSG_ALIAS_CHARS` | 별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다. |
| 4 | 하이픈으로 시작하거나 끝남 | `MSG_ALIAS_HYPHEN_EDGE` | 별칭은 하이픈(-)으로 시작하거나 끝날 수 없습니다. |
| 5 | 예약어 (대소문자 무시, E-2) | `MSG_ALIAS_RESERVED` | 예약어라서 별칭으로 쓸 수 없습니다. 다른 별칭을 입력해 주세요. |

- 상수: `ALIAS_MIN_LENGTH = 4`, `ALIAS_MAX_LENGTH = 30`, `RESERVED_ALIASES = frozenset({"links", "static", "stats", "docs", "redoc", "openapi.json", "api", "admin", "manage"})`
- 주의: 3번은 ASCII만 허용해야 한다. `str.isalnum()`은 한글과 전각 숫자도 참이므로 쓰지 않는다. 정규식을 쓰면 `re.fullmatch`를 쓴다(`$`는 끝 줄바꿈 앞에서도 맞는다).
- 그 밖의 문구: `MSG_ALIAS_TAKEN = "이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요."` (409), `MSG_LINK_NOT_FOUND = "링크를 찾을 수 없습니다."` (통계 API 404)

### 3.2 저장

- 테이블(새 DB):
  ```sql
  CREATE TABLE IF NOT EXISTS links (
      code             TEXT PRIMARY KEY,
      url              TEXT NOT NULL,
      created_at       TEXT NOT NULL,
      clicks           INTEGER NOT NULL DEFAULT 0,
      last_accessed_at TEXT
  )
  ```
- `db.migrate_schema(conn)`: `PRAGMA table_info(links)`로 열을 확인하고 빠진 열만 `ALTER TABLE ... ADD COLUMN`으로 추가한다(E-11). `init_schema()`가 테이블 생성 뒤 부른다. 여러 번 불러도 안전.
- `Link`: 기존 필드 뒤에 `clicks: int = 0`, `last_accessed_at: datetime | None = None` 추가(기본값이 있어 기존 생성 코드와 호환).
- `LinkRepository.create(url, alias=None) -> Link`
  - `alias is None`: F1과 같음(무작위 코드, 충돌 시 재시도).
  - `alias`가 있으면: 그 값을 코드로 한 번만 INSERT. `sqlite3.IntegrityError`면 `AliasConflictError`를 던진다. 재시도하지 않고 아무것도 저장하지 않는다. `alias`는 이미 검증된 값이어야 한다.
- `LinkRepository.get(code)`: `clicks`, `last_accessed_at`도 채워서 돌려준다.
- `LinkRepository.record_click(code) -> Link | None`
  - 한 트랜잭션에서 `UPDATE links SET clicks = clicks + 1, last_accessed_at = ? WHERE code = ?`(E-10)를 하고, 영향받은 행이 없으면 `None`, 있으면 갱신된 `Link`를 돌려준다.
  - 시각은 `datetime.now(UTC).replace(microsecond=0)`를 `format_timestamp`로 저장.
- 연결은 F1과 같이 호출마다 열고 `closing`으로 닫는다. SQL은 모두 파라미터 바인딩.

### 3.3 JSON API

`POST /links`, 본문 `{"url": "...", "alias": "..."}` (`alias`는 선택, `StrictStr | None = None`)

| 경우 | 상태 | 본문 |
|---|---|---|
| 성공 | 201 | F1과 같은 네 필드. `code`는 별칭(있으면), `short_url`은 `<base_url>/<code>` |
| URL 검증 실패 | 422 | `{"detail": "<URL 문구>"}` (F1과 같음). URL을 먼저 검사한다 |
| 별칭 검증 실패 (`""` 포함, E-3) | 422 | `{"detail": "<별칭 문구>"}` |
| `alias`가 문자열도 `null`도 아님 | 422 | FastAPI 기본 422 본문 |
| 이미 쓰이는 코드·별칭 | 409 | `{"detail": MSG_ALIAS_TAKEN}` |

422, 409에서는 아무것도 저장하지 않는다.

`GET /links/{code}/stats`

- 200: `LinkStatsOut` = `{"code", "url", "short_url", "clicks", "created_at", "last_accessed_at"}`. `last_accessed_at`은 없으면 JSON `null`.
- 404: `{"detail": MSG_LINK_NOT_FOUND}` (JSON, E-9)
- 클릭 수를 늘리지 않는다(`repository.get` 사용).

`GET /{code}`

- `repository.record_click(code)`로 찾으면서 센다. 결과가 `None`이면 F1과 같은 404 HTML(세지 않음). 있으면 F1과 같은 302.

### 3.4 웹 화면

| 화면 | 요청 | 상태 | 템플릿 | 목업 |
|---|---|---|---|---|
| 홈 | `GET /` | 200 | `home.html` | `F2-home.html` |
| 결과 | `POST /` 성공 | 200 | `result.html` | `F2-result.html` |
| 입력 오류 (URL·별칭 규칙 위반) | `POST /` | 422 | `home.html` | `F2-error-alias.html` (URL 오류는 F1과 같은 문구) |
| 별칭 중복 | `POST /` | 409 | `home.html` | `F2-error-conflict.html` |
| 통계 | `GET /stats/{code}` | 200 | `stats.html` | `F2-stats.html`, `F2-stats-new.html` |
| 찾을 수 없음 | `GET /{code}`, `GET /stats/{code}` 없음 | 404 | `not_found.html` | `F1-not-found.html` (변경 없음) |

- 폼 처리 `POST /`: 필드 `url`(없으면 `""`), `alias`(없으면 `""`). `alias == ""`이면 별칭 없음(E-4). 순서: URL 검증 → 별칭 검증(있을 때) → 저장(`AliasConflictError`면 409).
- `home.html` 컨텍스트: `error`(문구 또는 None), `error_field`(`"url"` | `"alias"` | None), `url_value`, `alias_value`. 오류가 있으면 오류 문단 `<p class="error" id="form-error" role="alert">`, 해당 입력칸에 `aria-invalid="true"`와 `aria-describedby`에 `form-error`를 넣는다.
- 별칭 입력칸: `<label for="alias">별칭 (선택)</label>`, `<input type="text" id="alias" name="alias" value="{{ alias_value }}" autocomplete="off" placeholder="my-link" aria-describedby="alias-hint">`, 안내 `<p class="hint" id="alias-hint">`. `required`, `pattern`, `maxlength`는 쓰지 않는다(F1 D-7과 같은 이유: 검증은 서버 한 곳).
- 결과 화면: 컨텍스트에 `code` 추가. 원래 URL 아래 `<div class="link-row">`에 `<a class="back-link" href="/stats/{{ code }}">통계 보기</a>`와 기존 "다른 URL 줄이기". 통계 링크는 **상대 경로**(E-14).
- 통계 화면: 단축 URL 링크(`class="short-url"`), 원래 URL(텍스트, 이스케이프), `<dl class="stats-list">`에 클릭 수, 생성 시각, 마지막 접근 시각(없으면 `<dd class="muted">아직 없음</dd>`), "홈으로 가기" 링크. 시각은 `<time datetime="X">X</time>` (E-12).
- 문구, 배치, 색은 목업 그대로. `style.css`는 F1 공통 블록을 목업의 공통 블록(F1 + "F2 추가 스타일")으로 바꾼다.
- 이스케이프: 자동 이스케이프 유지, `|safe`, `Markup` 금지.

## 4. 수용 기준과 테스트 대응

| AC | 내용 | 테스트 파일 | 확인할 것 |
|---|---|---|---|
| AC-1 | 별칭 201, code·short_url | `tests/test_alias_api.py` | `code == alias`, `short_url == base_url + "/" + alias` |
| AC-2 | 별칭 리다이렉트 | `tests/test_alias_api.py` | `follow_redirects=False`, 302, Location |
| AC-3 | 별칭 없음 → 7자 코드 | `tests/test_alias_api.py` | 필드 없음, `null` 각각 `^[A-Za-z0-9]{7}$` |
| AC-4 | 길이 경계 | `tests/test_alias_api.py` | 3자·31자 422, 4자·30자 201 |
| AC-5 | 허용하지 않는 문자, 하이픈 끝 | `tests/test_alias_api.py` | 공백, `_`, `/`, `.`, 한글, 앞 하이픈, 뒤 하이픈 각각 422 (parametrize) |
| AC-6 | 예약어 | `tests/test_alias_api.py` | 9개 예약어 각각 422 (`openapi.json`은 문자 규칙에 먼저 걸려도 422면 됨) |
| AC-7 | 중복 409, 기존 링크 유지 | `tests/test_alias_api.py` | 두 번째 다른 URL로 409, 기존 별칭은 원래 URL로 302 |
| AC-8 | 대소문자 구분 | `tests/test_alias_api.py` | `My-Link`, `my-link` 모두 201, 각자 URL로 302 |
| AC-9 | 거절 시 저장 없음 | `tests/test_alias_api.py` | 422·409 뒤 `count_links()` 변화 없음 |
| AC-10 | 폼 별칭 입력칸, 결과에 별칭 | `tests/test_alias_web.py` | `<label for="alias">`, `name="alias"`, 결과 단축 URL이 `base_url/alias` |
| AC-11 | 폼 오류 422·409, 입력값 유지 | `tests/test_alias_web.py` | 상태, `text/html`, 오류 문구, `value="<url>"`, `value="<alias>"` |
| AC-12 | 새 링크 통계 | `tests/test_stats_api.py` | 200, 여섯 필드, `clicks == 0`, `last_accessed_at is None` |
| AC-13 | 3번 접근 → 3 | `tests/test_stats_api.py` | `clicks == 3`, `last_accessed_at` 형식 `^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$` |
| AC-14 | 통계 조회는 세지 않음 | `tests/test_stats_api.py` | 통계 API·통계 화면 여러 번 → `clicks == 0` |
| AC-15 | 없는 코드 접근은 세지 않음 | `tests/test_stats_api.py` | 링크 하나 만든 뒤 없는 코드 GET 404 → 그 링크 `clicks == 0` |
| AC-16 | 없는 코드 통계 API 404 | `tests/test_stats_api.py` | 404 |
| AC-17 | 통계 화면 | `tests/test_stats_web.py` | 200, `text/html`, 클릭 수, 원래 URL, "아직 없음" (접근 전), 접근 뒤엔 "아직 없음" 없음 |
| AC-18 | 없는 코드 통계 화면 404 | `tests/test_stats_web.py` | 404, `text/html`, "링크를 찾을 수 없습니다" |
| AC-19 | 결과 화면 "통계 보기" | `tests/test_stats_web.py` | 텍스트 "통계 보기", `href="/stats/<code>"` |
| AC-20 | 앱 재생성 후 클릭 수 유지 | `tests/test_stats_api.py` | 같은 `settings`로 `create_app` 두 번 |
| AC-21 | 통계 화면 이스케이프 | `tests/test_stats_web.py` | `https://example.com/<script>alert(1)</script>` → 원문 없음, `&lt;script&gt;` 있음 |
| AC-22 | lang, viewport | `tests/test_stats_web.py` | `<html lang="ko">`, `name="viewport"` |
| AC-23 | F1 회귀 | 기존 `tests/test_*.py` 전체 | 기존 테스트는 수정 없이 통과해야 한다 |

보조 단위 테스트:

- `tests/test_alias_validation.py`: 규칙 순서와 문구, 예약어 대소문자 무시(`Admin`), 끝 줄바꿈(`"abcd\n"`) 거절, 전각 숫자·한글 거절
- `tests/test_repository.py`(확장): `create(alias=...)` 충돌 시 `AliasConflictError`와 행 수 유지, `record_click` 없는 코드 `None`
- `tests/test_migration.py`: F1 스키마(세 열)로 만든 DB 파일에 행을 넣고 `create_app` → 기존 코드 302, 통계 `clicks == 0`, `init_schema` 두 번 호출 안전

## 5. 작업 분담

- implementer: `src/shortlink/**` 스텁 구현, 템플릿 3개 수정·추가, `style.css`.
- test-writer: 4절의 새 테스트 파일. 기존 F1 테스트는 고치지 않는다. `conftest.py`는 확장만.
