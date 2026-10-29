---
seq: 9
sender: "main"
receiver: "reviewer"
type: "T-TASK"
timestamp: "2026-10-29T05:32:37.351Z"
agent: "reviewer"
agent_id: "a99e7ca7e2a22575b"
turn: 1
reply_to: null
chars: 482
tokens_est: 238
wait_s: null
---

F1 리뷰 1라운드다. 리뷰 체크포인트 커밋은 9f6fab9 (기준 비교: 214eec8은 스켈레톤, d1ad59f는 기능 이전 상태). 테스트 152개 통과, ruff 통과 상태다.

- 설계서: docs/features/F1.md
- 승인된 계획: docs/plans/F1-plan.md (5절 D-1~D-8은 사람이 승인한 해석이라 그 자체는 지적 대상이 아니다. 구현이 이를 제대로 따르는지는 본다)
- 목업: docs/plans/mockups/F1-*.html
- 검토 대상: src/shortlink/** (템플릿, static 포함), tests/**
- 참고: implementer가 짝 없는 서로게이트(`{"url": "https://e.com/\ud800"}`)가 든 url이 sqlite 바인딩에서 UnicodeEncodeError로 500이 난다고 스스로 보고했다. 이것도 판단에 포함해 줘.

보고는 네 정의의 보고 형식으로 (R-번호).
