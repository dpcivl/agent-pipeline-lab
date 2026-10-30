---
seq: 9
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-29T07:19:05.636Z"
agent: "qa"
agent_id: "a3459ae8c94d484cc"
turn: 1
reply_to: null
chars: 635
tokens_est: 307
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) QA 1라운드다. 리뷰 체크포인트: 34689f1.

- 설계서: docs/features/F2.md(AC-1~AC-23), 해석 결정: docs/plans/F2-decisions.md, 목업: docs/plans/mockups/F2-index.html 과 F2-*.html
- 서버를 임시 DB와 별도 포트로 띄워 AC-1~AC-22를 블랙박스로 확인하고, F1 주요 흐름(생성 201, 302, 404, 폼 422)도 회귀 확인한다.
- 설계서 호환성 항목 "F1 시절에 만든 DB 파일로 앱을 시작해도 기존 링크가 동작하고 클릭 수는 0부터"도 확인한다: 저장소 밖이 아닌 임시 디렉터리에 sqlite3(파이썬 표준 라이브러리, `uv run python -c ...`)로 F1 스키마 `links(code TEXT PRIMARY KEY, url TEXT NOT NULL, created_at TEXT NOT NULL)`와 행 하나를 만든 뒤 그 파일로 서버를 띄워 리다이렉트와 통계(clicks 0부터)를 확인한다.
- 폼 제출에는 `--data-urlencode "url=..." --data-urlencode "alias=..."`를 쓴다.
- 끝나면 서버를 반드시 종료하고 포트를 확인한다.
