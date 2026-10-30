# F2 구현 계획 — 클릭 통계와 커스텀 별칭

- 설계서: `docs/features/F2.md` (v1)
- 화면 목업: `docs/plans/mockups/F2-index.html`
- 실행 모드: auto (H1은 메인 세션이 스스로 승인)
- 선행: F1 (`docs/plans/F1-plan.md`의 결정 D-1~D-11은 그대로 유지)

## 1. 구현 범위

- 커스텀 별칭: `POST /links`의 선택 필드 `alias`, 홈 화면 폼의 `alias` 입력칸, 규칙 위반 `422`, 중복 `409`
- 클릭 통계: `GET /{code}` 리다이렉트마다 `clicks + 1`과 `last_accessed_at` 기록
- 통계 API `GET /links/{code}/stats`, 통계 화면 `GET /stats/{code}`
- 결과 화면에 "통계 보기" 링크
- F1 데이터베이스 파일 자동 이전(열 추가), 기존 링크 클릭 수 0부터
- 범위 밖: 인증, 만료, 삭제, 요청 수 제한, 관리 화면, 상세 통계, 그래프, 별칭 수정

## 2. 모듈 구조

| 파일 | 변경 | 상태 |
|---|---|---|
| `src/shortlink/validation.py` | `validate_alias()`, `InvalidAliasError`, 별칭 상수와 문구 추가 | 스텁 |
| `src/shortlink/db.py` | `init_schema()`가 `clicks`, `last_accessed_at` 열을 만들고, F1 DB에는 `ALTER TABLE`로 열 추가 | 구현 단계 |
| `src/shortlink/repository.py` | `Link`에 `clicks`, `last_accessed_at` 추가, `create(url, alias=None)`, `AliasTakenError`, `record_click(code)` | 스텁 |
| `src/shortlink/api.py` | `LinkIn.alias`, `409`, `GET /links/{code}/stats`, `LinkStatsOut` | 스텁 |
| `src/shortlink/web.py` | 폼 `alias` 처리, `GET /stats/{code}`, 리다이렉트에서 `record_click`, `display_timestamp()` | 스텁 |
| `src/shortlink/templates/home.html` | 별칭 입력칸과 안내 문구, 오류 표시 대상 필드 | 구현 단계 |
| `src/shortlink/templates/result.html` | "통계 보기" 링크 | 구현 단계 |
| `src/shortlink/templates/stats.html` | 새 통계 화면 | 구현 단계 |
| `src/shortlink/static/style.css` | 목업의 "F2 추가 스타일" 블록 추가 | 구현 단계 |
| `main.py`, `config.py` | 변경 없음 (`api.router` → `web.router` 순서 유지) | — |

라우트: `/links/{code}/stats`와 `/stats/{code}`는 두 단계 경로라서 `GET /{code}`(한 단계)와 겹치지 않는다. `GET /links` 같은 한 단계 경로는 `GET /{code}`에서 없는 코드로 처리된다(404). 별칭에서 예약어를 막으므로 `/links`, `/static`, `/stats`, `/docs` 등이 링크 코드가 되는 일은 없다.

## 3. 인터페이스

### 3.1 별칭 검증 (`validation.validate_alias(alias: object) -> str`)

아래 순서로 검사하고 처음 걸린 규칙의 문구로 `InvalidAliasError(message)`를 던진다. 통과하면 입력을 그대로 돌려준다(대소문자 변환, 공백 제거 없음).

| 순서 | 조건 | 문구 상수 | 문구 |
|---|---|---|---|
| 1 | 문자열이 아님 | `MSG_ALIAS_NOT_STRING` | alias는 문자열이어야 합니다. |
| 2 | 길이가 4자 미만 또는 30자 초과 (문자 수) | `MSG_ALIAS_LENGTH` | 별칭은 4자 이상 30자 이하여야 합니다. |
| 3 | `[A-Za-z0-9-]` 밖의 문자 포함 (ASCII만, `re.fullmatch`) | `MSG_ALIAS_CHARS` | 별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다. |
| 4 | 하이픈으로 시작하거나 끝남 | `MSG_ALIAS_HYPHEN` | 별칭은 하이픈(-)으로 시작하거나 끝날 수 없습니다. |
| 5 | 예약어 (대소문자 무시, 2.D-4) | `MSG_ALIAS_RESERVED` | 이 별칭은 예약어라서 쓸 수 없습니다. 다른 별칭을 입력해 주세요. |

