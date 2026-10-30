---
seq: 10
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-29T23:57:40.134Z"
agent: "qa"
agent_id: "a72746a8b0cb3d19c"
turn: 1
reply_to: null
chars: 714
tokens_est: 354
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) QA 1라운드입니다. 검증 대상은 커밋 e9f25fe의 작업 트리입니다.

- 설계서: docs/features/F2.md (AC-1~AC-23), 계획: docs/plans/F2-plan.md (해석 결정 D-F2-1~9는 사람 승인 완료, 기대 동작의 기준)
- 목업: docs/plans/mockups/F2-*.html
- 서버: `uv run uvicorn shortlink.main:create_app --factory`. 저장소의 shortlink.db를 건드리지 않도록 SHORTLINK_DB_PATH를 임시 경로로, 다른 서비스와 겹치지 않게 포트도 따로 지정하세요. 끝나면 서버를 꼭 종료하세요.
- 설계서의 "F1 시절 DB 파일 호환"은 QA 확인 대상입니다: F1 스키마(links: code TEXT PRIMARY KEY, url TEXT NOT NULL, created_at TEXT NOT NULL)로 만든 DB 파일에 행을 넣고 그 파일로 서버를 띄워, 기존 링크 리다이렉트와 clicks가 0부터 세어지는지 확인해 주세요.
- F1 수용 기준(docs/features/F1.md)도 주요 흐름을 다시 확인해 주세요.

HTTP 요청으로 블랙박스 검증하고, AC별 PASS/FAIL과 발견한 문제를 blocker / major / minor 심각도, 재현 절차와 함께 Q-1, Q-2처럼 번호를 붙여 보고해 주세요.
