# F2 구현 계획 — 클릭 통계와 커스텀 별칭

- 설계서: `docs/features/F2.md` (v1)
- 선행: F1 (`docs/plans/F1-plan.md`의 인터페이스와 결정 D-1~D-11은 그대로 유효)
- 화면 목업: `docs/plans/mockups/F2-index.html`
- 실행 모드: human

## 1. 구현 범위

- 커스텀 별칭: `POST /links`의 선택 필드 `alias`, 홈 화면 폼의 선택 입력칸 `alias`
- 클릭 통계: 리다이렉트할 때 클릭 수와 마지막 접근 시각 기록, 통계 API `GET /links/{code}/stats`, 통계 화면 `GET /stats/{code}`
- 결과 화면에 "통계 보기" 링크
- F1 DB 파일 호환: 앱 시작 시 `links` 테이블에 새 열을 추가(마이그레이션)
- 범위 밖: 인증, 만료, 삭제, 요청 수 제한, 관리 화면, 상세 통계, 별칭 수정

## 2. 모듈 구조 (변경분)

| 파일 | 변경 | 상태 |
|---|---|---|
| `src/shortlink/validation.py` | `validate_alias()`, `InvalidAliasError`, 별칭 상수와 문구 추가 | 스텁 |
| `src/shortlink/db.py` | `init_schema()`가 새 열(`clicks`, `last_accessed_at`)이 없으면 `ALTER TABLE`로 추가 | 스텁 (`ensure_click_columns()`) |
| `src/shortlink/repository.py` | `Link`에 `clicks`, `last_accessed_at` 추가, `create(url, alias=None)`, `record_click(code)`, `AliasTakenError` | 스텁 |
| `src/shortlink/api.py` | `LinkIn.alias`, 409 처리, `GET /links/{code}/stats`, `LinkStatsOut` | 스텁 |
| `src/shortlink/web.py` | 폼 `alias` 처리(422/409), `GET /stats/{code}`, 리다이렉트 시 `record_click`, `display_timestamp()` | 스텁 |
| `src/shortlink/templates/home.html` | 별칭 입력칸, 안내 문구, 오류 위치 표시 | 구현 단계 |
| `src/shortlink/templates/result.html` | "통계 보기" 링크 | 구현 단계 |
| `src/shortlink/templates/stats.html` | 새 통계 화면 | 구현 단계 |
| `src/shortlink/static/style.css` | 목업 `F2-*.html`의 "F2 추가 스타일" 블록을 덧붙임 | 구현 단계 |

라우트: `GET /links/{code}/stats`(api)와 `GET /stats/{code}`(web)는 두 단계 경로라서 한 단계 경로만 받는 `GET /{code}`와 충돌하지 않는다. 등록 순서(api → web, `/{code}`가 마지막)는 F1과 같다.

## 3. 인터페이스

### 3.1 별칭 검증 (`validation.validate_alias(alias: object) -> str`)

규칙을 아래 순서로 검사하고 처음 걸린 규칙의 문구로 `InvalidAliasError(message)`를 던진다. 통과하면 입력을 그대로 돌려준다(대소문자 변환, 공백 제거 없음).

| 순서 | 조건 | 문구 상수 | 문구 |
|---|---|---|---|
| 1 | 문자열이 아님 | `MSG_ALIAS_NOT_STRING` | alias는 문자열이어야 합니다. |
| 2 | 길이(문자 수)가 4 미만 또는 30 초과 | `MSG_ALIAS_LENGTH` | 별칭은 4자 이상 30자 이하여야 합니다. |
| 3 | `^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$`에 맞지 않음 (`re.fullmatch`, ASCII 문자 클래스만) | `MSG_ALIAS_CHARS` | 별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있고, 하이픈으로 시작하거나 끝날 수 없습니다. |
| 4 | 예약어 (대소문자 무시, D2-3) | `MSG_ALIAS_RESERVED` | 이 별칭은 서비스에서 쓰는 이름이라 쓸 수 없습니다. 다른 별칭을 입력해 주세요. |

