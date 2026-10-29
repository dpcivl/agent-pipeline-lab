---
seq: 21
sender: "main"
receiver: "qa"
type: "T-REREVIEW"
timestamp: "2026-10-29T04:52:25.549Z"
agent: "qa"
agent_id: "a60810b096cc659b6"
turn: 2
reply_to: null
chars: 741
tokens_est: 359
wait_s: null
---

F1 QA 2라운드를 진행해 줘. 직전 리뷰 체크포인트는 62a0bf3, 이번 체크포인트는 5c61fc4다. 변경분은 `git diff 62a0bf3..5c61fc4 --stat`로 확인할 수 있다. 1라운드 지적은 없었다.

이번에 바뀐 동작만 서버를 띄워 확인하면 된다.
1) 리다이렉트 Location (D-3 개정, docs/plans/F1-decisions.md)
   - 출력 가능한 ASCII는 글자 그대로 나간다. 예: `https://example.com/?a=1|2&b={x}`, `https://example.com/<script>alert(1)</script>`, 이미 인코딩된 `%20`
   - 비ASCII(한글)만 UTF-8 퍼센트 인코딩된다.
   - AC-10과 AC-23의 리다이렉트도 다시 확인한다.
2) 서로게이트 거절 (D-8)
   - POST /links에 JSON 원문 `{"url":"https://a.com/\ud800"}`를 보내면 422 `{"detail":"URL에 쓸 수 없는 문자가 들어 있습니다."}`가 오고 아무것도 저장되지 않아야 한다.
   - 짝이 맞는 `😀`은 201이어야 한다.
3) 기본 회귀로 AC-1, AC-10, AC-17도 한 번씩 확인한다.

서버는 반드시 종료하고, 포트가 비었는지 확인한다. 파일은 수정하지 않는다. 결과는 네 보고 형식으로 알려 줘.

Address this before completing your current task.
