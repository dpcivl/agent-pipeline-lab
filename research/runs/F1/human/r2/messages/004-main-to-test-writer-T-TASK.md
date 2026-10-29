---
seq: 4
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-29T06:33:33.439Z"
agent: "test-writer"
agent_id: "ad935d2d159d0c840"
turn: 1
reply_to: null
chars: 1511
tokens_est: 714
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)의 pytest 테스트를 작성해 주세요. 구현은 다른 에이전트가 지금 동시에 진행 중이라 src/의 함수들은 아직 NotImplementedError 스텁일 수 있습니다. 테스트가 지금 실패하는 것은 정상입니다.

읽을 문서:
- 기능 설계서: docs/features/F1.md (수용 기준 AC-1~AC-23이 테스트의 기준)
- 구현 계획(사람 승인 완료): docs/plans/F1-plan.md — 특히 3절 인터페이스(검증 순서와 MSG_* 문구), 4절 화면별 고정 문구, 5절 수용 기준과 테스트 대응표, 6절 해석 결정 D-1~D-9
- 화면 목업: docs/plans/mockups/F1-home.html, F1-result.html, F1-input-error.html, F1-not-found.html (문구 기준)
- 스켈레톤: src/shortlink/validation.py, codes.py, links.py 등 (이름과 상수)
- 고정 픽스처: tests/conftest.py (settings, app, client — 확장만 가능)

할 일:
- 계획 5절의 대응표대로 tests/test_api_links.py, tests/test_redirect.py, tests/test_web.py를 만드세요. AC 하나마다 최소 하나의 테스트, 경계값과 실패 경로 포함. 테스트 이름이나 docstring에 AC 번호를 적어 주세요.
- 필요하면 tests/test_validation.py, tests/test_codes.py로 validate_url, generate_code 단위 테스트를 추가해도 됩니다.
- 리다이렉트 확인은 follow_redirects=False. AC-14는 같은 settings로 create_app을 다시 만들어 새 TestClient로 확인.
- AC-9, AC-19의 "저장하지 않음"은 settings.db_path에 sqlite3로 직접 연결해 SELECT COUNT(*) FROM links로 확인.
- 화면 테스트는 상태 코드, Content-Type text/html, 폼(method="post" action="/"), <label for="url">, name="url" 입력칸, 문구("줄이기", "복사", "다른 URL 줄이기", "링크를 찾을 수 없습니다", 오류 문구), href, 이스케이프(원문 "<script>" 없음, "&lt;script&gt;" 있음)를 확인하세요. 폼 제출은 client.post("/", data={"url": ...}).
- HTML 속성 순서나 공백 같은 세부 마크업에 지나치게 의존하지 않게 하세요(예: 정규식이나 html.parser로 요소/속성 확인). Jinja2 이스케이프는 따옴표를 &#34;/&#39;로 바꿀 수 있다는 점도 고려하세요.
- src/는 수정하지 마세요. 끝내기 전에 uv run ruff check tests, uv run ruff format tests를 실행하세요.

보고는 에이전트 정의의 보고 형식을 따르세요.
