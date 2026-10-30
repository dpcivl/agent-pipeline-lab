---
seq: 10
sender: "main"
receiver: "qa"
type: "T-TASK"
timestamp: "2026-10-30T00:45:29.979Z"
agent: "qa"
agent_id: "a9261a1aaf1377a99"
turn: 1
reply_to: null
chars: 753
tokens_est: 387
wait_s: null
---

F2(클릭 통계와 커스텀 별칭) QA 1라운드다. 리뷰 체크포인트: 16fdb28.

기준: docs/features/F2.md의 수용 기준 AC-1~AC-23과 "호환성" 항목, docs/plans/F2-plan.md(해석 결정 D2-1~D2-9, 사람 승인됨), 화면 목업 docs/plans/mockups/F2-*.html.

서버를 실제로 띄워(`uv run uvicorn shortlink.main:create_app --factory`, 다른 포트와 임시 DB 경로를 SHORTLINK_DB_PATH로 지정. DB 파일은 저장소 안 gitignore된 위치(예: *.db)나 실행 후 지울 위치에 두고 저장소 밖 경로는 쓰지 마) HTTP 요청으로 블랙박스 검증해 줘:
- 별칭 API/폼 AC-1~AC-11, 통계 AC-12~AC-22, F1 주요 흐름 회귀(AC-23 표본).
- 호환성: F1 스키마(code, url, created_at 3열)로 만든 DB 파일에 행을 넣고 서버를 띄웠을 때 기존 링크 리다이렉트와 clicks 0부터 세기 (이 항목은 평가 테스트가 아니라 QA 확인 대상이다).
- 서버 재시작 후 클릭 수 유지.
- 화면 HTML이 목업 문구·구조와 맞는지.
끝나면 서버를 반드시 종료하고 임시 DB를 지워 줘.

AC마다 PASS/FAIL, 그리고 발견한 문제는 심각도(blocker/major/minor), 재현 절차, 기대/실제를 적고 ID(Q-1, Q-2...)를 붙여 줘. 파일은 수정하지 않는다.
