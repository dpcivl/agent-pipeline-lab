# F2 구현 계획 — 클릭 통계와 커스텀 별칭

- 설계서: `docs/features/F2.md` (v1)
- 선행: F1 (`docs/plans/F1-plan.md`의 결정 D-1~D-11은 그대로 유지)
- 화면 목업: `docs/plans/mockups/F2-index.html`
- 실행 모드: human

## 1. 구현 범위

- 커스텀 별칭: `POST /links`의 선택 필드 `alias`, 홈 화면 폼의 `name="alias"` 입력칸
- 클릭 통계: 리다이렉트할 때 `clicks` +1, `last_accessed_at` 기록
- 통계 API `GET /links/{code}/stats`, 통계 화면 `GET /stats/{code}`
- 결과 화면에 "통계 보기" 링크
- F1 시절 DB 파일 호환(컬럼 추가 마이그레이션)
- 범위 밖: 인증, 만료, 삭제, 요청 수 제한, 관리 화면, 상세 통계·그래프, 별칭 수정

## 2. 모듈 구조

| 파일 | 변경 | 상태 |
|---|---|---|
| `src/shortlink/validation.py` | 별칭 규칙 추가: `validate_alias()`, `InvalidAliasError`, `ALIAS_MIN_LENGTH=4`, `ALIAS_MAX_LENGTH=30`, `RESERVED_ALIASES`, 문구 상수 | 스텁 추가 |
| `src/shortlink/db.py` | `init_schema()`가 새 컬럼 `clicks`, `last_accessed_at`을 만들고, F1 DB에는 `ALTER TABLE ... ADD COLUMN`으로 추가 | 구현 단계에서 수정 |
| `src/shortlink/repository.py` | `Link`에 `clicks`, `last_accessed_at` 필드. `create(url, alias=None)`, `record_click(code)`, `AliasTakenError` | 스텁 추가 |
| `src/shortlink/api.py` | `LinkIn.alias`, 409 처리, `GET /links/{code}/stats`와 `LinkStatsOut` | 스텁 추가 |
| `src/shortlink/web.py` | 폼 `alias` 처리, 리다이렉트 시 클릭 기록, `GET /stats/{code}`, `format_display_timestamp()` | 스텁 추가 |
| `src/shortlink/templates/home.html` | 별칭 입력칸, 오류 필드 표시 | 구현 단계에서 수정 |
| `src/shortlink/templates/result.html` | "통계 보기" 링크 | 구현 단계에서 수정 |
| `src/shortlink/templates/stats.html` | 통계 화면 (새 파일) | 구현 단계에서 작성 |
| `src/shortlink/static/style.css` | 목업의 F2 추가 스타일 블록 | 구현 단계에서 수정 |

라우트: `api.router`의 `/links/{code}/stats`와 `web.router`의 `/stats/{code}`는 두 단계 경로라 `GET /{code}`(한 단계)와 겹치지 않는다. `web.router`는 계속 마지막에 등록한다.

## 3. 인터페이스

### 3.1 별칭 검증 (`validation.validate_alias(alias: object) -> str`)

아래 순서로 검사하고 처음 걸린 규칙의 문구로 `InvalidAliasError(message)`를 던진다. 통과하면 입력을 **그대로** 돌려준다(앞뒤 공백 제거, 소문자 변환 없음).

| 순서 | 조건 | 문구 상수 | 문구 |
|---|---|---|---|
| 1 | 문자열이 아님 | `MSG_ALIAS_NOT_STRING` | alias는 문자열이어야 합니다. |
| 2 | 길이(문자 수)가 4 미만 또는 30 초과 | `MSG_ALIAS_LENGTH` | 별칭은 4자 이상 30자 이하여야 합니다. |
| 3 | `[A-Za-z0-9-]` 밖의 문자 포함 | `MSG_ALIAS_CHARS` | 별칭에는 영문, 숫자, 하이픈(-)만 쓸 수 있습니다. |
| 4 | 하이픈으로 시작하거나 끝남 | `MSG_ALIAS_HYPHEN_EDGE` | 별칭은 하이픈(-)으로 시작하거나 끝날 수 없습니다. |
| 5 | 예약어 (대소문자 무시, D-F2-4) | `MSG_ALIAS_RESERVED` | 예약된 이름이라 별칭으로 쓸 수 없습니다. |

