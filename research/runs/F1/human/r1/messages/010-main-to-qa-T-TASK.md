---
seq: 10
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-29T05:32:37.360Z"
agent: "qa"
agent_id: "aa7468d7770b0ba5c"
turn: 1
reply_to: null
chars: 640
tokens_est: 326
wait_s: null
---

F1 QA 1라운드다. 리뷰 체크포인트 커밋은 9f6fab9. 서버를 띄워 docs/features/F1.md의 수용 기준 AC-1~AC-23을 블랙박스로 검증해 줘.

- 승인된 해석: docs/plans/F1-plan.md 5절 (D-1 대문자 스킴 허용, D-2 공백/제어문자 422, D-4 Location은 ASCII 그대로·비ASCII만 퍼센트 인코딩, D-5 검증 실패 본문 {"detail": "<한국어 문구>"}, D-6 없는 코드는 HTML 404)
- 화면은 목업 docs/plans/mockups/F1-*.html과 문구·구조를 비교한다. CSS(/static/style.css)와 /static/copy.js가 실제로 제공되는지도 확인.
- AC-14는 서버를 같은 DB 경로로 재시작해서 확인.
- 경계 상황도 몇 가지 시도: 깨진 JSON, 한글 URL 리다이렉트, `https://[` 같은 이상한 호스트, 짝 없는 서로게이트 `{"url":"https://e.com/\ud800"}` (implementer가 500 가능성을 보고했다).
- Windows 환경이다. pytest는 쓰지 않고 curl로 요청한다. 끝나면 서버를 반드시 종료하고 포트가 비었는지 확인.

보고는 네 정의의 보고 형식으로 (Q-번호).
