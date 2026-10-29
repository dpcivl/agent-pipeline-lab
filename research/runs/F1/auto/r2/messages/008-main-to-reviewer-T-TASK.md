---
seq: 8
sender: "main"
receiver: "reviewer"
type: "T-TASK"
timestamp: "2026-10-29T05:14:11.238Z"
agent: "reviewer"
agent_id: "af6cc410cc44344fc"
turn: 1
reply_to: null
chars: 623
tokens_est: 291
wait_s: null
---

F1 코드 리뷰 1라운드를 해 줘. 리뷰 체크포인트 커밋은 166f2b6(HEAD)이고, 기준 스냅샷 e8f75ad 이후의 F1 변경 전체가 대상이다(`git diff e8f75ad..166f2b6`).

- 설계서: docs/features/F1.md (AC-1~AC-23)
- 계획: docs/plans/F1-plan.md
- 해석 결정: docs/plans/F1-decisions.md (D-1~D-9). 결정 기록에 있는 동작은 설계서 위반으로 보지 말고, 결정 자체가 문제라고 판단하면 근거와 함께 지적해라.
- 목업: docs/plans/mockups/F1-*.html
- 코드: src/shortlink/ (main.py, codes.py, validation.py, storage.py, api.py, web.py, templates/, static/)
- 테스트: tests/ (현재 89개 모두 통과)
- 고정 계약: CLAUDE.md

참고로 implementer가 남긴 질문이 하나 있다: 짝 없는 서로게이트 문자(JSON "\ud800")가 든 URL이 검증을 통과해 저장 시 500이 날 수 있다는 것. 이것도 판단에 포함해 줘.

네 정의의 보고 형식(R-번호, 심각도)으로 보고해 줘.