- 3번은 `str.isascii()`와 함께 검사한다(`str.isalnum()`은 한글·전각 숫자를 통과시키므로 쓰지 않는다). 정규식이면 `re.fullmatch(r"[A-Za-z0-9-]+", alias)`로, `$`가 줄바꿈 앞에서 맞는 문제를 피한다.
- `RESERVED_ALIASES = frozenset({"links", "static", "stats", "docs", "redoc", "openapi.json", "api", "admin", "manage"})`. `openapi.json`은 3번에서 먼저 걸리지만 목록에는 설계서대로 둔다.
- 중복 별칭 문구(409): `MSG_ALIAS_TAKEN` = "이미 사용 중인 별칭입니다. 다른 별칭을 입력해 주세요."

### 3.2 저장

스키마 (새 DB):

```sql
CREATE TABLE IF NOT EXISTS links (
    code             TEXT PRIMARY KEY,
    url              TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    clicks           INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TEXT
)
```

- F1 DB: `PRAGMA table_info(links)`로 컬럼을 확인하고 없는 컬럼만 `ALTER TABLE links ADD COLUMN clicks INTEGER NOT NULL DEFAULT 0`, `ALTER TABLE links ADD COLUMN last_accessed_at TEXT`. 기존 행은 `clicks=0`, `last_accessed_at=NULL`. `init_schema()`는 계속 여러 번 불러도 안전해야 한다.
- `Link`: `code`, `url`, `created_at`, `clicks: int = 0`, `last_accessed_at: datetime | None = None`.
- `LinkRepository.create(url, alias=None) -> Link`
  - `alias is None`: F1과 같이 무작위 코드, 충돌 시 최대 10회 재시도.
  - `alias`가 있으면: 그 값을 코드로 INSERT 한 번. PRIMARY KEY 충돌이면 `AliasTakenError`를 던지고 아무것도 저장하지 않는다. 미리 SELECT로 확인하지 않고 INSERT 결과로 판단한다(동시 요청 경쟁 방지). 기존 무작위 코드와 같은 값도 충돌로 본다.
  - `alias`는 이미 검증된 값이어야 한다.
- `LinkRepository.record_click(code) -> Link | None`
  - 한 트랜잭션 안에서 `UPDATE links SET clicks = clicks + 1, last_accessed_at = ? WHERE code = ?`를 하고(원자적 증가, 읽고-더하고-쓰기 금지) 갱신된 링크를 돌려준다. 행이 없으면 `None`, 아무것도 바꾸지 않는다. (`UPDATE ... RETURNING` 사용 가능, SQLite 3.49)
  - `last_accessed_at`은 UTC, 초 단위, `created_at`과 같은 형식으로 저장.
- `LinkRepository.get(code)`: 통계 필드까지 채워 돌려준다. 클릭 수를 바꾸지 않는다.
- SQL은 모두 파라미터 바인딩, 연결은 호출마다 열고 닫는다(F1과 같음).

### 3.3 JSON API

`POST /links`, 본문 `{"url": "...", "alias": "..."}` (`alias` 선택)

- `alias`가 없거나 `null`이면 무작위 코드 (AC-3).
- `alias`는 `StrictStr | None`. 숫자, 배열 등은 422(FastAPI 기본 본문).
- 검사 순서: URL 검증 → 별칭 검증 → 저장. 둘 다 틀리면 URL 문구가 나온다.
- 별칭 검증 실패: `422`, `{"detail": "<MSG_ALIAS_*>"}`. 빈 문자열 `""`은 길이 규칙으로 422 (D-F2-2).
- 중복: `409`, `{"detail": MSG_ALIAS_TAKEN}`.
- 성공: `201`, F1과 같은 네 필드. `code == alias`, `short_url == <base_url>/<alias>`.

