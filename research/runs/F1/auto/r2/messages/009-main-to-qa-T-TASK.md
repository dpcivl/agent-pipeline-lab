---
seq: 9
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-29T05:14:11.249Z"
agent: "qa"
agent_id: "a11b9ec634215fd51"
turn: 1
reply_to: null
chars: 560
tokens_est: 299
wait_s: null
---

F1 QA 1라운드를 해 줘. 리뷰 체크포인트 커밋은 166f2b6(HEAD)이다.

서버를 실제로 띄워 설계서 docs/features/F1.md의 AC-1~AC-23을 모두 HTTP 요청으로 검증해 줘. 해석 결정 docs/plans/F1-decisions.md(D-1~D-9)에 적힌 동작도 기준으로 삼는다(예: 공백이 든 URL 422, Location의 비ASCII만 퍼센트 인코딩, 없는 코드는 항상 404 HTML). 화면은 홈 → 폼 제출(성공/실패) → 결과 링크 → 리다이렉트 흐름으로 확인하고, HTML의 문구·링크·오류 표시를 목업(docs/plans/mockups/F1-home.html, F1-result.html, F1-error.html, F1-not-found.html)과 비교해 줘. /static/style.css, /static/copy.js가 제공되는지도 확인해라.

AC-14는 같은 DB 파일로 서버를 재시작한 뒤 이전 코드로 리다이렉트되는지로 확인한다. 끝나면 서버를 반드시 종료하고 포트가 비었는지 확인해라. 네 정의의 보고 형식(Q-번호)으로 보고해 줘.
