# Changelog

이 파일은 기능별 변경 기록입니다. 최신 변경이 위에 옵니다.

## F1: 단축 URL 생성과 리다이렉트 (2026-10-29)

설계서: `docs/features/F1.md` (v2)

### 추가

- `POST /links`: JSON `{"url": ...}`을 받아 7자 무작위 코드로 저장하고 `201`로 `code`, `short_url`, `url`, `created_at`(UTC ISO 8601)을 돌려줍니다.
- `GET /{code}`: 코드가 있으면 `302`와 `Location`(원래 URL), 없으면 `404` 화면을 돌려줍니다.
- 웹 화면 4개: 홈 `GET /`, 결과 `POST /`(200), 입력 오류 `POST /`(422, 입력값 유지), 찾을 수 없음(404). 결과 화면에는 단축 URL 링크와 "복사" 버튼(브라우저 JavaScript)이 있습니다.
- URL 검증 규칙: 빈 값, 문자열 아님, 2,048자 초과, 서로게이트, 공백과 제어 문자, `http`/`https` 외 스킴, 호스트 없음을 `422`로 거절합니다. 거절 시 저장하지 않습니다.
- 오류 문구는 API의 `detail`과 화면에서 같은 한국어 문구를 씁니다.
- 설정: 환경 변수 `SHORTLINK_DB_PATH`(기본 `shortlink.db`), `SHORTLINK_BASE_URL`(기본 `http://localhost:8000`).
- `create_app()`: 라우터 등록과 DB 스키마 준비까지 끝낸 앱을 반환합니다.
- 서비스 사용법 문서: `docs/service.md`.

### 해석 결정 (`docs/plans/F1-decisions.md`)

- 스킴 대소문자는 무시합니다(D-1).
- 공백과 제어 문자가 든 URL은 거절합니다(D-2).
- `Location`은 출력 가능한 ASCII를 그대로 두고 비ASCII만 UTF-8 퍼센트 인코딩합니다(D-3, 리뷰 후 개정).
- 없는 코드는 형식과 관계없이 항상 404 화면을 보여 줍니다(D-5).
- 짝이 없는 서로게이트가 든 URL은 `422`로 거절합니다(D-8, 리뷰 중 추가).

### 검증

- 테스트 253개 통과, `ruff check`, `ruff format --check`, `bandit` 지적 없음.
- 리뷰 2라운드에서 blocker와 major가 0건이 되었습니다. 남은 minor 지적은 `docs/plans/F1-report.md` 3절에 기록되어 있습니다.

### 알려진 제한

- 인증, 요청 수 제한, 본문 크기 제한이 없습니다(F3 범위).
- 보안 응답 헤더가 없고 `/docs`, `/openapi.json`이 공개됩니다.
- `\`를 `Location`에 그대로 내보냅니다. 호스트 기반 차단을 도입하기 전에 이 문자를 거절해야 합니다.
