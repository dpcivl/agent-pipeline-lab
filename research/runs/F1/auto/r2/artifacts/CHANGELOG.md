# Changelog

기능별 변경 기록입니다. 최신 항목이 위에 옵니다.

## F1: 단축 URL 생성과 리다이렉트 (2026-10-29)

설계서: `docs/features/F1.md` v2. 해석 결정: `docs/plans/F1-decisions.md`(D-1~D-10). 실행 보고서: `docs/plans/F1-report.md`.

### 추가

- `POST /links` (JSON API): `{"url": ...}`을 받아 7자 무작위 코드로 저장하고 `201`로 `code`, `short_url`, `url`, `created_at`(UTC, 초 단위, `Z`)을 돌려줍니다.
- `GET /{code}`: 저장된 원래 URL로 `302 Found`와 `Location` 헤더를 보냅니다. 없는 코드는 `404`와 안내 화면을 돌려줍니다.
- URL 검증 (API와 화면 공통): 값 없음·문자열 아님·빈 값, 2,048자 초과, 공백과 제어 문자, 짝 없는 서로게이트 문자, `http`/`https` 외 스킴, 호스트 없음을 `422`로 거절합니다. 거절된 요청은 저장하지 않습니다.
- 웹 화면 (Jinja2, `<html lang="ko">`, viewport 설정): 홈(`GET /`, URL 입력 폼), 결과(`POST /` 성공), 입력 오류(`POST /` 실패, 입력값 유지), 찾을 수 없음(없는 코드).
- 결과 화면의 "복사" 버튼 (브라우저 JavaScript, 2초 동안 "복사됨"). JavaScript가 꺼져 있어도 단축 URL 링크는 보입니다.
- 환경 변수 `SHORTLINK_DB_PATH`(기본 `shortlink.db`), `SHORTLINK_BASE_URL`(기본 `http://localhost:8000`, 끝의 `/`는 제거).
- SQLite 저장 (표준 라이브러리 `sqlite3`): 서버 시작 시 `links` 테이블을 만들고, 같은 DB 파일로 다시 시작해도 기존 코드가 동작합니다.
- `Location` 헤더에서만 비ASCII 문자를 UTF-8 퍼센트 인코딩합니다. 저장과 API 응답은 받은 그대로입니다.
- 스킴 비교는 대소문자를 구분하지 않습니다.

### 알려진 제한 (F1 범위 밖, 후속 기능에서 다룸)

- 커스텀 별칭, 클릭 통계: F2
- 인증, 만료, 삭제, 요청 수 제한: F3
- URL 정규화와 중복 URL 합치기: 하지 않음
- 생성한 링크 목록 조회: 아직 없음
