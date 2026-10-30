# CHANGELOG

기능별 변경 기록입니다. 최신 항목이 위에 옵니다.

## F2 — 클릭 통계와 커스텀 별칭 (2026-10-29)

설계서: `docs/features/F2.md` (v1). 해석 결정: `docs/plans/F2-decisions.md`. 실행 기록: `docs/plans/F2-plan.md`, `docs/plans/F2-report.md`.

### 추가

- 커스텀 별칭: `POST /links`의 선택 필드 `alias`. 별칭을 주면 그 값이 코드가 되고, 응답의 `code`와 `short_url`도 별칭을 씁니다. 규칙은 길이 4~30자, 영문 대소문자·숫자·하이픈, 양끝 하이픈 금지, 예약어 금지(9개, 대소문자 무시)입니다.
- 별칭 오류: 규칙 위반은 `422`, 이미 쓰이는 코드나 별칭은 `409`(`{"detail": "이미 쓰이는 별칭입니다. ..."}`). 거절된 요청은 아무것도 저장하지 않습니다.
- 클릭 통계: `GET /{code}`로 리다이렉트할 때마다 클릭 수를 1 늘리고 마지막 접근 시각을 기록합니다. 없는 코드의 404는 세지 않습니다.
- 통계 API `GET /links/{code}/stats`: `code`, `url`, `short_url`, `clicks`, `created_at`, `last_accessed_at`을 돌려줍니다. 없는 코드는 JSON `404`. 조회는 클릭 수를 늘리지 않습니다.
- 통계 화면 `GET /stats/{code}`: 단축 URL, 원래 URL, 클릭 수, 생성 시각, 마지막 접근 시각("아직 없음" 표시). 없는 코드는 `404` 화면.
- F1 DB 자동 이전: 시작할 때 `clicks`, `last_accessed_at` 열이 없으면 `ALTER TABLE`로 추가합니다. 기존 링크는 클릭 수 0부터 셉니다.

### 변경

- 홈 화면 폼에 "별칭 (선택)" 입력칸(`name="alias"`)을 추가했습니다. 빈 값이면 무작위 코드를 만듭니다.
- 입력 오류 화면이 `422`(규칙 위반)와 `409`(중복)를 구분해 같은 홈 화면에 오류 문구를 보이고, 입력했던 URL과 별칭을 남깁니다.
- 결과 화면에 "통계 보기" 링크(`/stats/{code}`)를 추가했습니다.
- 저장 테이블 `links`에 `clicks INTEGER NOT NULL DEFAULT 0`, `last_accessed_at TEXT` 열을 추가했습니다.
- 서비스 문서 `docs/service.md`를 F2 기준으로 갱신했습니다.

### 동작 메모

- 클릭 수는 중복을 제거하지 않습니다. 같은 사람의 새로 고침, 미리보기, 봇 요청도 모두 1씩 늘립니다.
- 별칭은 대소문자를 구분합니다(`My-Link`와 `my-link`는 별개). 예약어 비교만 대소문자를 무시합니다.
- 별칭의 앞뒤 공백은 잘라 내지 않으므로 공백이 있으면 `422`입니다.
- 별칭 `alias`가 빈 문자열(`""`)이면 API는 `422`, 화면은 무작위 코드입니다. `null`이나 필드 없음은 무작위 코드입니다.
- 통계 화면과 통계 API는 코드를 아는 누구에게나 공개됩니다(인증은 F3 범위).

### 알려진 제약 (minor, 기록만)

- 요청 수 제한이 없습니다(F3 범위). 리다이렉트마다 DB 쓰기가 일어나므로 대량 요청에서 쓰기 경합이 생길 수 있고, 클릭 수를 부풀릴 수 있습니다.
- F1 DB로 여러 프로세스가 같은 순간에 처음 시작하면 한쪽이 `duplicate column name`으로 시작에 실패할 수 있습니다. 다시 시작하면 정상입니다.
- `alias`가 문자열이 아닐 때의 422 본문은 FastAPI 기본 형식(`detail`이 배열)입니다. F1의 `url` 처리와 같습니다.
- 예약어가 설계서의 9개뿐이라 F3에서 추가될 경로를 미리 막지 않습니다.

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