- 상수: `ALIAS_MIN_LENGTH = 4`, `ALIAS_MAX_LENGTH = 30`, `RESERVED_ALIASES = frozenset({"links", "static", "stats", "docs", "redoc", "openapi.json", "api", "admin", "manage"})`
- 중복(409) 문구: `MSG_ALIAS_TAKEN` = "이미 쓰이는 별칭입니다. 다른 별칭을 입력해 주세요." (`validation.py`에 둔다)
- `InvalidAliasError(ValueError)`는 `InvalidURLError`와 같은 모양(`.message`).

### 3.2 저장

스키마 (새 DB):

```sql
CREATE TABLE IF NOT EXISTS links (
    code             TEXT PRIMARY KEY,
    url              TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    clicks           INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TEXT            -- NULL = 접근한 적 없음
)
```

- F1 DB 이전: `init_schema()`가 `PRAGMA table_info(links)`로 열을 확인하고, 없는 열만 `ALTER TABLE links ADD COLUMN clicks INTEGER NOT NULL DEFAULT 0`, `ALTER TABLE links ADD COLUMN last_accessed_at TEXT`로 추가한다. 여러 번 불러도 안전해야 한다. 기존 행은 `clicks = 0`, `last_accessed_at = NULL`.
- `Link`: `code`, `url`, `created_at`, `clicks: int = 0`, `last_accessed_at: datetime | None = None` (기본값으로 F1 호출부 호환).
- `LinkRepository.create(url, alias=None) -> Link`
  - `alias is None`: F1과 같음(무작위 코드, 충돌 재시도 10회).
  - `alias`가 있으면: 이미 검증된 값으로 INSERT 한 번. PRIMARY KEY 충돌이면 `AliasTakenError`를 던지고 아무것도 저장하지 않는다. 재시도하지 않는다. 존재 여부를 먼저 SELECT하지 않고 INSERT 충돌로 판단한다(동시 요청에도 안전).
  - 별칭은 대소문자를 구분한다. SQLite `TEXT PRIMARY KEY`의 기본 비교(BINARY)가 그대로 구분한다.
- `LinkRepository.record_click(code) -> Link | None`
  - 한 트랜잭션에서 `UPDATE links SET clicks = clicks + 1, last_accessed_at = ? WHERE code = ?`를 하고, 갱신된 행이 없으면 `None`, 있으면 그 행을 다시 읽어 `Link`로 돌려준다.
  - 증가는 SQL 안에서 한다(`clicks + 1`). 읽고 더해서 쓰는 방식은 동시 요청에서 클릭을 잃으므로 쓰지 않는다.
  - `last_accessed_at`은 `created_at`과 같은 형식(UTC 초 단위, `Z`).
- `LinkRepository.get(code)`: 클릭 수를 바꾸지 않는다. 통계 API와 화면이 쓴다.

### 3.3 JSON API

`POST /links`, 본문 `{"url": "...", "alias": "..."}` (`alias` 선택)

- `LinkIn.alias: StrictStr | None = None`. 필드가 없거나 `null`이면 별칭 없음.
- 검사 순서: URL(`validate_url`) → 별칭(`validate_alias`) → 저장. 둘 다 틀리면 URL 문구.
- `201`: F1과 같은 네 필드. 별칭을 주면 `code == alias`, `short_url == <base_url>/<alias>`.
- `422`: 별칭 규칙 위반, `alias`가 문자열이 아님(숫자, 배열 등), 빈 문자열 `""`(길이 규칙, 2.D-1). 검증 실패 본문은 `{"detail": "<문구>"}`.
- `409`: 이미 쓰이는 코드나 별칭. 본문 `{"detail": MSG_ALIAS_TAKEN}`.
- 422와 409 모두 아무것도 저장하지 않는다.

`GET /links/{code}/stats`

