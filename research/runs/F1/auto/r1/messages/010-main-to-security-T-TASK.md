---
seq: 10
sender: "main"
receiver: "security"
type: "T-TASK"
timestamp: "2026-10-29T04:45:30.986Z"
agent: "security"
agent_id: "a184f4afb29f737c5"
turn: 1
reply_to: null
chars: 457
tokens_est: 205
wait_s: null
---

F1(단축 URL 생성과 리다이렉트) 보안 점검 1라운드다. 리뷰 체크포인트: 62a0bf3.

- 대상: src/shortlink/** (api.py, web.py, validation.py, links.py, db.py, main.py, templates/, static/copy.js). 기능 전체 변경분은 `git diff 0e781ba..62a0bf3`.
- 설계서: docs/features/F1.md, 해석 결정: docs/plans/F1-decisions.md (D-2 공백/제어 문자 거절, D-3 RedirectResponse 퍼센트 인코딩 등).
- F1 범위 밖(설계서 "범위 밖"): 인증, 요청 수 제한은 F3에서 다룬다. 이 항목은 minor 이하로 기록만 하면 된다.
- `uv run bandit -r src -q`도 실행한다. 파일은 수정하지 않는다. 보고는 네 정의의 보고 형식으로.