- 상수: `ALIAS_MIN_LENGTH = 4`, `ALIAS_MAX_LENGTH = 30`, `RESERVED_ALIASES = frozenset({"links", "static", "stats", "docs", "redoc", "openapi.json", "api", "admin", "manage"})`
- `openapi.json`은 `.` 때문에 3번 규칙에서 먼저 걸리지만 목록에는 설계서대로 둔다.
- 중복 문구 `MSG_ALIAS_TAKEN = "이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요."`도 이 모듈에 둔다(API와 화면이 같이 씀).

### 3.2 저장

- 테이블: `links(code TEXT PRIMARY KEY, url TEXT NOT NULL, created_at TEXT NOT NULL, clicks INTEGER NOT NULL DEFAULT 0, last_accessed_at TEXT)`
- `init_schema()`: `CREATE TABLE IF NOT EXISTS`(새 열 포함) 뒤 `ensure_click_columns(conn)`가 `PRAGMA table_info(links)`로 열을 확인하고 없는 열만 `ALTER TABLE links ADD COLUMN ...`. F1 DB의 기존 행은 `clicks = 0`, `last_accessed_at = NULL`이 된다. 여러 번 불러도 안전해야 한다.
- `Link`: 기존 필드 뒤에 `clicks: int = 0`, `last_accessed_at: datetime | None = None` (기본값이 있어 기존 생성 코드가 깨지지 않음).
- `LinkRepository.create(url, alias=None) -> Link`
  - `alias`가 `None`이면 F1과 같다(무작위 7자, 충돌 시 재시도). 무작위 코드가 기존 별칭과 겹쳐도 PRIMARY KEY 충돌로 재시도된다.
  - `alias`가 있으면(이미 검증된 값) 그 값을 코드로 INSERT 한 번. PRIMARY KEY 충돌이면 `AliasTakenError`를 던지고 아무것도 저장하지 않는다. 기존 무작위 코드와 같은 별칭도 409다(설계서 "이미 쓰이는 코드나 별칭").
  - 별칭 비교는 SQLite 기본 `BINARY` 비교라 대소문자를 구분한다(AC-8). 열에 `COLLATE NOCASE`를 붙이지 않는다.
- `LinkRepository.get(code) -> Link | None`: 새 필드까지 채운다. 클릭 수를 바꾸지 않는다.
- `LinkRepository.record_click(code) -> Link | None`: 한 트랜잭션에서 `UPDATE links SET clicks = clicks + 1, last_accessed_at = ? WHERE code = ?`를 하고, 갱신된 행이 없으면 `None`, 있으면 갱신 뒤의 `Link`를 돌려준다. 증가는 SQL 안에서 해서 동시 요청에도 수가 빠지지 않게 한다. 시각은 `created_at`과 같은 형식(UTC, 초 단위, `Z`).

### 3.3 JSON API

`POST /links`, 본문 `{"url": "...", "alias": "..."}`

- `LinkIn.alias: StrictStr | None = None`. 필드가 없거나 `null`이면 별칭 없음.
- 검사 순서: 본문 형식(FastAPI) → `validate_url` → `validate_alias`(별칭이 있을 때) → 저장. 처음 걸린 오류 하나만 돌려준다.
- 별칭 규칙 위반 `422 {"detail": "<문구>"}`, 숫자 같은 비문자열 `alias`는 FastAPI 기본 422.
- 중복 `409 {"detail": MSG_ALIAS_TAKEN}`.
- 201 응답 필드는 F1과 같다(`code`, `short_url`, `url`, `created_at`). 별칭이 있으면 `code == alias`.

`GET /links/{code}/stats`

- 200 `LinkStatsOut {code, url, short_url, clicks, created_at, last_accessed_at}`. `last_accessed_at`은 접근한 적이 없으면 `null`. 시각 형식은 `format_timestamp()`.
- 없는 코드 `404 {"detail": "링크를 찾을 수 없습니다."}` (JSON).
- 조회는 `repository.get()`만 쓰고 클릭 수를 늘리지 않는다.

`GET /{code}` (변경)