- `200`, `LinkStatsOut`: `code`, `url`, `short_url`, `clicks`(int), `created_at`(str), `last_accessed_at`(str 또는 `null`)
- 없는 코드: `404` JSON `{"detail": "링크를 찾을 수 없습니다."}` (`MSG_LINK_NOT_FOUND`)
- 클릭 수를 바꾸지 않는다.

`GET /{code}` (변경)

- `repository.get()` 대신 `repository.record_click()`. 결과가 `None`이면 F1과 같은 404 화면, 아니면 F1과 같은 302.
- 코드 형식(7자 영숫자)으로 미리 거르지 않는다. 별칭, F1 코드 모두 DB 조회로 판단한다.

### 3.4 웹 화면

| 화면 | 요청 | 상태 | 템플릿 | 목업 |
|---|---|---|---|---|
| 홈 | `GET /` | 200 | `home.html` | `F2-home.html` |
| 별칭 규칙 오류 | `POST /` 별칭 규칙 위반 | 422 | `home.html` | `F2-error-alias.html` |
| 별칭 중복 | `POST /` 이미 쓰이는 별칭 | 409 | `home.html` | `F2-error-conflict.html` |
| 결과 | `POST /` 성공 | 200 | `result.html` | `F2-result.html` |
| 통계 | `GET /stats/{code}` | 200 | `stats.html` | `F2-stats.html` |
| 통계 (접근 없음) | `GET /stats/{code}` 클릭 0 | 200 | `stats.html` | `F2-stats-empty.html` |
| 찾을 수 없음 | `GET /stats/{code}` 없는 코드 | 404 | `not_found.html` (F1 그대로) | `F1-not-found.html` |
| URL 입력 오류 | `POST /` URL 규칙 위반 | 422 | `home.html` | `F1-error.html` + 별칭 입력칸 |

홈 폼 (`home.html`):

- 구조는 목업 그대로: URL 필드 묶음(`div.field`) → 별칭 필드 묶음 → 제출 버튼(`div.form-actions`).
- `<label for="url">줄일 URL</label>`, `<input type="text" id="url" name="url" value="{{ url_value }}" inputmode="url" ...>`
- `<label for="alias">별칭 (선택)</label>`, `<input type="text" id="alias" name="alias" value="{{ alias_value }}" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="my-link" aria-describedby="alias-hint">`
- 안내 `<p class="hint" id="alias-hint">영문, 숫자, 하이픈(-)으로 4~30자. 비워 두면 무작위 코드를 만듭니다.</p>`
- `maxlength`, `pattern`, `required`는 쓰지 않는다(F1 D-7과 같은 이유: 서버 오류 화면을 가리지 않게).
- 오류 문구는 F1처럼 폼 맨 위 `<p class="error" id="form-error" role="alert">`. 오류 대상 필드(`error_field`: `"url"` 또는 `"alias"`)의 입력칸에만 `aria-invalid="true"`를 붙이고 `aria-describedby`에 `form-error`를 넣는다(별칭은 `form-error alias-hint`).
- 폼 `alias`가 없거나 빈 문자열이면 별칭 없음(2.D-1). 그 밖에는 그대로 `validate_alias`.
- 거절 시 `url_value`, `alias_value` 둘 다 입력칸에 남긴다(자동 이스케이프).
- 상태 코드: URL 오류·별칭 규칙 오류 `422`, 중복 `409`.

결과 화면 (`result.html`): F1 그대로 두고 맨 아래 링크 줄을 `<div class="link-row">`로 바꿔 `<a class="back-link" href="/stats/{{ code }}">통계 보기</a>`와 `<a class="back-link" href="/">다른 URL 줄이기</a>`를 나란히 둔다. 컨텍스트에 `code` 추가.

통계 화면 (`stats.html`, 목업 `F2-stats.html`):

