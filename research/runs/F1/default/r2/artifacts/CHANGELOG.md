# Changelog

기능별 변경 기록입니다. 최신 항목이 위에 옵니다.

## F1 — 단축 URL 생성과 리다이렉트 (2026-10-29)

설계서: `docs/features/F1.md` v2

### 추가

- JSON API `POST /links`: URL을 받아 7자 무작위 코드를 만들고 `201`로 `code`, `short_url`, `url`, `created_at`을 돌려줍니다.
- 리다이렉트 `GET /{code}`: 저장된 코드는 `302`와 `Location`으로 원래 URL로 보내고, 없는 코드는 `404` 화면을 보냅니다.
- 웹 화면(한국어, Jinja2 서버 렌더링): 홈(`GET /`), 결과와 입력 오류(`POST /`), 찾을 수 없음 화면. 결과 화면에는 "복사" 버튼(JavaScript)과 "다른 URL 줄이기" 링크가 있고, JavaScript가 꺼져 있어도 링크가 보입니다.
- URL 검증: `http`/`https` 스킴(대소문자 무시), 호스트 필수, 2,048자 이하, 빈 값과 공백·제어 문자 거절. API와 웹 폼이 같은 규칙을 씁니다.
- SQLite 저장(표준 라이브러리 `sqlite3`): `SHORTLINK_DB_PATH`에 저장하며, 같은 파일로 앱을 다시 띄워도 이전 코드가 동작합니다.
- 환경 변수 `SHORTLINK_DB_PATH`(기본 `shortlink.db`), `SHORTLINK_BASE_URL`(기본 `http://localhost:8000`).
- 서비스 문서 `docs/service.md`.

### 참고

- 검증에 걸린 요청은 저장하지 않습니다.
- 같은 URL을 여러 번 줄이면 요청마다 새 코드를 만들며 중복을 합치지 않습니다.
- 정규화(앞뒤 공백 제거, 대소문자 변경)는 하지 않습니다. 공백이 있는 URL은 잘라내지 않고 거절합니다.
- 설계 해석 결정은 `docs/plans/F1-plan.md` 7절과 `docs/plans/F1-decisions.md`에 있습니다.
