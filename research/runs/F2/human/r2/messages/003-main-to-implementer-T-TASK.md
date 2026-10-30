---
seq: 3
sender: "main"
receiver: "implementer"
type: "T-TASK"
timestamp: "2026-10-30T00:38:39.138Z"
agent: "implementer"
agent_id: "a6f57ffdc2a6f9660"
turn: 1
reply_to: null
chars: 1393
tokens_est: 603
wait_s: null
---

F2(클릭 통계와 커스텀 별칭)를 구현해 줘. 사람이 계획과 목업을 승인했다.

읽을 문서:
- 설계서: docs/features/F2.md
- 구현 계획(인터페이스, 문구, 결정 D2-1~D2-9): docs/plans/F2-plan.md — 특히 2, 3, 5절
- 화면 목업(문구, 배치, 클래스, 색의 기준): docs/plans/mockups/F2-index.html, F2-home.html, F2-result.html, F2-error-alias.html, F2-error-duplicate.html, F2-stats.html, F2-stats-empty.html
- 고정 계약: CLAUDE.md

할 일 (쓰기 영역: src/shortlink/** 만):
1. 스텁 구현: validation.validate_alias, db.ensure_click_columns, repository(Link 새 필드, create(url, alias), get이 새 열 읽기, record_click, AliasTakenError), api(LinkIn.alias, 422/409, GET /links/{code}/stats), web(폼 alias 처리, error_field/url_value/alias_value 컨텍스트, result.html에 code, GET /stats/{code}, follow_link이 record_click 사용, display_timestamp).
2. 템플릿: home.html(별칭 칸, 안내 문구, 오류 표시 방식은 목업 그대로), result.html("통계 보기" 링크와 .result-actions), 새 stats.html(base.html 상속).
3. style.css 끝에 목업의 "F2 추가 스타일" 블록을 그대로 덧붙인다. F1 공통 스타일은 바꾸지 않는다.

지켜야 할 것:
- F1 동작과 F1 결정(docs/plans/F1-plan.md 5절 D-1~D-11)을 깨지 않는다. 기존 테스트 tests/*.py가 계속 통과해야 한다(tests/는 고치지 않는다. 테스트는 test-writer가 동시에 작성 중이다).
- SQL은 모두 파라미터 바인딩, 연결은 호출마다 열고 닫는다(contextlib.closing). 클릭 증가는 SQL 안에서(clicks = clicks + 1).
- Jinja2 자동 이스케이프 유지, |safe/Markup 금지. 인라인 스크립트 금지(CSP).
- 계획서와 다르게 해야 할 이유가 생기면 임의로 바꾸지 말고 보고에 적어 줘.

끝나면 `uv run ruff check src tests`, `uv run ruff format src`, `uv run pytest -q`(기존 테스트)를 돌리고 결과와 함께 바꾼 파일 목록, 계획과 다른 점을 짧게 보고해 줘. 커밋은 하지 않는다.
