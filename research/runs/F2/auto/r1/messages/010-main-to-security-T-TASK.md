---
seq: 10
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-29T07:19:05.653Z"
agent: "security"
agent_id: "a07e766323a926f72"
turn: 1
reply_to: null
chars: 459
tokens_est: 249
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) 보안 점검 1라운드다. 리뷰 체크포인트: 34689f1. F2 전체 변경은 `git diff 4cf5823..34689f1`.

- 설계서: docs/features/F2.md, 해석 결정: docs/plans/F2-decisions.md (E-13: 통계는 코드를 아는 누구나 볼 수 있음 — 인증은 F3 범위이므로 그 자체는 지적 대상이 아님)
- 볼 것: 별칭 입력 검증(문자 규칙 우회, 유니코드, 줄바꿈, 예약어로 라우트 가리기), 별칭이 경로·헤더·HTML에 들어갈 때 문제, 통계 화면 XSS와 href, SQL 파라미터 바인딩(마이그레이션의 ALTER 문 포함), 409/404 응답의 정보 노출, 클릭 집계 조작 가능성, bandit 결과(`uv run bandit -r src -q`).
- F1에서 결정된 보안 헤더(CSP, nosniff)가 새 화면에도 붙는지 확인.
