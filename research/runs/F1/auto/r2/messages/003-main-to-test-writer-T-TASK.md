---
seq: 3
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-29T05:10:48.062Z"
agent: "test-writer"
agent_id: "ac6963e1736f78e26"
turn: 1
reply_to: null
chars: 1125
tokens_est: 539
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)의 수용 기준 테스트를 작성해 줘.

읽을 문서:
- 설계서: docs/features/F1.md (수용 기준 AC-1~AC-23)
- 구현 계획: docs/plans/F1-plan.md — 특히 "5. 수용 기준과 테스트 대응" 표, 3장의 오류 문구 표, 4장의 화면 고정 문구
- 해석 결정: docs/plans/F1-decisions.md (D-1 스킴 대소문자 무시, D-2 공백·제어 문자 422, D-3 Location의 비ASCII만 퍼센트 인코딩, D-4 422 본문 {"detail": ...}, D-5 없는 코드는 항상 404 HTML)
- 화면 목업: docs/plans/mockups/F1-home.html, F1-result.html, F1-error.html, F1-not-found.html

구현은 implementer가 동시에 진행 중이라 지금 src/shortlink/의 함수들은 NotImplementedError 스텁이다. 계획서의 인터페이스와 HTTP 동작 기준으로 써라(테스트가 지금 실패하는 것은 정상). 

요점:
- 파일: tests/test_api.py(AC-1~AC-15와 D-1~D-3 확인), tests/test_web.py(AC-16~AC-23). 필요하면 conftest.py에 픽스처를 추가만 한다(기존 settings, app, client 의미 유지).
- 리다이렉트 검증은 리다이렉트를 따라가지 않게(follow_redirects=False) 한다.
- 저장 여부(AC-9, AC-19)는 settings.db_path의 links 테이블 행 수를 sqlite3로 직접 센다.
- AC-14는 같은 settings로 create_app을 다시 불러 새 TestClient로 확인한다.
- AC-8 경계: 정확히 2,048자 URL은 201, 2,049자는 422.
- 화면 문구는 목업/계획서의 고정 문구를 기준으로 하되, 마크업 공백이나 속성 순서 차이로 깨지지 않게 너무 문자열 그대로 비교하지는 마라(필요하면 정규식이나 html.parser로 확인).
- 끝나기 전에 uv run ruff check tests, uv run ruff format tests를 실행한다.

보고는 네 정의의 보고 형식으로.