`GET /links/{code}/stats`

- `200`, `LinkStatsOut`: `code`, `url`, `short_url`, `clicks`(int), `created_at`(문자열), `last_accessed_at`(문자열 또는 `null`)
- 없으면 `404`, `{"detail": "링크를 찾을 수 없습니다."}` JSON (D-F2-6)
- 클릭 수를 바꾸지 않는다.

`GET /{code}` (변경)

- `repository.record_click(code)`로 바꾼다. 있으면 클릭 +1 후 F1과 같은 `302`, 없으면 F1과 같은 `404` HTML, 아무것도 세지 않음.
- 코드 형식(7자 영숫자 등)으로 미리 거르지 않는다. 별칭으로 만든 코드도 리다이렉트된다.

### 3.4 웹 화면

| 화면 | 요청 | 상태 | 템플릿 | 목업 |
|---|---|---|---|---|
| 홈 (별칭 칸 추가) | `GET /` | 200 | `home.html` | `F2-home.html` |
| 결과 ("통계 보기" 추가) | `POST /` 성공 | 200 | `result.html` | `F2-result.html` |
| 입력 오류 (URL, F1과 같음) | `POST /` URL 실패 | 422 | `home.html` | `F1-error.html` 문구 + `F2-home.html` 배치 |
| 별칭 오류 | `POST /` 별칭 규칙 위반 | 422 | `home.html` | `F2-alias-error.html` |
| 별칭 중복 | `POST /` 별칭 중복 | 409 | `home.html` | `F2-alias-conflict.html` |
| 통계 | `GET /stats/{code}` | 200 | `stats.html` | `F2-stats.html`, `F2-stats-empty.html` |
| 찾을 수 없음 | `GET /{code}`, `GET /stats/{code}` 없음 | 404 | `not_found.html` | `F1-not-found.html` (변경 없음) |

- 홈 폼: URL 칸 → 별칭 칸 → "줄이기" 버튼을 세로로 쌓는다.
  - `<label for="alias">별칭 (선택)</label>`, `<input type="text" id="alias" name="alias" value="{{ alias_value }}" autocomplete="off" placeholder="my-link" aria-describedby="alias-hint">`, 안내 `<p class="hint" id="alias-hint">영문, 숫자, 하이픈(-)으로 4~30자. 비워 두면 7자 코드를 자동으로 만듭니다.</p>`
  - `required`, `pattern`, `maxlength`는 쓰지 않는다(F1 D-7과 같은 이유: 서버 오류 화면을 가리지 않게).
- 폼의 `alias`가 빈 문자열이거나 없으면 별칭 없음으로 본다(D-F2-1). 공백만 있는 값(`" "`)은 비어 있지 않으므로 규칙 위반 422.
- 오류 화면: 오류 문구 `<p class="error" id="form-error" role="alert">`를 폼 맨 위에 하나 두고, 문제가 된 칸(`error_field`가 `"url"` 또는 `"alias"`)에만 `aria-invalid="true" aria-describedby="form-error"`. 입력했던 URL과 별칭은 둘 다 `value`에 남긴다.
- 결과 화면: "다른 URL 줄이기" 앞에 `<a class="stats-link" href="/stats/{{ code }}">통계 보기</a>`.
- 통계 화면: 제목 "링크 통계", 단축 URL(링크), 원래 URL, 클릭 수(큰 숫자 + "회"), 생성 시각, 마지막 접근 시각(없으면 "아직 없음"), "다른 URL 줄이기" 링크.
  - 시각 표시: `format_display_timestamp(dt)` → `"2026-10-29 01:23:45 UTC"`, `<time datetime="2026-10-29T01:23:45Z">`로 감싼다.
  - 클릭 수는 천 단위 쉼표(`{:,}`)로 표시한다. 예: `1,284회`, `0회`.
  - 통계 화면은 클릭 수를 늘리지 않는다.
