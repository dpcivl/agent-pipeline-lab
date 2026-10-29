---
seq: 10
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-29T02:21:21.696Z"
agent: "qa"
agent_id: "aed70ddfd3bef930d"
turn: 1
reply_to: null
chars: 756
tokens_est: 400
wait_s: null
---

F1(단축 URL 생성과 리다이렉트) QA 1라운드입니다. 리뷰 체크포인트는 `62afa74`입니다.

- 기준: 설계서 `docs/features/F1.md`의 AC-1~AC-23, 화면 문구와 구조는 목업 `docs/plans/mockups/F1-home.html`, `F1-result.html`, `F1-input-error.html`, `F1-not-found.html`, 설계서가 정하지 않은 부분은 `docs/plans/F1-plan.md` 4절(화면 규칙)과 7절(해석 결정 D-1~D-9)
- 에이전트 정의의 절차대로 임시 DB와 포트 8765로 서버를 띄워 블랙박스로 검증하세요.
- 모든 AC를 수용 기준 검증 표에 넣어 주세요. AC-14는 서버를 같은 DB 경로로 재시작해서 확인합니다. AC-13은 반복 요청으로 확인합니다. 화면은 폼 제출(`--data-urlencode`)로 결과·입력 오류 화면을 받고, `/static/style.css`, `/static/copy.js`가 제공되는지도 봐 주세요.
- 경계 상황도 시도해 보세요: 2,048/2,049자, 스킴 대문자(`HTTPS://`), 공백·개행이 든 URL, 비ASCII URL의 리다이렉트, 잘못된 JSON 본문, 폼에서 `url` 필드 누락, `/favicon.ico` 같은 코드가 아닌 경로, `<script>`가 든 URL.
- 끝나면 서버를 반드시 종료하고 포트가 비었는지 확인하세요. 파일은 수정하지 않습니다. 보고는 에이전트 정의의 형식을 따릅니다.
