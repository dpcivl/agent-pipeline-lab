---
seq: 2
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-29T05:10:48.048Z"
agent: "implementer"
agent_id: "a46510386cb9984ad"
turn: 1
reply_to: null
chars: 1314
tokens_est: 623
wait_s: null
---

F1(단축 URL 생성과 리다이렉트)을 구현해 줘.

읽을 문서:
- 설계서: docs/features/F1.md (수용 기준 AC-1~AC-23)
- 구현 계획: docs/plans/F1-plan.md (모듈 구조, 인터페이스, 검증 순서와 오류 문구, 화면 문구와 마크업 요점)
- 해석 결정: docs/plans/F1-decisions.md (D-1~D-7, 특히 D-2 공백·제어 문자 거절, D-3 Location 헤더의 비ASCII만 퍼센트 인코딩)
- 화면 목업: docs/plans/mockups/F1-home.html, F1-result.html, F1-error.html, F1-not-found.html (F1-index.html은 목록)

스켈레톤이 이미 있다: src/shortlink/codes.py, validation.py, storage.py, api.py, web.py는 시그니처와 docstring만 있는 스텁이고, main.py의 create_app()에는 저장소 생성·스키마 준비·라우터 등록이 연결되어 있다. 스텁을 채우고 다음을 새로 만든다:
- src/shortlink/templates/: base.html, home.html(홈과 입력 오류 겸용), result.html, not_found.html
- src/shortlink/static/style.css: 목업의 <style> 블록에서 ".mockup-note"(목업 전용)를 뺀 나머지와 같게
- src/shortlink/static/copy.js: 목업 result 화면의 인라인 스크립트 동작을 그대로 옮김 (클립보드 API가 없을 때도 오류 없이)

요점:
- 템플릿은 목업의 마크업 구조, 클래스 이름, 문구를 그대로 따른다. 목업 전용 안내 줄(.mockup-note)과 결과 화면의 인라인 <script>는 실제 화면에 넣지 않는다.
- Jinja2 자동 이스케이프를 유지하고 |safe, Markup은 쓰지 않는다.
- 고정 계약(CLAUDE.md): create_app(settings=None), Settings, 환경 변수 이름은 바꾸지 않는다. 확장만.
- 테스트는 test-writer가 동시에 tests/test_api.py, tests/test_web.py로 쓰고 있다. tests/는 건드리지 마라. 간단한 자체 확인은 임시 스크립트 없이 `uv run python -c ...`나 TestClient로 해도 된다(저장소 밖 경로와 저장소 안 임시 파일은 만들지 마라).
- 끝나기 전에 uv run ruff check src, uv run ruff format src를 실행한다.

보고는 네 정의의 보고 형식으로.
