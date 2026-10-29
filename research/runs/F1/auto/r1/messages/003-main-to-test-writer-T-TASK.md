---
seq: 3
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-29T04:40:41.726Z"
agent: "test-writer"
agent_id: "a3c9dd2bf4b0cc4ad"
turn: 1
reply_to: null
chars: 1774
tokens_est: 817
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)의 pytest 테스트를 tests/에 작성해 줘. implementer가 동시에 src/를 구현하고 있어서 지금은 스텁(NotImplementedError)만 있다. 테스트가 지금 실패하는 건 정상이다.

읽을 것:
- 설계서: docs/features/F1.md (AC-1~AC-23). 테스트의 기준은 이 수용 기준이다.
- 구현 계획: docs/plans/F1-plan.md — 인터페이스(3.1 DB 스키마 `links(code, url, created_at)`, 3.2 검증 순서와 오류 문구, 3.3 서비스 함수, 3.5 웹 라우트), 3.6 화면 고정 요소, 4절 AC-테스트 파일 대응표.
- 해석 결정: docs/plans/F1-decisions.md (D-1~D-7)
- 화면 목업: docs/plans/mockups/F1-home.html, F1-result.html, F1-error.html, F1-not-found.html. 문구 기준.
- 고정 픽스처: tests/conftest.py (settings, app, client). 확장만 가능.

요청:
- 계획 4절의 파일 구성(test_api_create.py, test_api_validation.py, test_redirect.py, test_persistence.py, test_web.py, test_validation.py)을 따른다. AC마다 최소 하나의 테스트, 테스트 이름이나 docstring에 AC 번호를 넣는다.
- 리다이렉트 테스트는 client.get(..., follow_redirects=False)로 302와 Location을 확인한다.
- AC-9/AC-19 "저장 없음"은 settings.db_path의 links 테이블 행 수를 sqlite3로 세서 확인한다(필요하면 conftest에 헬퍼 픽스처 추가).
- AC-8 경계: 정확히 2,048자/2,049자인 https URL을 만들어 확인.
- AC-14: 같은 settings로 create_app을 다시 만들어 새 TestClient로 확인.
- AC-15: created_at이 `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` 형식이고 요청 시각과 60초 이내.
- AC-20: `<script>`가 든 URL(예: `https://example.com/<script>alert(1)</script>`)을 폼으로 성공 제출, 그리고 오류가 나는 값(예: `javascript:<script>alert(1)</script>`)으로 제출해서 응답 HTML에 원문 `<script>alert(1)</script>`가 없고 이스케이프된 형태가 있는지 확인.
- 화면 문구는 계획 3.6과 목업의 문자열(예: "줄이기", "복사", "다른 URL 줄이기", "링크를 찾을 수 없습니다", "홈으로 가기", 오류 문구)로 확인하되, 공백·속성 순서 같은 사소한 마크업 차이에 깨지지 않게 정규식이나 간단한 HTML 파싱(html.parser)을 써라. 새 의존성은 추가하지 않는다.
- 결정 D-1(대문자 스킴 허용), D-2(공백/제어 문자 거절), D-7(폼 url 누락 → 422 HTML)도 테스트한다.
- 끝나면 `uv run ruff check tests`, `uv run ruff format tests` 실행. `uv run pytest --collect-only -q`로 수집 오류가 없는지 확인.
- src/는 건드리지 않는다. 저장소 밖 경로는 쓰지 않는다. git 커밋은 하지 않는다.

보고는 네 정의의 보고 형식으로.
