---
seq: 4
sender: "main"
receiver: "test-writer"
type: "T-TASK"
timestamp: "2026-10-29T05:28:46.563Z"
agent: "test-writer"
agent_id: "ad099a69ee132ab3c"
turn: 1
reply_to: null
chars: 1544
tokens_est: 699
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)의 테스트를 작성해 줘. 사람이 계획과 목업을 승인했고, implementer가 동시에 src/를 구현하고 있다(지금은 스텁이라 테스트가 실패해도 정상).

읽을 것:
- 설계서: docs/features/F1.md (수용 기준 AC-1~AC-23이 테스트의 기준)
- 구현 계획: docs/plans/F1-plan.md (4절 AC↔테스트 대응표, 3절 인터페이스, 5절 승인된 해석 D-1~D-8)
- 화면 목업(문구 기준): docs/plans/mockups/F1-home.html, F1-result.html, F1-error.html, F1-not-found.html
- 스켈레톤 인터페이스: src/shortlink/validation.py, codes.py, repository.py (LinkRepository(db_path, code_factory=...)), web.py
- 픽스처: tests/conftest.py (settings, app, client; 확장만 가능)

작성할 파일 (계획 4절 그대로):
- tests/test_api_links.py: AC-1~9, 13, 15
- tests/test_redirect.py: AC-10, 11, 12, 14 (리다이렉트는 follow_redirects=False)
- tests/test_web.py: AC-16~23 (폼 제출은 data={"url": ...}, 결과/오류/404 HTML 검증, 네 화면 모두 lang="ko"와 viewport)
- tests/test_validation.py: 규칙 순서와 MSG_* 문구, 대문자 스킴 허용(D-1), 공백/줄바꿈 거절(D-2), 2048/2049 경계
- tests/test_repository.py: code_factory로 충돌 재시도, 계속 충돌하면 RuntimeError
- 추가로 D-4: 한글 경로 URL(예: https://example.com/경로) 리다이렉트가 500이 아니라 302이고 Location이 퍼센트 인코딩된 값인지, ASCII URL은 Location이 원문과 글자 그대로 같은지.

주의:
- AC-9, AC-19의 "저장하지 않음"은 settings.db_path의 links 테이블 행 수를 sqlite3로 직접 세서 확인한다(헬퍼 픽스처를 conftest에 추가해도 된다). 연결은 꼭 닫는다(Windows tmp 정리 문제).
- AC-20: 원문 "<script>alert(1)" 같은 태그 문자열이 HTML에 그대로 나오지 않고 이스케이프된 형태가 있는지 확인. 결과 화면용 입력은 https://example.com/<script>alert(1)</script> 처럼 유효한 URL로, 오류 화면용은 <script>alert(1)</script>로.
- 화면 문구 검증은 목업 문구 기준이되, 마크업 공백 차이에 깨지지 않도록 핵심 문구 포함 여부와 속성 위주로 검사한다.
- src/는 수정하지 않는다. 끝나기 전에 uv run ruff check tests, uv run ruff format tests.

보고는 네 정의의 보고 형식으로.