- 제목 "링크 통계", 안내 "단축 링크가 몇 번 쓰였는지 보여 드립니다."
- 단축 URL: 결과 화면과 같은 `a.short-url` (복사 버튼 없음)
- `<dl class="stats">`: 클릭 수(`<span class="click-count">{{ clicks }}</span>회`), 원래 URL(`dd.original-url`, 이스케이프), 생성 시각, 마지막 접근 시각
- 시각 표시: `<time datetime="2026-10-29T01:23:45Z">2026-10-29 01:23:45 UTC</time>` (`display_timestamp()`), 마지막 접근이 없으면 `<span class="muted">아직 없음</span>`
- 링크 줄: `<a class="back-link" href="/">다른 URL 줄이기</a>`
- 클릭 수는 천 단위 구분 없이 정수 그대로.

공통: `base.html`(lang, viewport) 상속, 자동 이스케이프 유지, `|safe` 금지. CSS는 목업의 "F2 추가 스타일" 블록을 `style.css` 끝에 그대로 붙인다.

## 4. 수용 기준과 테스트 대응

| AC | 내용 | 테스트 파일 | 확인할 것 |
|---|---|---|---|
| AC-1 | 별칭 생성 201 | `tests/test_aliases.py` | `code == alias`, `short_url == base_url + "/" + alias` |
| AC-2 | 별칭 리다이렉트 | `tests/test_aliases.py` | `GET /{alias}` 302, Location |
| AC-3 | 별칭 없음 → 7자 코드 | `tests/test_aliases.py` | `alias` 생략, `alias: null` 둘 다 `^[A-Za-z0-9]{7}$` |
| AC-4 | 길이 경계 | `tests/test_aliases.py` | 3자·31자 422, 4자·30자 201 |
| AC-5 | 문자와 하이픈 규칙 | `tests/test_aliases.py` | 공백, `_`, `/`, `.`, 한글, `-abcd`, `abcd-` 422 (parametrize). 가운데 하이픈 `my-link` 201 |
| AC-6 | 예약어 | `tests/test_aliases.py` | 예약어 9개 각각 422 (parametrize), 대문자 예약어(`Admin`)도 422 |
| AC-7 | 중복 409 | `tests/test_aliases.py` | 두 번째 409, 기존 링크 Location 그대로. 무작위 코드와 같은 별칭도 409 |
| AC-8 | 대소문자 구분 | `tests/test_aliases.py` | `My-Link`, `my-link` 둘 다 201, 각자 URL로 302 |
| AC-9 | 거절 시 저장 없음 | `tests/test_aliases.py` | 422·409 뒤 `count_links()` 변화 없음 |
| AC-10 | 폼 별칭 입력칸과 결과 | `tests/test_web_f2.py` | `<label for="alias">`, `name="alias"`, "별칭 (선택)", 폼 제출 결과의 `href="<base>/<alias>"` |
| AC-11 | 폼 오류 422/409 | `tests/test_web_f2.py` | 422·409, `text/html`, 문구, `value="<url>"`, `value="<alias>"`, 저장 없음 |
| AC-12 | 새 링크 통계 | `tests/test_stats.py` | 200, 필드 6개, `clicks == 0`, `last_accessed_at is None` |
| AC-13 | 3번 접근 | `tests/test_stats.py` | `clicks == 3`, `last_accessed_at` 형식 `^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$` |
| AC-14 | 통계 조회는 안 셈 | `tests/test_stats.py` | API 여러 번 + 통계 화면 조회 뒤 `clicks` 그대로 |
| AC-15 | 404는 안 셈 | `tests/test_stats.py` | 없는 코드 `GET` 뒤 기존 링크 `clicks` 그대로 |
| AC-16 | 없는 코드 통계 API | `tests/test_stats.py` | 404 |
| AC-17 | 통계 화면 | `tests/test_web_f2.py` | 200, `text/html`, 클릭 수, 원래 URL, "아직 없음" (접근 전), 접근 뒤 "아직 없음" 사라짐 |
| AC-18 | 없는 코드 통계 화면 | `tests/test_web_f2.py` | 404, `text/html`, "링크를 찾을 수 없습니다" |
| AC-19 | 결과 화면 "통계 보기" | `tests/test_web_f2.py` | `href="/stats/<code>"`, "통계 보기" |
| AC-20 | 앱 재생성 후 클릭 수 유지 | `tests/test_stats.py` | 같은 `settings`로 `create_app` 두 번 |
| AC-21 | 통계 화면 이스케이프 | `tests/test_web_f2.py` | `<script>alert(1)</script>`이 든 URL → 원문 없음, `&lt;script&gt;` 있음 |
| AC-22 | lang, viewport | `tests/test_web_f2.py` | 통계 화면 `<html lang="ko">`, `name="viewport"` |
| AC-23 | F1 호환 | 기존 `tests/test_*.py` 전체 | 그대로 통과 |

