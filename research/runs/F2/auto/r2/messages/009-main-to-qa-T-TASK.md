---
seq: 9
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-29T08:19:41.706Z"
agent: "qa"
agent_id: "a6233e35397c5401e"
turn: 1
reply_to: null
chars: 795
tokens_est: 395
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) QA 1라운드다. 검증 대상 커밋은 `b42b3bb`.

서버를 실제로 띄워(`uv run uvicorn shortlink.main:create_app --factory`, 임시 DB 경로와 빈 포트를 `SHORTLINK_DB_PATH`, `--port`로 지정) HTTP 요청으로 `docs/features/F2.md`의 수용 기준 AC-1~AC-22를 블랙박스로 검증해 줘. AC-23은 F1 핵심 흐름(생성 201, 302 리다이렉트, 없는 코드 404, 홈/결과/오류 화면)을 간단히 확인하면 된다.

꼭 확인할 것:
- 설계서 "호환성" 절: F1 시절 DB 파일(3열 스키마: `code TEXT PRIMARY KEY, url TEXT NOT NULL, created_at TEXT NOT NULL`)을 sqlite3로 직접 만들어 행을 넣고 그 파일로 서버를 시작했을 때 기존 링크가 302로 동작하고 클릭 수가 0부터 세어지는지.
- 화면: `GET /`, 폼 제출(성공/422/409), `GET /stats/{code}`(접근 전 "아직 없음", 접근 후), 없는 코드 통계 화면 404. 문구와 구조를 목업 `docs/plans/mockups/F2-*.html`과 비교.
- 해석 결정은 `docs/plans/F2-plan.md` 5절 참고.

끝나면 서버 프로세스를 반드시 종료하고 임시 파일을 정리해 줘. 각 AC의 PASS/FAIL과 근거(요청, 응답 요약), 발견한 문제는 blocker / major / minor 심각도로 보고해 줘. 파일은 수정하지 않는다.