- `repository.record_click(code)`로 바꾼다. 결과가 `None`이면 F1과 같은 404 화면(어떤 행도 바뀌지 않음), 있으면 F1과 같은 302.

### 3.4 웹 화면

| 화면 | 요청 | 상태 | 템플릿 | 목업 |
|---|---|---|---|---|
| 홈 | `GET /` | 200 | `home.html` | `F2-home.html` |
| 결과 | `POST /` 성공 | 200 | `result.html` | `F2-result.html` |
| 입력 오류(별칭 규칙) | `POST /` 별칭 규칙 위반 | 422 | `home.html` | `F2-error-alias.html` |
| 입력 오류(중복) | `POST /` 별칭 중복 | 409 | `home.html` | `F2-error-duplicate.html` |
| 입력 오류(URL) | `POST /` URL 규칙 위반 | 422 | `home.html` | F1과 같음(오류 위치만 URL 칸) |
| 통계 | `GET /stats/{code}` | 200 | `stats.html` | `F2-stats.html`, `F2-stats-empty.html` |
| 찾을 수 없음 | 없는 코드 `GET /{code}`, `GET /stats/{code}` | 404 | `not_found.html` | `F1-not-found.html` (변경 없음) |

홈 폼 (`home.html`)

- 순서: 오류 문구(있을 때) → `줄일 URL` 라벨과 입력칸 → `별칭 (선택)` 라벨과 입력칸 → 별칭 안내 문구 → `줄이기` 버튼.
- 별칭 입력칸: `<label for="alias">별칭 (선택)</label>`, `<input type="text" id="alias" name="alias" value="{{ alias_value }}" autocomplete="off" placeholder="my-link" aria-describedby="alias-hint">`. `maxlength`, `pattern`, `required`는 쓰지 않는다(F1 D-7과 같은 이유).
- 안내 문구: `<p class="hint" id="alias-hint">영문, 숫자, 하이픈(-)으로 4~30자. 비워 두면 7자 코드를 자동으로 만듭니다.</p>`
- 폼 처리 `shorten_form(url="", alias="")`: `alias`가 빈 문자열이면 별칭 없음(D2-1). 검사 순서는 API와 같다(URL → 별칭 → 중복).
- 오류 화면 컨텍스트: `error`(문구), `error_field`(`"url"` 또는 `"alias"`), `url_value`, `alias_value`. 오류 문구 `<p class="error" id="form-error" role="alert">`는 폼 맨 위에 하나만 두고, `error_field`에 해당하는 입력칸에만 `aria-invalid="true"`와 `aria-describedby`(`form-error`, 별칭 칸은 `form-error alias-hint`)를 붙인다.
- 422(별칭 규칙)와 409(중복) 모두 입력했던 URL과 별칭을 그대로 입력칸에 남긴다(이스케이프 유지).

결과 화면 (`result.html`)

- 컨텍스트에 `code` 추가. "다른 URL 줄이기" 앞에 `<a class="stats-link" href="/stats/{{ code }}">통계 보기</a>`를 둔다. 배치는 `F2-result.html`의 `.result-actions` 행.

통계 화면 (`stats.html`)

- 제목(`<title>`): `링크 통계 — ShortLink`, `<h1>링크 통계</h1>`, 설명 "이 단축 링크가 얼마나 쓰였는지 보여 드립니다."
- 단축 URL 링크(`.short-url`), 클릭 수 상자(`.click-count`, 숫자는 천 단위 구분 없이 그대로), 정의 목록(`<dl class="stats-list">`)에 원래 URL, 만든 시각, 마지막 접근.
- 시각 표시: `<time datetime="2026-10-29T01:23:45Z">2026-10-29 01:23:45 UTC</time>`. `datetime` 속성은 `format_timestamp()`, 보이는 글자는 `display_timestamp()` (`"%Y-%m-%d %H:%M:%S UTC"`).
- 마지막 접근이 없으면 `<dd class="muted">아직 없음</dd>`.
- 하단 링크: "홈으로 가기"(`href="/"`). 통계 화면을 열어도 클릭 수는 늘지 않는다.
- 원래 URL은 자동 이스케이프로 표시(AC-21). `|safe` 금지.

