---
seq: 21
sender: "main"
receiver: "qa"
type: "T-REREVIEW"
timestamp: "2026-10-29T05:19:18.621Z"
agent: "qa"
agent_id: "a11b9ec634215fd51"
turn: 2
reply_to: null
chars: 469
tokens_est: 238
wait_s: null
---

F1 QA 2라운드다. 직전 리뷰 체크포인트는 166f2b6, 이번은 36183ce(HEAD). 변경분은 `git diff 166f2b6..36183ce --stat`로 확인해라(서로게이트 거절 D-10 추가). 서버를 새 임시 DB로 다시 띄워 ① Q-1이 해결됐는지(POST /links {"url":"https://a.com/\ud800"} 및 원시 바이트 \xed\xa0\x80 → 422, detail "URL에 쓸 수 없는 문자가 있습니다.", 미저장) ② 변경과 관련된 동작(정상 비ASCII/이모지 URL은 여전히 201과 리다이렉트, 기존 검증 문구 유지)만 다시 확인해 줘. Q-2, Q-3 minor는 반영하지 않기로 했으니 "미반영(minor)"로만 적어라. 끝나면 서버 종료와 포트 해제를 확인하고 이전 형식으로 보고해 줘.

Address this before completing your current task.
