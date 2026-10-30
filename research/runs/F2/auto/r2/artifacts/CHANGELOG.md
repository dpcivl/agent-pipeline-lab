# CHANGELOG

기능별 변경 기록입니다. 최신 항목이 위에 옵니다.

## F2 — 클릭 통계와 커스텀 별칭 (2026-10-29)

설계서: `docs/features/F2.md` (v1). 실행 기록: `docs/plans/F2-plan.md`, `docs/plans/F2-report.md`, 결정 기록 `docs/plans/F2-decisions.md`.

### 추가

- 커스텀 별칭: `POST /links`의 선택 필드 `alias`. 별칭이 곧 코드가 되고 `code`, `short_url`에 쓰입니다. 규칙은 4~30자, 영문·숫자·하이픈, 하이픈으로 시작·끝 금지, 대소문자 구분, 예약어 9개 금지. 규칙 위반은 `422`, 이미 쓰이는 코드·별칭은 `409`이며 둘 다 저장하지 않습니다.
- 별칭 오류 문구(`MSG_ALIAS_*`, 409용 `MSG_ALIAS_TAKEN` 포함)는 API와 화면이 같이 씁니다.
- 홈 화면 폼에 `<label>`이 붙은 선택 입력칸 `name="alias"`("별칭 (선택)"). 잘못된 별칭은 `422`, 중복 별칭은 `409` 화면에 오류를 보이고 입력값을 남깁니다.
- 클릭 수 집계: `GET /{code}`가 `302`를 줄 때마다 `clicks`를 1 늘리고 `last_accessed_at`을 기록합니다. 없는 코드는 세지 않습니다.
- 통계 API `GET /links/{code}/stats`: `code`, `url`, `short_url`, `clicks`, `created_at`, `last_accessed_at`(없으면 `null`)을 돌려줍니다. 없는 코드는 `404` JSON. 조회는 클릭을 늘리지 않습니다.
- 통계 화면 `GET /stats/{code}`: 단축 URL, 원래 URL, 클릭 수, 생성 시각, 마지막 접근 시각("아직 없음" 표시)을 보여 줍니다. 없는 코드는 `404` 화면.
- 결과 화면에 "통계 보기" 링크 추가.
- F1 DB 자동 이전: 앱 시작 시 `clicks`와 `last_accessed_at` 열을 `ALTER TABLE`로 추가합니다. 기존 링크는 그대로 동작하고 클릭 수는 0부터 셉니다.
- 서비스 문서 `docs/service.md`를 F2 내용(별칭, 통계 API와 화면, 저장 구조, DB 이전)으로 갱신.

### 동작 메모

- `alias`를 주지 않거나 `null`이면 F1과 같이 무작위 코드를 만듭니다. 빈 문자열 `""`은 별칭 규칙 위반(`422`)입니다.
- 별칭의 앞뒤 공백은 지우지 않으므로 공백이 있으면 `422`입니다. 폼에서 별칭 입력칸을 비워 두면 별칭 없음으로 봅니다.
- 검사 순서는 URL 먼저, 그다음 별칭(길이 → 문자 → 하이픈 → 예약어)입니다.
- 별칭이 기존 무작위 코드와 같아도 `409`입니다.
- 클릭은 봇이나 반복 방문을 구분하지 않고 모두 셉니다.
- 통계 시각 표시는 화면에서 `YYYY-MM-DD HH:MM:SS UTC`, API와 DB에서는 F1과 같은 ISO 8601 `Z` 형식입니다.

### 알려진 제약 (minor, 기록만)