## 4. 수용 기준과 테스트 대응

| AC | 내용 | 테스트 파일 | 확인할 것 |
|---|---|---|---|
| AC-1 | 별칭 생성 201, code·short_url | `tests/test_aliases.py` | `code == alias`, `short_url == base_url + "/" + alias` |
| AC-2 | 별칭으로 302 | `tests/test_aliases.py` | `follow_redirects=False`, Location |
| AC-3 | 별칭 없으면 7자 코드 | `tests/test_aliases.py` | 필드 없음과 `null` 둘 다 `^[A-Za-z0-9]{7}$` |
| AC-4 | 길이 경계 | `tests/test_aliases.py` | 3자·31자 422, 4자·30자 201 |
| AC-5 | 허용 안 되는 문자, 하이픈 시작·끝 | `tests/test_aliases.py` | 공백, `_`, `/`, `.`, 한글, `-abcd`, `abcd-` 각각 422 (parametrize), `a-b-c-d` 201 |
| AC-6 | 예약어 | `tests/test_aliases.py` | 예약어 9개 각각 422 (parametrize), 대문자 예약어(`Admin`)도 422 (D2-3) |
| AC-7 | 중복 409, 기존 링크 유지 | `tests/test_aliases.py` | 두 번째 요청 409, 첫 링크 리다이렉트 그대로. 기존 무작위 코드를 별칭으로 써도 409 |
| AC-8 | 대소문자 구분 | `tests/test_aliases.py` | `My-Link`, `my-link` 둘 다 201, 각자 URL로 302 |
| AC-9 | 거절 시 저장 없음 | `tests/test_aliases.py` | 422·409 뒤 `count_links()` 변화 없음 |
| AC-10 | 폼 별칭 입력칸, 결과에 별칭 | `tests/test_web_f2.py` | `<label for>` 연결된 `name="alias"`, "별칭 (선택)", 결과 HTML의 단축 URL이 별칭 |
| AC-11 | 폼 422·409 오류 화면 | `tests/test_web_f2.py` | 상태 코드, `text/html`, 오류 문구, `value="<url>"`, `value="<alias>"`, 행 수 변화 없음. 빈 별칭은 무작위 코드(D2-1) |
| AC-12 | 새 링크 통계 | `tests/test_stats.py` | 200, 필드 6개, `clicks == 0`, `last_accessed_at is None` |
| AC-13 | 3번 접근 | `tests/test_stats.py` | `clicks == 3`, `last_accessed_at` 형식과 생성 시각 이후 |
| AC-14 | 통계 조회는 안 셈 | `tests/test_stats.py` | API 여러 번, 통계 화면 여러 번 뒤에도 `clicks` 그대로 |
| AC-15 | 없는 코드 접근은 안 셈 | `tests/test_stats.py` | 링크 생성 뒤 없는 코드 `GET` → 그 링크 `clicks == 0` |
| AC-16 | 없는 코드 통계 API 404 | `tests/test_stats.py` | 404 |
| AC-17 | 통계 화면 | `tests/test_web_f2.py` | 200 `text/html`, 클릭 수, 원래 URL, 접근 전 "아직 없음", 접근 뒤 "아직 없음" 없음 |
| AC-18 | 없는 코드 통계 화면 | `tests/test_web_f2.py` | 404 `text/html`, "링크를 찾을 수 없습니다" |
| AC-19 | 결과 화면 "통계 보기" | `tests/test_web_f2.py` | `href="/stats/<code>"`, 글자 "통계 보기" (무작위 코드와 별칭 둘 다) |
| AC-20 | 앱 재생성 후 클릭 수 유지 | `tests/test_stats.py` | 같은 `settings`로 `create_app` 두 번 |
| AC-21 | 통계 화면 이스케이프 | `tests/test_web_f2.py` | `https://example.com/<script>alert(1)</script>` → 원문 없음, `&lt;script&gt;` 있음 |
| AC-22 | 통계 화면 lang, viewport | `tests/test_web_f2.py` | `<html lang="ko">`, `name="viewport"`, CSP 헤더(F1 D-10) |
| AC-23 | F1 계속 만족 | 기존 `tests/test_*.py` 전체 | 기존 테스트가 그대로 통과. F1 테스트는 F2가 의도적으로 바꾼 동작이 아니면 고치지 않는다 |

