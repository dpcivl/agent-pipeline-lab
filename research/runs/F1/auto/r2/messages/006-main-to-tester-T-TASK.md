---
seq: 6
sender: "main"
receiver: "tester"
type: "T-TASK"
timestamp: "2026-10-29T05:13:42.776Z"
agent: "tester"
agent_id: "a50bc98228f5625d2"
turn: 1
reply_to: null
chars: 446
tokens_est: 192
wait_s: null
---

F1 테스트를 실행하고 판정해 줘. 테스트 루프 1회차다.

- 설계서: docs/features/F1.md (AC-1~AC-23)
- 해석 결정: docs/plans/F1-decisions.md (D-1~D-9). 설계서에 없는 동작이라도 이 결정 기록에 있으면 기준으로 삼아라.
- 계획: docs/plans/F1-plan.md
- 테스트: tests/test_api.py, tests/test_web.py, tests/conftest.py

`uv run pytest -q`로 실행하고, 실패가 있으면 각각 code_bug / test_bug / spec_ambiguous로 분류해 네 정의의 보고 형식으로 보고해 줘. 린트(`uv run ruff check src tests`)와 포맷 확인(`uv run ruff format --check src tests`) 결과도 한 줄씩 덧붙여 줘.