- 이스케이프, `lang="ko"`, viewport, CSP는 F1과 같은 `base.html`과 미들웨어를 그대로 쓴다.
- 문구, 배치, 색은 목업 그대로. 새 CSS는 목업의 "F2 추가 스타일" 블록을 `style.css` 끝에 덧붙인다.

## 4. 수용 기준과 테스트 대응

새 테스트 파일: `tests/test_aliases.py`(API 별칭), `tests/test_stats.py`(통계 API, 클릭), `tests/test_web_f2.py`(화면). F1 테스트 파일은 그대로 두고 계속 통과해야 한다.

| AC | 내용 | 테스트 파일 | 확인할 것 |
|---|---|---|---|
| AC-1 | 별칭 생성 201 | `test_aliases.py` | `code == alias`, `short_url == base_url + "/" + alias` |
| AC-2 | 별칭 리다이렉트 | `test_aliases.py` | `GET /my-link` 302, Location == 원래 URL |
| AC-3 | alias 없음 → 7자 코드 | `test_aliases.py` | `alias` 생략과 `null` 각각 `^[A-Za-z0-9]{7}$` |
| AC-4 | 길이 경계 | `test_aliases.py` | 3자·31자 422, 4자·30자 201 |
| AC-5 | 허용하지 않는 문자, 하이픈 끝 | `test_aliases.py` | 공백, `_`, `/`, `.`, 한글, `-abcd`, `abcd-` 각각 422 (parametrize). 4자 한글처럼 길이는 맞는 값도 포함 |
| AC-6 | 예약어 | `test_aliases.py` | 9개 각각 422, 대문자 변형(`Admin`)도 422 (D-F2-4) |
| AC-7 | 중복 409 | `test_aliases.py` | 두 번째 409, 첫 링크 리다이렉트가 첫 URL 그대로. 무작위 코드와 같은 별칭도 409 |
| AC-8 | 대소문자 구분 | `test_aliases.py` | `My-Link`, `my-link` 모두 201, 각자 URL로 302 |
| AC-9 | 거절 시 저장 없음 | `test_aliases.py` | 422·409 뒤 `count_links()` 변화 없음 |
| AC-10 | 폼 별칭 입력칸과 결과 | `test_web_f2.py` | `label for="alias"`, `input name="alias"`, 결과 HTML의 단축 URL이 `/<별칭>` |
| AC-11 | 폼 오류 422/409 | `test_web_f2.py` | 422·409 각각 `text/html`, 오류 문구, `input name=url`과 `name=alias`의 `value`가 입력값 |
| AC-12 | 새 링크 통계 | `test_stats.py` | 200, 6개 키, `clicks == 0`, `last_accessed_at is None`, `created_at`이 생성 응답과 같음 |
| AC-13 | 3번 접근 | `test_stats.py` | `clicks == 3`, `last_accessed_at` 형식 `^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$` |
| AC-14 | 통계 조회는 세지 않음 | `test_stats.py` | API 여러 번, 통계 화면 여러 번 뒤에도 `clicks` 그대로 |
| AC-15 | 404는 세지 않음 | `test_stats.py` | 없는 코드 접근 뒤 기존 링크 `clicks` 0 |
| AC-16 | 없는 코드 통계 API | `test_stats.py` | 404 |
| AC-17 | 통계 화면 | `test_web_f2.py` | 200, `text/html`, 클릭 수, 원래 URL, 새 링크는 "아직 없음", 접근 후에는 "아직 없음" 없음 |
| AC-18 | 없는 코드 통계 화면 | `test_web_f2.py` | 404, `text/html`, "링크를 찾을 수 없습니다" |
| AC-19 | "통계 보기" 링크 | `test_web_f2.py` | 결과 HTML에 `href="/stats/<code>"`이고 글자가 "통계 보기" |
| AC-20 | 앱 재생성 후 클릭 수 유지 | `test_stats.py` | 같은 `settings`로 `create_app` 두 번 |
| AC-21 | 통계 화면 이스케이프 | `test_web_f2.py` | `https://example.com/<script>alert(1)</script>` 링크의 통계 화면에 `<script>alert(1)` 원문 없음, `&lt;script&gt;` 있음 |
| AC-22 | lang, viewport | `test_web_f2.py` | 통계 화면 `<html lang="ko">`, `name="viewport"` |
| AC-23 | F1 호환 | 기존 F1 테스트 전체 | `uv run pytest`로 함께 실행 |

