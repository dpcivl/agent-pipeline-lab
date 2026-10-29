# CHANGELOG

기능별 변경 기록입니다. 최신 항목이 위에 옵니다.

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
