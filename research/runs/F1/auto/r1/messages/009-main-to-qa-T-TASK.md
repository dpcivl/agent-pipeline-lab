---
seq: 9
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-29T04:45:30.974Z"
agent: "qa"
agent_id: "a60810b096cc659b6"
turn: 1
reply_to: null
chars: 535
tokens_est: 271
wait_s: null
---

F1(단축 URL 생성과 리다이렉트) QA 1라운드다. 리뷰 체크포인트: 62a0bf3.

- 설계서: docs/features/F1.md의 AC-1~AC-23을 서버를 실제로 띄워 블랙박스로 검증한다.
- 해석 결정: docs/plans/F1-decisions.md (D-1~D-7, 확정 해석). 오류 문구는 docs/plans/F1-plan.md 3.2 표, 화면 고정 요소는 3.6, 목업은 docs/plans/mockups/F1-*.html.
- 임시 DB와 포트 8765를 쓰고, AC-14는 서버를 같은 DB 경로로 재시작해서 확인한다. 임시 DB는 저장소 밖(mktemp)이어도 되지만 저장소 안 파일은 만들지 말고, 서버는 반드시 종료하고 포트가 비었는지 확인한다.
- JSON API와 폼 제출(--data-urlencode), 404 화면, /static/style.css·/static/copy.js 서빙, 경계(2,048/2,049자), 이스케이프(AC-20)까지 본다.
- 파일은 수정하지 않는다. 보고는 네 정의의 보고 형식으로.
