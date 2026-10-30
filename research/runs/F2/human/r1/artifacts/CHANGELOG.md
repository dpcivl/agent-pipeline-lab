# CHANGELOG

기능별 변경 기록입니다. 최신 항목이 위에 옵니다.

## F2 — 클릭 통계와 커스텀 별칭 (2026-10-30)

설계서: `docs/features/F2.md` (v1). 실행 기록: `docs/plans/F2-plan.md`, `docs/plans/F2-report.md`.

### 추가

- 커스텀 별칭: `POST /links`의 선택 필드 `alias`로 코드를 직접 정합니다(길이 4~30자, 영문 대소문자·숫자·하이픈, 하이픈으로 시작·끝나지 않음, 예약어 9개 거절, 대소문자 구분). 규칙 위반은 `422`, 이미 쓰이는 별칭은 `409`이며 아무것도 저장하지 않습니다.
- 홈 화면 폼에 "별칭 (선택)" 입력칸(`name="alias"`)을 추가했습니다. 422·409 오류 시 같은 상태 코드의 홈 화면에 문구를 보이고 URL과 별칭을 입력칸에 남깁니다.
- 클릭 통계: `GET /{code}` 리다이렉트마다 클릭 수를 1 늘리고 마지막 접근 시각을 기록합니다. 없는 코드의 404는 세지 않습니다.
- 통계 API `GET /links/{code}/stats`(`code`, `url`, `short_url`, `clicks`, `created_at`, `last_accessed_at`). 없는 코드는 `404` JSON. 통계 조회는 클릭 수를 늘리지 않습니다. 인증이 없는 공개 API입니다.
- 통계 화면 `GET /stats/{code}`: 클릭 수, 원래 URL, 생성 시각, 마지막 접근 시각(없으면 "아직 없음"). 없는 코드는 `404` HTML 화면.
- 결과 화면에 "통계 보기" 링크를 추가했습니다.
- 오류 문구 6개(`MSG_ALIAS_*`, `MSG_ALIAS_TAKEN`)를 `validation.py`에 추가했습니다.
- 저장: `links` 테이블에 `clicks`(정수, 기본 0)와 `last_accessed_at`(텍스트, `NULL` 가능) 열을 추가했습니다. F1 DB 파일은 시작할 때 자동으로 마이그레이션하며 기존 링크는 클릭 수 0부터 셉니다. 여러 프로세스가 동시에 시작해도 한 번만 마이그레이션합니다(`BEGIN IMMEDIATE`).
- 요구 사항: SQLite 3.35 이상 (`UPDATE ... RETURNING`).

### 변경

- 홈 화면 폼 오류 문구의 id를 `url-error`에서 `form-error`로 바꾸고, 문제가 된 입력칸에 `aria-invalid`를 붙입니다.
- 클릭 수는 천 단위 쉼표로 표시합니다(예: `1,284회`).

### 동작 메모

- 별칭은 입력한 그대로 검사합니다(공백 제거와 소문자 변환 없음). 폼에서 별칭 칸이 비어 있으면 별칭 없음으로 보고 무작위 코드를 만듭니다. API에서 `alias`를 생략하거나 `null`이면 별칭 없음이고, `""`은 길이 규칙 위반 `422`입니다.
- URL과 별칭이 둘 다 틀리면 URL 문구만 나옵니다(URL 검사가 먼저).
- 통계 화면의 단축 URL을 눌러 이동하면 그 접속도 클릭으로 셉니다.
- 설계서에 명시되지 않은 F2 구현 결정은 계획서 `docs/plans/F2-plan.md` 5절(D-F2-1~9)에 기록했습니다.

### 알려진 제약 (minor, 기록만)

- 통계 API와 통계 화면은 코드만 알면 원래 URL, 클릭 수, 마지막 접근 시각을 볼 수 있습니다(인증은 F3 범위).
- 리다이렉트마다 쓰기 트랜잭션이 생깁니다. 요청이 몰리면 `database is locked` 오류와 클릭 수 누락이 날 수 있습니다. 요청 수 제한과 WAL 모드는 F3 이후에 검토합니다.
- 예약어가 설계서의 9개뿐이라 `login`, `health` 같은 별칭을 만들 수 있습니다. 대소문자만 다른 별칭(`Team-Docs`와 `team-docs`)으로 비슷한 주소를 만드는 것도 설계서 AC-8에 따라 허용됩니다.
- `init_schema`의 예외 처리 `ROLLBACK`은 SQLite가 이미 트랜잭션을 끝낸 경우 원래 예외를 가릴 수 있습니다(디스크 가득 참 등, 드문 경우).

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