보조 테스트:

- `tests/test_validation.py`에 `validate_alias` 규칙 순서와 문구 추가.
- `tests/test_repository.py`에 `create(alias=...)` 충돌 시 `AliasTakenError`, `record_click` 원자적 증가와 없는 코드 `None` 추가.
- `tests/test_migration.py`: F1 스키마(3열)로 DB를 직접 만들고 행을 넣은 뒤 `create_app` → 기존 링크 302, 통계 `clicks` 0에서 시작, 리다이렉트 뒤 1. `init_schema` 두 번 호출해도 오류 없음.

## 5. 설계서 해석 결정

| # | 설계서 | 해석 | 이유 |
|---|---|---|---|
| D-1 | "별칭을 주지 않으면" | API: 필드 없음 또는 `null` = 별칭 없음, `""`는 길이 규칙으로 422. 폼: 빈 입력칸 = 별칭 없음 | 폼은 빈 칸도 항상 전송되므로 빈 값을 "안 줌"으로 봐야 한다. API는 명시적으로 준 값이므로 규칙대로 검사 |
| D-2 | 규칙 위반 순서 | URL 먼저, 그다음 별칭. 별칭은 길이 → 문자 → 하이픈 → 예약어 | 오류는 하나만 보이므로 순서를 고정해 문구를 예측 가능하게 함 |
| D-3 | 공백이 든 별칭 | 앞뒤 공백도 제거하지 않고 422 | F1의 "정규화 없음" 원칙과 같음 |
| D-4 | 예약어 | 대소문자 무시(`Admin`, `LINKS`도 422) | 대소문자만 다른 예약어는 경로를 사칭하거나 헷갈리게 함. 관리 경로(F3)와 겹칠 위험 차단 |
| D-5 | `openapi.json` 예약어 | 목록에 그대로 두지만 `.` 때문에 문자 규칙(3번)에서 먼저 걸림 | 규칙 순서(D-2) |
| D-6 | 409 대상 | 별칭이 기존 무작위 코드와 같아도 409 | 설계서 "이미 쓰이는 코드나 별칭" |
| D-7 | 통계 API 404 본문 | `{"detail": "링크를 찾을 수 없습니다."}` JSON | `/links/...`는 JSON API 경로. `GET /{code}` 404(F1 D-6, HTML)와 다름 |
| D-8 | 통계 화면 시각 표시 | `YYYY-MM-DD HH:MM:SS UTC`, `<time datetime>`에 ISO 원문 | 사람이 읽기 쉬운 형식, 기계 판독용 원문 유지 |
| D-9 | 클릭 수 세기 | `GET /{code}`의 302 응답마다 1. 봇, 중복 방문 구분 없음 | 설계서 "리다이렉트할 때마다", 상세 통계는 범위 밖 |
| D-10 | 마지막 접근 시각 | 초 단위 UTC, `created_at`과 같은 형식 | 설계서 "같은 형식" |
| D-11 | F1 DB 이전 | 앱 시작 시 `ALTER TABLE ADD COLUMN`으로 자동 이전 | 설계서 호환성 요구. 별도 이전 명령 없이 동작해야 함 |

## 6. 작업 분담

- implementer: 2절의 `src/` 변경 전부, 템플릿 3개(`home.html`, `result.html` 수정, `stats.html` 새로), `style.css` 추가 블록.
- test-writer: 4절의 테스트. 새 파일 `test_aliases.py`, `test_stats.py`, `test_web_f2.py`, `test_migration.py`, 기존 `test_validation.py`, `test_repository.py`에 추가. 기존 F1 테스트는 고치지 않는다(AC-23 기준). `conftest.py`는 확장만.