보조 테스트:
- `tests/test_validation.py`에 추가하지 않고 `tests/test_aliases.py` 안에 `validate_alias()` 단위 테스트(규칙 순서와 문구, 입력을 그대로 돌려줌, 줄바꿈 끝 `"abcd\n"` 거절)
- `tests/test_stats.py`에 마이그레이션 테스트: F1 스키마(3컬럼)로 만든 DB 파일에 행을 넣고 `create_app` → 리다이렉트 302, 통계 `clicks` 0에서 1
- `tests/test_repository.py` 확장 가능: `create(url, alias=...)` 중복 시 `AliasTakenError`, `record_click` 없는 코드 `None`

## 5. 설계서 해석 결정 (H1에서 확인 요청)

| # | 설계서 | 해석 | 이유 |
|---|---|---|---|
| D-F2-1 | 폼의 선택 입력칸 | 폼에서 별칭 칸이 비어 있으면(빈 문자열) 별칭 없음 → 무작위 코드 | 브라우저 폼은 빈 칸도 `alias=`로 보냄 |
| D-F2-2 | API의 선택 필드 | API에서 `alias` 생략·`null`은 별칭 없음, `""`은 길이 규칙 위반 422 | JSON은 "없음"을 따로 표현할 수 있으므로 빈 문자열은 잘못된 값으로 봄 |
| D-F2-3 | 별칭 규칙 | 입력 그대로 검사, 앞뒤 공백 제거·소문자 변환 없음 | F1의 "정규화 없음" 원칙과 대소문자 구분(AC-8) |
| D-F2-4 | 예약어 | 대소문자 무시로 비교 (`Admin`, `STATS`도 거절) | 대소문자만 바꾼 `Admin` 같은 링크가 운영 경로처럼 보이는 것을 막음. 설계서 예약어 9개 자체는 모두 거절되므로 AC-6과 충돌 없음 |
| D-F2-5 | 검사 순서 | URL 검증 → 별칭 검증 → 중복(409). 둘 다 틀리면 URL 문구 하나만 표시 | 첫 번째 오류 하나만 보이는 F1 방식과 같음 |
| D-F2-6 | 통계 API 404 본문 | `{"detail": "링크를 찾을 수 없습니다."}` JSON | `/links` 아래는 JSON API. `GET /{code}`의 404 HTML(F1 D-6)과 경로가 다름 |
| D-F2-7 | 마지막 접근 시각 | `created_at`과 같은 저장·응답 형식. 화면에는 `2026-10-29 01:23:45 UTC`로 표시 | 화면은 사람이 읽기 쉽게, `<time datetime>`으로 기계 판독 형식 유지 |
| D-F2-8 | 클릭 수 증가 | SQL `clicks = clicks + 1` 한 문장으로 원자적 증가. HEAD 요청은 따로 처리하지 않음(FastAPI GET 라우트는 HEAD를 받지 않음) | 동시 요청에서 클릭이 사라지지 않게 |
| D-F2-9 | 통계 화면 링크 대상 | 통계 화면의 단축 URL을 눌러 이동하면 그 클릭도 센다 | 일반 리다이렉트와 구분할 방법이 없고, 설계서는 리다이렉트마다 센다고 함 |

## 6. 작업 분담

- implementer: `src/shortlink/**` 스텁 구현과 기존 함수 수정, `stats.html` 작성, `home.html`·`result.html` 수정, `style.css` 추가 블록.
- test-writer: 4절의 새 테스트 파일. 기존 F1 테스트는 고치지 않는다(호환성 확인용). `conftest.py`는 확장만(예: 링크의 `clicks`를 DB에서 직접 읽는 헬퍼).