보조 테스트

- `tests/test_validation.py`에 `validate_alias` 단위 테스트 추가(규칙 순서와 문구, 비문자열, 숫자만 있는 별칭 허용).
- `tests/test_repository.py`에 `create(alias=...)`, `AliasTakenError`, `record_click()` (없는 코드 `None`, 증가와 시각) 추가.
- `tests/test_migration.py`: F1 스키마(열 3개)로 만든 DB 파일에 행을 넣고 `create_app` → 기존 링크 302, 통계 `clicks == 0` → 접근 뒤 1. `init_schema` 두 번 호출 안전. (설계서상 평가 테스트 대상은 아니지만 회귀 방지용)
- `conftest.py`는 확장만 한다.

## 5. 설계서 해석 결정 (H1에서 확인 요청)

| # | 설계서 | 해석 | 이유 |
|---|---|---|---|
| D2-1 | "별칭을 주지 않으면" | 폼: 별칭 칸이 빈 문자열이면 별칭 없음(무작위 코드). API: 필드 없음과 `null`은 별칭 없음, 빈 문자열 `""`은 길이 규칙 위반 422 | 폼은 빈 칸도 항상 전송되므로 비워 둔 것을 "안 줌"으로 봐야 함. API는 명시적으로 준 값이므로 규칙대로 검사 |
| D2-2 | 오류 우선순위 | URL 검사 → 별칭 규칙 → 중복 순으로 처음 걸린 오류 하나만 표시 | F1의 "첫 번째 규칙 하나만 표시"와 같은 방식 |
| D2-3 | 예약어 목록 | 대소문자 무시(`Admin`, `API`, `Stats`도 거절) | 별칭 자체는 대소문자를 구분하지만, 예약어는 경로와 헷갈리는 이름을 막는 목적이라 대문자 변형도 막는 편이 안전(F3 관리 화면 대비) |
| D2-4 | "이미 쓰이는 코드나 별칭" | 기존 무작위 코드와 같은 별칭도 409 | 코드와 별칭이 같은 `code` 열을 씀 |
| D2-5 | 409·422 응답 본문 | `{"detail": "<한국어 문구>"}` (F1 D-5와 같음) | 화면과 API가 같은 문구를 씀 |
| D2-6 | 마지막 접근 시각 | 리다이렉트(302)가 나간 요청 시각, UTC 초 단위 `Z` 형식. 통계 화면에는 `2026-10-29 01:23:45 UTC`로 표시 | 설계서 "같은 형식". 화면은 읽기 쉽게 하되 `<time datetime>`에 원래 형식을 둠 |
| D2-7 | 통계 API 404 본문 | `{"detail": "링크를 찾을 수 없습니다."}` JSON | API 경로이므로 JSON. 화면 경로 `GET /stats/{code}`만 HTML 404 |
| D2-8 | 클릭 수 세는 범위 | `GET /{code}`가 302를 돌려준 경우만 셈. 봇·중복 접근 구분 없음 | 설계서가 "리다이렉트할 때마다"라고 씀. 상세 통계는 범위 밖 |
| D2-9 | F1 DB 호환 | 앱 시작 시 없는 열만 `ALTER TABLE ADD COLUMN` | 기존 행 보존, 클릭 수 0부터 |

## 6. 작업 분담

- implementer: `src/shortlink/**` 스텁 구현, `home.html`·`result.html` 수정, `stats.html` 작성, `style.css`에 목업의 "F2 추가 스타일" 블록 덧붙이기.
- test-writer: 4절의 테스트 파일. 기존 F1 테스트는 유지하고, 새 파일과 보조 테스트를 추가한다.