- 문자열이 아닌 `alias`(숫자, 배열 등)는 `validate_alias()`의 한국어 문구가 아니라 FastAPI 기본 422 본문(`detail`이 배열)으로 거절합니다. F1 `url`과 같은 규칙이며 상태 코드와 저장 없음은 지켜집니다 (결정 D-12).
- 동시 리다이렉트에서 `last_accessed_at`이 최대 1초 이른 값으로 덮어써질 수 있습니다. 클릭 수는 정확합니다.
- 여러 워커가 F1 DB를 동시에 시작하면 열 추가가 겹쳐 한 워커가 `duplicate column name`으로 시작에 실패할 수 있습니다. 단일 프로세스 실행에는 영향이 없고 재시작하면 정상입니다.
- `web.py`의 `follow_link` docstring과 모듈 docstring이 F2 동작을 아직 반영하지 않습니다 (문서성).
- 보안 관련 기록 (F3 범위): 리다이렉트 반복으로 클릭 수를 부풀리거나 별칭을 선점할 수 있고, 통계는 코드만 알면 누구나 볼 수 있습니다. 요청 수 제한과 인증이 없습니다. 예약어 목록은 F3에서 늘어날 경로(`login`, `health` 등)를 아직 막지 않습니다.
- `bandit` B608 경고 2건은 클래스 상수를 쓴 오탐입니다. 고정 리터럴 쿼리로 정리할 수 있습니다.
- 생김새가 비슷한 별칭(대소문자 차이 등)으로 사칭할 수 있습니다. AC-8에 따른 설계상 수용이며 F3에서 검토합니다.
- 쓰기가 막히면 리다이렉트가 500이 될 수 있습니다 (잠금 경합, 읽기 전용 DB). 쓰기 실패 시 폴백과 WAL·busy_timeout 설정을 검토합니다.

## F1 — 단축 URL 생성과 리다이렉트 (2026-10-29)

설계서: `docs/features/F1.md` (v2). 실행 기록: `docs/plans/F1-plan.md`, `docs/plans/F1-report.md`.

### 추가

- JSON API `POST /links`: `{"url": ...}`을 받아 7자 무작위 코드를 만들고 `201`로 `code`, `short_url`, `url`, `created_at`을 돌려줍니다.
- 리다이렉트 `GET /{code}`: 코드가 있으면 `302`와 `Location` 헤더, 없으면 `404` 화면.
- 웹 화면 4개: 홈(`GET /`), 결과(`POST /` 성공), 입력 오류(`POST /` 실패, `422`, 입력값 유지), 찾을 수 없음(`404`). 복사 버튼은 `copy.js`로 동작하며 JavaScript가 없어도 링크는 보입니다.
- URL 검증: 스킴 `http`/`https`(대소문자 무시), 호스트 필수, 2,048자 이하, 공백과 제어 문자 거절, UTF-8 인코딩 불가 문자 거절. 오류 문구 7개(`MSG_*`)는 API와 화면이 같이 씁니다.
- SQLite 저장(`sqlite3`, ORM 없음). `links` 테이블, 앱을 다시 만들어도 데이터 유지.
- 설정: 환경 변수 `SHORTLINK_DB_PATH`(기본 `shortlink.db`), `SHORTLINK_BASE_URL`(기본 `http://localhost:8000`).
- 보안 헤더: 모든 응답에 `X-Content-Type-Options: nosniff`, HTML 화면에 CSP(`default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`). `/docs`와 `/redoc`은 CSP 제외.
- 서비스 문서 `docs/service.md` 추가.

### 동작 메모

- URL은 받은 그대로 저장하고 응답합니다(정규화 없음). 같은 URL을 여러 번 보내면 요청마다 새 코드가 나옵니다.
- `Location` 헤더는 ASCII를 그대로 두고 비ASCII 문자만 UTF-8 퍼센트 인코딩합니다.
- 없는 코드의 404는 API와 화면 구분 없이 HTML입니다.

### 알려진 제약 (minor, 기록만)

- 형식이 깨진 호스트(예: `https://[`)는 "호스트가 없습니다" 문구로 거절됩니다. 동작에는 문제가 없습니다.
- 요청 수 제한과 요청 본문 크기 제한이 없습니다(F3 범위).
- `copy.js` 가드 테스트가 문자열 존재만 확인하므로, 가드가 빠져도 테스트가 통과할 수 있습니다.
