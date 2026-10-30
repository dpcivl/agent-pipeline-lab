---
seq: 14
sender: "main"
receiver: "doc-keeper"
type: "T-TASK"
timestamp: "2026-10-29T08:24:12.759Z"
agent: "doc-keeper"
agent_id: "a0cca456316f2f5af"
turn: 1
reply_to: null
chars: 842
tokens_est: 396
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) 구현이 끝났다. 서비스 문서와 CHANGELOG를 갱신하고 기능 커밋 하나를 만들어 줘.

참고:
- 설계서 `docs/features/F2.md`, 계획 `docs/plans/F2-plan.md`, 결정 기록 `docs/plans/F2-decisions.md`, 실행 보고서 `docs/plans/F2-report.md`(알려진 제약은 3절)
- 실제 코드 `src/shortlink/` (특히 `api.py`, `web.py`, `validation.py`, `db.py`)

할 일:
1. `docs/service.md`: 별칭(`POST /links`의 `alias`, 규칙, 422/409와 문구), 통계 API `GET /links/{code}/stats`(응답 예시 포함), 통계 화면 `GET /stats/{code}`, 홈 폼의 별칭 입력칸, 결과 화면의 "통계 보기", F1 DB 자동 이전을 추가한다.
2. `CHANGELOG.md`: 맨 위에 `## F2 — 클릭 통계와 커스텀 별칭 (2026-10-29)` 항목을 F1 항목과 같은 형식(추가 / 동작 메모 / 알려진 제약)으로 넣는다. 알려진 제약은 보고서 3절의 minor 지적을 짧게 요약한다.
3. `git add -A --sparse`로 남은 변경(보고서, 결정 기록 포함)을 모두 담아 커밋한다. 첫 줄은 `F2: 클릭 통계와 커스텀 별칭 추가`, 본문에 변경 요점과 체크포인트 커밋 2개(`8bad8e8`, `b42b3bb`)를 적고, 마지막 줄에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`를 넣는다. push는 하지 않는다.
