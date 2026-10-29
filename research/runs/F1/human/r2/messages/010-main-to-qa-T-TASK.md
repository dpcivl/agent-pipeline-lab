---
seq: 10
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-29T06:38:02.713Z"
agent: "qa"
agent_id: "aa0e6b6432eadb203"
turn: 1
reply_to: null
chars: 648
tokens_est: 328
wait_s: null
---

F1(단축 URL 생성과 리다이렉트) QA 1라운드입니다. 리뷰 체크포인트: 92f903f (현재 HEAD).

- 설계서: docs/features/F1.md — AC-1~AC-23을 서버를 실제로 띄워 HTTP 요청으로 블랙박스 검증해 주세요.
- 구현 계획(사람 승인 완료): docs/plans/F1-plan.md — 3절 검증 문구, 4절 화면 문구, 6절 해석 결정 D-1~D-9를 기대값으로 삼으세요.
- 목업: docs/plans/mockups/F1-home.html, F1-result.html, F1-input-error.html, F1-not-found.html — 받은 HTML의 문구, 링크, 오류 표시를 비교.
- AC-14(재시작 후 리다이렉트)는 같은 DB 경로로 서버를 껐다 다시 띄워 확인해 주세요.
- 경계 상황도 확인: 2048/2049자, 공백 포함 URL, 비ASCII URL의 Location, JSON이 아닌 본문, url 필드 없는 폼 제출, GET /links, /static/style.css 등.
- 끝나면 서버를 반드시 종료하고 포트가 비었는지 확인하세요(Windows면 taskkill //F //T //PID).

파일은 수정하지 말고, 에이전트 정의의 보고 형식(Q-번호, 심각도)으로 보고해 주세요.
